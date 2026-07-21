"""
skill_registry.py - Modular skill registry for the agent harness.

A skill is a named, declarative unit of work the main agent can invoke. Each
skill declares its inputs, outputs, the sub-skills it may chain to, the tools
it uses, and a validation contract. The registry resolves skills by name (and
optionally by capability tag), executes them via a pluggable executor, and
validates outputs against JSON schemas in assets/schemas/.

The registry overlays metadata from ``config/skill_registry.yaml`` onto the
built-in Python skill definitions (which carry the real execution logic).

This module is the single source of truth for "which skills exist, what they
accept/return, and how they are invoked" - the runtime counterpart of SKILL.md.

Usage:
    from tools.skill_registry import SkillRegistry, get_default_registry
    reg = get_default_registry()
    skill = reg.resolve("sub-core-analysis")
    result = reg.execute("sub-core-analysis", {"theme": "Le Loi", ...})
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import copy
from pathlib import Path
from typing import Any

from tools.exceptions import ValidationError
from tools.logger import setup_logger
from tools.schema import is_valid, load_schema, validate

logger = setup_logger("skill_registry")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "skill_registry.yaml"


@dataclass
class Skill:
    """A declarative skill definition with an executable handler."""

    name: str
    description: str
    handler: Callable[[dict[str, Any], Any], Any]
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    sub_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    step: int = 0
    category: str = "domain"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "step": self.step,
            "category": self.category,
            "sub_skills": list(self.sub_skills),
            "tools": list(self.tools),
            "gates": list(self.gates),
            "capabilities": list(self.capabilities),
            "has_input_schema": self.input_schema is not None,
            "has_output_schema": self.output_schema is not None,
        }


class SkillRegistry:
    """Registry of skills: resolve, execute, validate."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            logger.debug("overwriting existing skill registration: %s", skill.name)
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> bool:
        return self._skills.pop(name, None) is not None

    def resolve(self, name: str) -> Skill:
        skill = self._skills.get(name)
        if skill is None:
            raise ValidationError(f"Unknown skill: {name}", gate="skill")
        return skill

    def has(self, name: str) -> bool:
        return name in self._skills

    def names(self) -> list[str]:
        return sorted(self._skills.keys())

    def by_capability(self, capability: str) -> list[Skill]:
        return [s for s in self._skills.values() if capability in s.capabilities]

    def by_category(self, category: str) -> list[Skill]:
        return [s for s in self._skills.values() if s.category == category]

    def manifest(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in sorted(self._skills.values(), key=lambda s: (s.step, s.name))]

    def validate_input(self, name: str, args: dict[str, Any]) -> None:
        skill = self.resolve(name)
        if skill.input_schema is not None:
            validate(args, skill.input_schema, path=f"$skill.{name}.input")

    def validate_output(self, name: str, result: Any) -> None:
        skill = self.resolve(name)
        if skill.output_schema is not None:
            if not is_valid(result, skill.output_schema):
                try:
                    validate(result, skill.output_schema, path=f"$skill.{name}.output")
                except ValidationError:
                    logger.error("skill %s produced schema-invalid output", name)
                    raise

    def execute(self, name: str, args: dict[str, Any], context: Any = None, *, validate_io: bool = True) -> Any:
        skill = self.resolve(name)
        if validate_io:
            self.validate_input(name, args)
        logger.debug("executing skill %s args=%s", name, args)
        result = skill.handler(args, context)
        if validate_io:
            self.validate_output(name, result)
        return result

    def safe_execute(self, name: str, args: dict[str, Any], context: Any = None) -> dict[str, Any]:
        try:
            result = self.execute(name, args, context)
            return {"ok": True, "result": result, "skill": name}
        except Exception as ex:  # noqa: BLE001
            return {"ok": False, "error": str(ex), "skill": name}

    def graph(self) -> dict[str, Any]:
        """Return the skill dependency graph (who chains to whom)."""
        nodes = []
        edges: list[dict[str, str]] = []
        for s in self._skills.values():
            nodes.append(s.to_dict())
            for child in s.sub_skills:
                edges.append({"from": s.name, "to": child})
        return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Built-in skill handlers. These wrap the domain logic that, in a live Claude
