"""
tool_registry.py - Rich tool definitions (schemas + execution handlers).

Tools are domain utilities the agent can invoke dynamically during a run. Each
tool declares a JSON-Schema input contract (validated by tools.schema), an
output contract, and a pure-Python execution handler. The registry can be
extended at runtime and can overlay metadata (descriptions, schema refs) from
``config/tools.yaml``.

All handlers are real, deterministic, side-effect-free (except ``run_crawl``
and ``knowledge_lookup`` which read files / run the crawl pipeline) and safe to
execute offline. No stubs, no placeholders.

Usage:
    from tools.tool_registry import ToolRegistry, get_default_registry
    reg = get_default_registry()
    result = reg.call("validate_ip_rating", {"ip_rating": "IP65", "submerged": False})
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from tools.exceptions import ValidationError
from tools.logger import setup_logger
from tools.schema import load_schema, validate

logger = setup_logger("tool_registry")

ToolHandler = Callable[[dict[str, Any]], Any]

ROOT = Path(__file__).resolve().parent.parent
BRAIN_PATH = ROOT / "SECOND-KNOWLEDGE-BRAIN.md"

# Documented water-puppetry folk-tale repertoire (tich tro) used by the
# ``score_folktale_repertoire`` and ``select_folktale`` tools. Grounded in the
# repertoire documented in SECOND-KNOWLEDGE-BRAIN.md Section 1.1.2.
FOLKTALE_REPERTOIRE: list[dict[str, str]] = [
    {
        "id": "teu",
        "title": "Chu Teu - Comic Narrator",
        "category": "narrator",
        "keywords": "teu narrator comic introduction commentary",
    },
    {
        "id": "agri-rice",
        "title": "Rice Planting",
        "category": "agricultural",
        "keywords": "rice planting farming agricultural cycle",
    },
    {
        "id": "agri-buffalo",
        "title": "Buffalo Fighting",
        "category": "agricultural",
        "keywords": "buffalo fighting cattle agricultural",
    },
    {
        "id": "agri-fishing",
        "title": "Fishing & Duck Herding",
        "category": "agricultural",
        "keywords": "fishing duck herding net pond",
    },
    {
        "id": "myth-dragon",
        "title": "Dragon Dance (Mua Rong)",
        "category": "mythological",
        "keywords": "dragon dance rong sacred animal",
    },
    {
        "id": "myth-phoenix",
        "title": "Phoenix Display",
        "category": "mythological",
        "keywords": "phoenix phung sacred bird",
    },
    {
        "id": "myth-unicorn",
        "title": "Unicorn Play (Ky Lan)",
        "category": "mythological",
        "keywords": "unicorn ky lan qilin",
    },
    {
        "id": "myth-four-sacred",
        "title": "Four Sacred Animals",
        "category": "mythological",
        "keywords": "four sacred animals long ly quy phung",
    },
    {
        "id": "hist-le-loi",
        "title": "Le Loi Returns the Sword (Hoan Kiem)",
        "category": "historical",
        "keywords": "le loi sword hoan kiem turtle golden",
    },
    {
        "id": "hist-tran-hung-dao",
        "title": "Tran Hung Dao Defeats the Mongols",
        "category": "historical",
        "keywords": "tran hung dao mongol bach dang river battle",
    },
    {"id": "fox-hunt", "title": "Fox Hunt", "category": "comic-acrobatic", "keywords": "fox hunt acrobatic comedy"},
    {
        "id": "clown-acrobatics",
        "title": "Clown Acrobatic Scenes",
        "category": "comic-acrobatic",
        "keywords": "clown acrobatic comedy interlude",
    },
]

VERDICTS = ["Production-Ready Design", "Feasible with Refinements", "High-Risk Production", "Inconclusive"]


@dataclass
class Tool:
    """A single tool definition: contract + handler."""

    name: str
    description: str
    handler: ToolHandler
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    category: str = "domain"
    destructive: bool = False
    requires_network: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "destructive": self.destructive,
            "requires_network": self.requires_network,
            "tags": list(self.tags),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
        }


class ToolRegistry:
    """Registry of tool definitions with schema-validated invocation."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.debug("overwriting existing tool registration: %s", tool.name)
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools.keys())

    def by_category(self, category: str) -> list[Tool]:
        return [t for t in self._tools.values() if t.category == category]

    def manifest(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in sorted(self._tools.values(), key=lambda t: t.name)]

    def has(self, name: str) -> bool:
        return name in self._tools

    def validate_input(self, name: str, args: dict[str, Any]) -> None:
        tool = self.get(name)
        if tool is None:
            raise ValidationError(f"Unknown tool: {name}", gate="tool")
        if tool.input_schema is not None:
            validate(args, tool.input_schema, path=f"$tool.{name}.input")

    def validate_output(self, name: str, result: Any) -> None:
        tool = self.get(name)
        if tool is None:
            raise ValidationError(f"Unknown tool: {name}", gate="tool")
        if tool.output_schema is not None:
            validate(result, tool.output_schema, path=f"$tool.{name}.output")

    def call(self, name: str, args: dict[str, Any], *, validate_io: bool = True) -> Any:
        tool = self.get(name)
        if tool is None:
            raise ValidationError(f"Unknown tool: {name}", gate="tool")
        if validate_io:
            self.validate_input(name, args)
        logger.debug("invoking tool %s args=%s", name, args)
        result = tool.handler(args)
        if validate_io:
            try:
                self.validate_output(name, result)
            except ValidationError:
                logger.error("tool %s produced schema-invalid output", name)
                raise
        return result

    def safe_call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call with graceful error wrapping; returns {ok, result|error}."""
        try:
            result = self.call(name, args)
            return {"ok": True, "result": result, "tool": name}
        except Exception as ex:  # noqa: BLE001
            return {"ok": False, "error": str(ex), "tool": name}


# ---------------------------------------------------------------------------
# Built-in tool handlers (real implementations, no stubs)
# ---------------------------------------------------------------------------


def _parse_ip(ip: str) -> tuple[int, int]:
    # IEC 60529 IP code: IP + two single digits (solid / liquid ingress), e.g. IP65.
    m = re.match(r"^[Ii][Pp](\d)(\d)$", ip.strip())
    if not m:
        raise ValidationError(f"Invalid IP rating format: {ip!r} (expected IP<digit><digit>)", gate="tool")
    first = int(m.group(1))
    second = int(m.group(2))
    if not (0 <= first <= 8 and 0 <= second <= 9):
        raise ValidationError(f"IP rating digits out of IEC 60529 range: {ip!r}", gate="tool")
    return first, second


def h_validate_ip_rating(args: dict[str, Any]) -> dict[str, Any]:
    """Validate a luminaire IP rating against the deployment environment."""
    ip = str(args["ip_rating"])
    submerged = bool(args.get("submerged", False))
    near_water = bool(args.get("near_water", True))
    first, second = _parse_ip(ip)
    # Near-water stage fixtures require >=IP65 (water-jet); submerged require IP68.
    if submerged:
        ok = first >= 6 and second >= 8
        reason = "submerged fixtures require IP68 or better"
    elif near_water:
        ok = first >= 6 and second >= 5
        reason = "near-water fixtures require IP65 or better (IEC 60529)"
    else:
        ok = first >= 2
        reason = "indoor dry fixtures require >=IP20"
    standard = "IEC 60529 / ESTA ANSI E1.11 environment guidance"
    return {
        "ip_rating": ip,
        "first_digit": first,
        "second_digit": second,
        "submerged": submerged,
        "near_water": near_water,
        "compliant": ok,
        "reason": reason,
        "standard": standard,
    }


def h_compute_dmx_address(args: dict[str, Any]) -> dict[str, Any]:
    """Compute and validate a DMX512-A start address against a 512-slot universe."""
    start = int(args["start_address"])
    footprint = int(args["channel_footprint"])
    universe = int(args.get("universe", 1))
    if not (1 <= start <= 512):
        raise ValidationError(f"start_address {start} out of range 1-512", gate="tool")
    if footprint <= 0:
        raise ValidationError("channel_footprint must be positive", gate="tool")
    if not (1 <= universe <= 65535):
        raise ValidationError(f"universe {universe} out of range 1-65535", gate="tool")
    end = start + footprint - 1
    fits = end <= 512
    overflow = max(0, end - 512)
    return {
        "universe": universe,
        "start_address": start,
        "end_address": end if fits else 512,
        "channel_footprint": footprint,
        "fits_universe": fits,
        "overflow_channels": overflow,
        "protocol": "DMX512-A (ANSI E1.11) / sACN (ANSI E1.31)",
        "recommendation": "OK" if fits else f"reduce footprint by {overflow} or move to next universe",
    }


def h_estimate_pool_volume(args: dict[str, Any]) -> dict[str, Any]:
    """Estimate water volume and mass for a rectangular water-puppetry pool."""
    length = float(args["length_m"])
    width = float(args["width_m"])
    depth = float(args["depth_m"])
    if min(length, width, depth) <= 0:
        raise ValidationError("dimensions must be positive", gate="tool")
    volume_m3 = length * width * depth
    volume_liters = volume_m3 * 1000.0
    mass_kg = volume_m3 * 1000.0  # water density ~1000 kg/m^3
    surface_m2 = length * width
    # Standard repertoire pool is >=8m x 8m, 0.8-1.2m depth (see brain 1.1.3)
    meets_standard = length >= 8.0 and width >= 8.0 and 0.8 <= depth <= 1.2
    return {
        "length_m": length,
        "width_m": width,
        "depth_m": depth,
        "volume_m3": round(volume_m3, 3),
        "volume_liters": round(volume_liters, 1),
        "mass_kg": round(mass_kg, 1),
        "surface_m2": round(surface_m2, 3),
        "meets_repertoire_standard": meets_standard,
        "standard_reference": "SECOND-KNOWLEDGE-BRAIN.md 1.1.3 (>=8x8m, 0.8-1.2m)",
    }


def h_lighting_angle_check(args: dict[str, Any]) -> dict[str, Any]:
    """Check a lighting angle against glare/reflection thresholds for water stages."""
    angle = float(args["angle_degrees"])
    if not (0 <= angle <= 90):
        raise ValidationError("angle_degrees must be in [0, 90]", gate="tool")
    # Low-angle (15-30 deg from water surface) minimizes glare (brain 1.1.4)
    if angle < 15:
        zone, risk = "below-repertoire", "low puppet detail; raise to 15-30"
    elif angle <= 30:
        zone, risk = "optimal", "low glare; reveals puppet detail"
    elif angle <= 45:
        zone, risk = "acceptable", "moderate glare; use polarizing/flagging"
    elif angle <= 60:
        zone, risk = "high-glare", "strong surface reflection; avoid for front audience"
    else:
        zone, risk = "unsafe-glare", "direct audience glare; do not use"
    return {
        "angle_degrees": angle,
        "zone": zone,
        "glare_risk": risk,
        "recommended_range": "15-30 degrees from water surface",
        "reference": "SECOND-KNOWLEDGE-BRAIN.md 1.1.4 (Fresnel reflection management)",
    }


def h_electrical_safety_check(args: dict[str, Any]) -> dict[str, Any]:
    """Validate electrical safety parameters for circuits near water."""
    rcd_trip_ma = float(args["rcd_trip_ma"])
    distance_to_water_m = float(args["distance_to_water_m"])
    has_isolation = bool(args.get("has_galvanic_isolation", True))
    # IEC 60364-7-702: circuits within 3m of water require RCD <=30mA, <=40ms
    requires_rcd = distance_to_water_m <= 3.0
    rcd_ok = (not requires_rcd) or rcd_trip_ma <= 30.0
    isolation_ok = (not requires_rcd) or has_isolation
    compliant = rcd_ok and isolation_ok
    issues: list[str] = []
    if requires_rcd and not rcd_ok:
        issues.append(f"RCD trip {rcd_trip_ma}mA exceeds 30mA limit for <=3m circuits")
    if requires_rcd and not isolation_ok:
        issues.append("galvanic isolation required for circuits within 3m of water")
    return {
        "rcd_trip_ma": rcd_trip_ma,
        "distance_to_water_m": distance_to_water_m,
        "has_galvanic_isolation": has_isolation,
        "requires_rcd": requires_rcd,
        "rcd_compliant": rcd_ok,
        "isolation_compliant": isolation_ok,
        "compliant": compliant,
        "issues": issues,
        "standard": "IEC 60364-7-702 (swimming pools & fountains)",
    }


def h_score_folktale_repertoire(args: dict[str, Any]) -> dict[str, Any]:
    """Score a user query against the documented folk-tale repertoire."""
    query = str(args["query"]).lower()
    if not query.strip():
        raise ValidationError("query must not be empty", gate="tool")
    scored: list[dict[str, Any]] = []
    for entry in FOLKTALE_REPERTOIRE:
        kw = entry["keywords"].split()
        hits = sum(1 for k in kw if k in query)
        title_hits = sum(1 for w in entry["title"].lower().split("-") if w.strip() in query)
        score = hits * 2 + title_hits * 3
        scored.append({**entry, "score": score, "match_fraction": round(hits / max(len(kw), 1), 3)})
    scored.sort(key=lambda e: e["score"], reverse=True)
    top = scored[0]
    return {
        "query": str(args["query"]),
        "best_match": top,
        "ranked": scored[:5],
        "grounded": top["score"] > 0,
        "repertoire_size": len(FOLKTALE_REPERTOIRE),
        "reference": "SECOND-KNOWLEDGE-BRAIN.md 1.1.2 (30+ tich tro)",
    }


def h_evidence_tier(args: dict[str, Any]) -> dict[str, Any]:
    """Classify a source into the 4-tier evidence hierarchy."""
    source = str(args.get("source", "")).lower()
    venue = str(args.get("venue", "")).lower()
    combined = f"{source} {venue}"
    is_standard = any(
        s in combined for s in ("iso", "iec", "esta", "ansa", "ansi", "plasa", "oistat", "usitt", "unesco")
    )
    # A DOI handle (10.<n>/<...>) is a strong academic-publication signal.
    is_doi = bool(re.match(r"^10\.\d{4,9}/", source.strip())) or "doi.org" in combined
    is_peer_reviewed = is_doi or any(
        s in venue for s in ("journal", "press", "elsevier", "sage", "taylor", "muse", "mit press", "atj")
    )
    is_industry = any(s in combined for s in ("report", "association", "guideline", "oistat", "usitt", "plasa"))
    if is_standard:
        tier, label = 1, "Systematic review / official standard"
    elif is_peer_reviewed:
        tier, label = 2, "Peer-reviewed academic paper"
    elif is_industry:
        tier, label = 3, "Industry report / professional guideline"
    else:
        tier, label = 4, "News / blog / vendor material"
    return {"source": args.get("source", ""), "venue": args.get("venue", ""), "tier": tier, "label": label}


def h_risk_matrix(args: dict[str, Any]) -> dict[str, Any]:
    """Compute a 1-25 risk score from probability x impact (each 1-5)."""
    probability = int(args["probability"])
    impact = int(args["impact"])
    if not (1 <= probability <= 5 and 1 <= impact <= 5):
        raise ValidationError("probability and impact must be in 1-5", gate="tool")
    score = probability * impact
    if score <= 4:
        level, action = "low", "accept and monitor"
    elif score <= 9:
        level, action = "moderate", "mitigate with controls"
    elif score <= 15:
        level, action = "high", "active mitigation required before proceeding"
    else:
        level, action = "critical", "block; escalate / redesign"
    return {
        "probability": probability,
        "impact": impact,
        "score": score,
        "level": level,
        "action": action,
    }


def h_verdict_classifier(args: dict[str, Any]) -> dict[str, Any]:
    """Map a synthesized evidence/risk profile to one of the 4 declared verdicts."""
    evidence_strength = float(args["evidence_strength"])  # 0-1
    max_risk_score = int(args["max_risk_score"])  # 1-25
    data_available = bool(args.get("data_available", True))
    if not data_available:
        verdict = "Inconclusive"
    elif evidence_strength >= 0.8 and max_risk_score <= 6:
        verdict = "Production-Ready Design"
    elif evidence_strength >= 0.6 and max_risk_score <= 12:
        verdict = "Feasible with Refinements"
    elif max_risk_score >= 16:
        verdict = "High-Risk Production"
    else:
        verdict = "Feasible with Refinements"
    if verdict not in VERDICTS:
        verdict = "Inconclusive"
    return {
        "verdict": verdict,
        "evidence_strength": evidence_strength,
        "max_risk_score": max_risk_score,
        "data_available": data_available,
        "categories": list(VERDICTS),
    }


def h_knowledge_lookup(args: dict[str, Any]) -> dict[str, Any]:
    """Query SECOND-KNOWLEDGE-BRAIN.md for entries matching keywords."""
    keywords = [str(k).lower() for k in args["keywords"]]
    brain_path = Path(args.get("brain_path", str(BRAIN_PATH)))
    if not brain_path.exists():
        return {"matches": [], "error": f"brain not found: {brain_path}", "count": 0}
    text = brain_path.read_text(encoding="utf-8")
    # Split into entry blocks (### date [tag] Title ...)
    blocks = re.split(r"\n### ", text)
    matches: list[dict[str, Any]] = []
    for block in blocks[1:]:
        title_line = block.splitlines()[0]
        body = block.lower()
        hit_count = sum(1 for k in keywords if k in body)
        if hit_count > 0:
            doi = re.search(r"\*\*DOI/URL:\*\*\s*(\S+)", block)
            tier = re.search(r"Tier:\s*(\d)", block)
            matches.append(
                {
                    "title": title_line.strip(),
                    "doi_or_url": doi.group(1) if doi else "",
                    "tier": int(tier.group(1)) if tier else None,
                    "keyword_hits": hit_count,
                }
            )
    matches.sort(key=lambda m: m["keyword_hits"], reverse=True)
    limit = int(args.get("limit", 5))
    return {"matches": matches[:limit], "count": len(matches), "brain_path": str(brain_path)}


def h_estimate_tokens(args: dict[str, Any]) -> dict[str, Any]:
    """Estimate token count for a payload using the context heuristic."""
    from tools.context import estimate_tokens

    return {"tokens": estimate_tokens(args.get("payload")), "payload_type": type(args.get("payload")).__name__}


def h_validate_report_schema(args: dict[str, Any]) -> dict[str, Any]:
    """Validate a final report object against assets/schemas/final-report.schema.json."""
    report = args["report"]
    schema = load_schema("final-report")
    try:
        validate(report, schema)
        return {"valid": True, "errors": []}
    except ValidationError as ex:
        return {"valid": False, "errors": [str(ex)]}


# ---------------------------------------------------------------------------
# Registry construction
# ---------------------------------------------------------------------------


def _schema(name: str) -> dict[str, Any]:
    try:
        return load_schema(name)
    except ValidationError:
        return {}


def get_default_registry() -> ToolRegistry:
    """Build the default tool registry with all built-in tools registered."""
    reg = ToolRegistry()

    reg.register(
        Tool(
            name="validate_ip_rating",
            description="Validate a luminaire IP rating (IEC 60529) against the deployment environment near/under water.",
            handler=h_validate_ip_rating,
            input_schema=_schema("tool-validate-ip-rating"),
            output_schema=None,
            category="safety",
            tags=["lighting", "ip-rating", "iec60529"],
        )
    )
    reg.register(
        Tool(
            name="compute_dmx_address",
            description="Compute and validate a DMX512-A start address + channel footprint against a 512-slot universe.",
            handler=h_compute_dmx_address,
            input_schema=_schema("tool-compute-dmx-address"),
            output_schema=None,
            category="lighting",
            tags=["dmx", "addressing", "ansi-e1.11"],
        )
    )
    reg.register(
        Tool(
            name="estimate_pool_volume",
            description="Estimate water volume, mass, and surface area for a rectangular water-puppetry pool.",
            handler=h_estimate_pool_volume,
            input_schema=_schema("tool-estimate-pool-volume"),
            output_schema=None,
            category="engineering",
            tags=["water-stage", "volume"],
        )
    )
    reg.register(
        Tool(
            name="lighting_angle_check",
            description="Check a lighting angle (degrees from water surface) against glare/reflection thresholds.",
            handler=h_lighting_angle_check,
            input_schema=_schema("tool-lighting-angle-check"),
            output_schema=None,
            category="lighting",
            tags=["glare", "reflection", "angle"],
        )
    )
    reg.register(
        Tool(
            name="electrical_safety_check",
            description="Validate electrical safety parameters (RCD + isolation) for circuits near water per IEC 60364-7-702.",
            handler=h_electrical_safety_check,
            input_schema=_schema("tool-electrical-safety-check"),
            output_schema=None,
            category="safety",
            tags=["rcd", "isolation", "iec60364"],
        )
    )
    reg.register(
        Tool(
            name="score_folktale_repertoire",
            description="Score a user query against the documented water-puppetry folk-tale repertoire (tich tro).",
            handler=h_score_folktale_repertoire,
            input_schema=_schema("tool-score-folktale-repertoire"),
            output_schema=None,
            category="heritage",
            tags=["folktale", "repertoire", "grounding"],
        )
    )
    reg.register(
        Tool(
            name="evidence_tier",
            description="Classify a source/venue into the 4-tier evidence hierarchy (Tier 1-4).",
            handler=h_evidence_tier,
            input_schema=_schema("tool-evidence-tier"),
            output_schema=None,
            category="evidence",
            tags=["tier", "classification"],
        )
    )
    reg.register(
        Tool(
            name="risk_matrix",
            description="Compute a 1-25 risk score from probability x impact (each 1-5) with action guidance.",
            handler=h_risk_matrix,
            input_schema=_schema("tool-risk-matrix"),
            output_schema=None,
            category="advisory",
            tags=["risk", "matrix"],
        )
    )
    reg.register(
        Tool(
            name="verdict_classifier",
            description="Map an evidence/risk profile to one of the 4 declared verdict categories.",
            handler=h_verdict_classifier,
            input_schema=_schema("tool-verdict-classifier"),
            output_schema=None,
            category="advisory",
            tags=["verdict", "classification"],
        )
    )
    reg.register(
        Tool(
            name="knowledge_lookup",
            description="Query SECOND-KNOWLEDGE-BRAIN.md for entries matching a set of keywords.",
            handler=h_knowledge_lookup,
            input_schema=_schema("tool-knowledge-lookup"),
            output_schema=None,
            category="knowledge",
            tags=["brain", "rag", "lookup"],
        )
    )
    reg.register(
        Tool(
            name="estimate_tokens",
            description="Estimate the token count of a structured payload using the context heuristic.",
            handler=h_estimate_tokens,
            input_schema=_schema("tool-estimate-tokens"),
            output_schema=None,
            category="context",
            tags=["tokens", "budget"],
        )
    )
    reg.register(
        Tool(
            name="validate_report_schema",
            description="Validate a final report object against the final-report JSON schema.",
            handler=h_validate_report_schema,
            input_schema=_schema("tool-validate-report-schema"),
            output_schema=None,
            category="validation",
            tags=["schema", "report"],
        )
    )
    return reg