# Code session, is expressed as markdown prompts in skills/*.md. Here each
# handler is a deterministic, real implementation that applies the documented
# domain method and uses the tool_registry to ground outputs in standards.
# ---------------------------------------------------------------------------


def _require(ctx: Any, key: str, default: Any = None) -> Any:
    if ctx is None:
        return default
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return getattr(ctx, key, default)


def h_gather_requirements(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """sub-gather-requirements: clarify object, scope, timeframe, audience, language."""
    obj = args.get("object") or args.get("theme") or ""
    if not obj:
        raise ValidationError("object of analysis is required", gate="G-REQ")
    return {
        "object": obj,
        "scope": args.get("scope", "full production design"),
        "timeframe": args.get("timeframe", "current season"),
        "available_inputs": args.get("available_inputs", []),
        "target_audience": args.get("target_audience", "general"),
        "language": args.get("language", "English"),
        "analysis_type": args.get("analysis_type", "combined"),
        "assumptions": args.get("assumptions", ["default analysis_type=combined"]),
    }


def h_evidence_collector(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """sub-evidence-collector: assemble an evidence bundle with tiers."""
    from tools.tool_registry import get_default_registry

    tool_reg = get_default_registry()
    sources = args.get("sources", [])
    current_data = []
    authoritative_docs = []
    recent_news = []
    for s in sources:
        tier = tool_reg.call("evidence_tier", {"source": s.get("url", ""), "venue": s.get("venue", "")})
        entry = {
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "date": s.get("date", ""),
            "tier": tier["tier"],
            "tier_label": tier["label"],
        }
        if tier["tier"] <= 1:
            authoritative_docs.append(entry)
        elif tier["tier"] == 4:
            recent_news.append(entry)
        else:
            current_data.append(entry)
    degraded = not (current_data or authoritative_docs)
    return {
        "current_data": current_data,
        "authoritative_docs": authoritative_docs,
        "recent_news": recent_news,
        "reference_benchmarks": [],
        "degraded": degraded,
        "limitation_flag": "no live evidence retrieved" if degraded else None,
    }


def h_core_analysis(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """sub-core-analysis: design a water-puppetry scenario grounded in heritage + safety."""
    from tools.tool_registry import get_default_registry

    tool_reg = get_default_registry()
    theme = args.get("theme") or args.get("object") or ""
    venue = args.get("venue", {})
    equipment = args.get("equipment", {})

    folktale = tool_reg.call("score_folktale_repertoire", {"query": theme})
    pool_dims = {
        "length_m": float(venue.get("pool_length_m", 8.0)),
        "width_m": float(venue.get("pool_width_m", 8.0)),
        "depth_m": float(venue.get("pool_depth_m", 1.0)),
    }
    pool = tool_reg.call("estimate_pool_volume", pool_dims)
    fixtures = equipment.get("fixtures", [])
    fixture_checks = []
    for fx in fixtures:
        ip = fx.get("ip_rating", "IP20")
        fixture_checks.append(
            tool_reg.call(
                "validate_ip_rating",
                {"ip_rating": ip, "submerged": fx.get("submerged", False), "near_water": fx.get("near_water", True)},
            )
        )
    lighting = args.get("lighting", {})
    angle_check = tool_reg.call("lighting_angle_check", {"angle_degrees": float(lighting.get("angle_degrees", 20))})
    safety = tool_reg.call(
        "electrical_safety_check",
        {
            "rcd_trip_ma": float(safety_args(args).get("rcd_trip_ma", 30)),
            "distance_to_water_m": float(safety_args(args).get("distance_to_water_m", 1.0)),
            "has_galvanic_isolation": safety_args(args).get("has_galvanic_isolation", True),
        },
    )

    return {
        "theme": theme,
        "folktale": folktale["best_match"],
        "folktale_grounded": folktale["grounded"],
        "pool": pool,
        "lighting": {"angle_check": angle_check, "color_temp_k": lighting.get("color_temp_k", 3200)},
        "fixture_checks": fixture_checks,
        "safety": safety,
        "effects": args.get("effects", ["low-lying fog", "water-surface projection"]),
        "scenarios": {
            "best": "full automated rig + LED matrix + projection mapping",
            "base": "manual poles + IP65 LED floods + fog",
            "worst": "heritage-only manual poles, ambient light only",
        },
    }


def safety_args(args: dict[str, Any]) -> dict[str, Any]:
    return args.get("safety", {})


def h_knowledge_updater(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """sub-knowledge-updater: query the brain and surface tiered citations."""
    from tools.tool_registry import get_default_registry

    tool_reg = get_default_registry()
    keywords = args.get("keywords", [])
    lookup = tool_reg.call("knowledge_lookup", {"keywords": keywords, "limit": 5})
    gaps = []
    coverage = "Strong" if lookup["count"] >= 3 else "Moderate" if lookup["count"] >= 1 else "Weak"
    if lookup["count"] < 3:
        gaps.append(f"insufficient coverage for {keywords}")
    return {
        "citations": lookup["matches"],
        "gaps": gaps,
        "coverage": coverage,
        "count": lookup["count"],
    }


def h_advisor(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """sub-advisor: synthesize into a risk-disclosed conclusion."""
    from tools.tool_registry import get_default_registry

    tool_reg = get_default_registry()
    risks_in = args.get("risks", [])
    risk_scores = []
    for r in risks_in:
        rm = tool_reg.call(
            "risk_matrix", {"probability": int(r.get("probability", 3)), "impact": int(r.get("impact", 3))}
        )
        rm["description"] = r.get("description", "")
        risk_scores.append(rm)
    max_risk = max((r["score"] for r in risk_scores), default=1)
    evidence_strength = float(args.get("evidence_strength", 0.5))
    data_available = bool(args.get("data_available", True))
    verdict = tool_reg.call(
        "verdict_classifier",
        {
            "evidence_strength": evidence_strength,
            "max_risk_score": max_risk,
            "data_available": data_available,
        },
    )
    return {
        "verdict": verdict["verdict"],
        "scenarios": args.get("scenarios", {"best": "", "base": "", "worst": ""}),
        "key_risks": risk_scores,
        "evidence_chain": args.get("evidence_chain", []),
        "remediation": args.get("remediation", []),
        "disclosure": "Automated synthesis; cross-check against current authoritative sources before acting.",
    }


def h_main_harness(args: dict[str, Any], ctx: Any = None) -> dict[str, Any]:
    """main harness skill: orchestrate the 5 sub-skills in declared order."""
    reg = get_default_registry()
    state: dict[str, Any] = {}
    reqs = reg.execute("sub-gather-requirements", args, ctx)
    state["requirements"] = reqs
    evidence = reg.execute("sub-evidence-collector", {"sources": args.get("sources", [])}, state)
    state["evidence"] = evidence
    core = reg.execute(
        "sub-core-analysis",
        {
            "theme": reqs["object"],
            "venue": args.get("venue", {}),
            "equipment": args.get("equipment", {}),
            "lighting": args.get("lighting", {}),
            "safety": args.get("safety", {}),
            "effects": args.get("effects", []),
        },
        state,
    )
    state["core_analysis"] = core
    knowledge = reg.execute("sub-knowledge-updater", {"keywords": args.get("keywords", [reqs["object"]])}, state)
    state["knowledge"] = knowledge
    advisor = reg.execute(
        "sub-advisor",
        {
            "risks": args.get("risks", []),
            "evidence_strength": args.get("evidence_strength", 0.5),
            "data_available": not evidence["degraded"],
            "scenarios": core["scenarios"],
            "evidence_chain": args.get("evidence_chain", []),
            "remediation": args.get("remediation", []),
        },
        state,
    )
    state["advisor"] = advisor
    state["verdict"] = advisor["verdict"]
    state["degradation_level"] = 2 if evidence["degraded"] else 0
    return state


def _schema(name: str) -> dict[str, Any]:
    """Load an output/strict schema by name (empty dict if missing)."""
    try:
        return load_schema(name)
    except ValidationError:
        return {}


def _input_schema(output_name: str, required: list[str]) -> dict[str, Any]:
    """Build a lenient INPUT schema from an output schema, keeping only ``required``
    user-provided fields. Handlers fill the remaining defaults, so input
    validation must not over-constrain."""
    base = _schema(output_name)
    if not base:
        return {}
    schema = copy.deepcopy(base)
    schema["required"] = list(required)
    # input allows extra fields (e.g. the full harness args dict) without error
    schema["additionalProperties"] = True
    return schema


def get_default_registry() -> SkillRegistry:
    """Build the default skill registry with all built-in skills."""
    reg = SkillRegistry()
    reg.register(
        Skill(
            name="water-puppetry-staging-design",
            description="Main harness: orchestrates the 5 sub-skills into a risk-disclosed report.",
            handler=h_main_harness,
            input_schema=_schema("harness-input"),
            output_schema=_schema("harness-output"),
            sub_skills=[
                "sub-gather-requirements",
                "sub-evidence-collector",
                "sub-core-analysis",
                "sub-knowledge-updater",
                "sub-advisor",
            ],
            tools=[
                "validate_ip_rating",
                "compute_dmx_address",
                "estimate_pool_volume",
                "lighting_angle_check",
                "electrical_safety_check",
                "score_folktale_repertoire",
                "evidence_tier",
                "risk_matrix",
                "verdict_classifier",
                "knowledge_lookup",
            ],
            gates=["U1", "U2", "U3", "U4", "U5", "U6", "G1", "G2", "G3", "G4"],
            capabilities=["analyze", "design", "advise", "orchestrate"],
            step=0,
            category="harness",
        )
    )
    reg.register(
        Skill(
            name="sub-gather-requirements",
            description="Clarify object, scope, timeframe, inputs, audience, language before data fetching.",
            handler=h_gather_requirements,
            input_schema=_input_schema("requirements", ["object"]),
            output_schema=_schema("requirements"),
            gates=["G-REQ"],
            capabilities=["intake"],
            step=1,
            category="sub-agent",
        )
    )
    reg.register(
        Skill(
            name="sub-evidence-collector",
            description="Fetch authoritative real-time + reference data with tier labels.",
            handler=h_evidence_collector,
            input_schema=_input_schema("evidence-bundle", ["sources"]),
            output_schema=_schema("evidence-bundle"),
            tools=["evidence_tier"],
            gates=["U1", "U3"],
            capabilities=["research"],
            step=2,
            category="sub-agent",
        )
    )
    reg.register(
        Skill(
            name="sub-core-analysis",
            description="Design a water-puppetry scenario grounded in heritage, lighting, and safety.",
            handler=h_core_analysis,
            input_schema=_input_schema("core-analysis", []),
            output_schema=_schema("core-analysis"),
            tools=[
                "score_folktale_repertoire",
                "estimate_pool_volume",
                "validate_ip_rating",
                "lighting_angle_check",
                "electrical_safety_check",
            ],
            gates=["G1", "G2", "G3", "G4"],
            capabilities=["design", "engineer"],
            step=3,
            category="sub-agent",
        )
    )
    reg.register(
        Skill(
            name="sub-knowledge-updater",
            description="Query the knowledge brain for tiered citations and flag gaps.",
            handler=h_knowledge_updater,
            input_schema=_input_schema("knowledge-evidence", ["keywords"]),
            output_schema=_schema("knowledge-evidence"),
            tools=["knowledge_lookup"],
            gates=["U1"],
            capabilities=["research", "rag"],
            step=4,
            category="sub-agent",
        )
    )
    reg.register(
        Skill(
            name="sub-advisor",
            description="Synthesize prior analysis into a risk-disclosed conclusion.",
            handler=h_advisor,
            input_schema=_input_schema("advisor-conclusion", []),
            output_schema=_schema("advisor-conclusion"),
            tools=["risk_matrix", "verdict_classifier"],
            gates=["U2", "U6"],
            capabilities=["advise", "synthesize"],
            step=5,
            category="sub-agent",
        )
    )
    return reg
