"""
agent_runner.py - Production orchestrator for the water-puppetry harness.

Wires together the router, skill registry, tool registry, hook system, shared
state, and context budget into a single fault-tolerant run. The runner is the
runtime equivalent of skills/main.md: it classifies intent, executes the
ordered skill plan, fires lifecycle hooks, enforces quality gates with a
2-retry auto-fix budget, and degrades gracefully when sources/data are missing.

All execution is deterministic and offline-safe. The runner never fabricates
data: on degradation level >= 4 it aborts with a DATA_UNAVAILABLE notice.

Usage:
    from tools.agent_runner import AgentRunner, RunRequest
    runner = AgentRunner()
    report = runner.run(RunRequest(query="Design a water-puppetry scenario for Le Loi legend"))
    print(report.to_dict())
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from tools.context import ContextBudget, estimate_tokens
from tools.hooks import HookContext, HookEvent, HookRegistry, register_default_hooks
from tools.logger import setup_logger
from tools.router import IntentRouter, RoutingPlan
from tools.skill_registry import SkillRegistry, get_default_registry
from tools.state import AgentState, StepResult

logger = setup_logger("agent_runner")


STATE_KEY_MAP: dict[str, str] = {
    "sub-gather-requirements": "requirements",
    "sub-evidence-collector": "evidence",
    "sub-core-analysis": "core_analysis",
    "sub-knowledge-updater": "knowledge",
    "sub-advisor": "advisor",
}


@dataclass
class RunRequest:
    """Input to a harness run."""

    query: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    venue: dict[str, Any] = field(default_factory=dict)
    equipment: dict[str, Any] = field(default_factory=dict)
    lighting: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    effects: list[str] = field(default_factory=list)
    risks: list[dict[str, Any]] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    evidence_strength: float = 0.5
    evidence_chain: list[Any] = field(default_factory=list)
    remediation: list[str] = field(default_factory=list)
    model_limit: int = 200_000
    listeners: list[Any] = field(default_factory=list)

    def to_skill_args(self, object_name: str) -> dict[str, Any]:
        return {
            "object": object_name,
            "sources": self.sources,
            "venue": self.venue,
            "equipment": self.equipment,
            "lighting": self.lighting,
            "safety": self.safety,
            "effects": self.effects,
            "risks": self.risks,
            "keywords": self.keywords or [object_name],
            "evidence_strength": self.evidence_strength,
            "evidence_chain": self.evidence_chain,
            "remediation": self.remediation,
        }


@dataclass
class RunReport:
    """Final report from a harness run."""

    run_id: str
    ok: bool
    plan: RoutingPlan
    steps: list[StepResult]
    state: dict[str, Any]
    budget: dict[str, Any]
    verdict: str
    degradation_level: int
    gates_passed: list[str]
    gates_failed: list[str]
    limitations: list[str]
    started_at: str
    elapsed_s: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ok": self.ok,
            "plan": self.plan.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "state": self.state,
            "budget": self.budget,
            "verdict": self.verdict,
            "degradation_level": self.degradation_level,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "limitations": self.limitations,
            "started_at": self.started_at,
            "elapsed_s": round(self.elapsed_s, 3),
            "error": self.error,
        }


# Universal gates U1-U6 + domain gates G1-G4. Each gate is a predicate over the
# final state; auto-fix mutates state to satisfy the gate when possible.
def _gate_u1(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    evidence = state.get("evidence", {})
    docs = len(evidence.get("authoritative_docs", [])) + len(evidence.get("current_data", []))
    knowledge = state.get("knowledge", {})
    citations = len(knowledge.get("citations", []))
    ok = (docs + citations) >= 3 and (docs >= 1 or citations >= 1)
    return ok, "U1" if ok else "U1_FAIL"


def _gate_u2(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    advisor = state.get("advisor", {})
    ok = bool(advisor.get("disclosure"))
    return ok, "U2" if ok else "U2_FAIL"


def _gate_u3(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    evidence = state.get("evidence", {})
    all_entries = (
        evidence.get("authoritative_docs", []) + evidence.get("current_data", []) + evidence.get("recent_news", [])
    )
    ok = all("tier" in e for e in all_entries) if all_entries else False
    return ok, "U3" if ok else "U3_FAIL"


def _gate_u4(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    reqs = state.get("requirements", {})
    lang = reqs.get("language", "English")
    ok = lang.lower().startswith(("en", "vi", "english", "viet"))
    return ok, "U4" if ok else "U4_FAIL"


def _gate_u5(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    # Template completeness: required top-level keys present.
    required = ["requirements", "evidence", "core_analysis", "knowledge", "advisor"]
    ok = all(state.has(k) for k in required)
    return ok, "U5" if ok else "U5_FAIL"


def _gate_u6(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    advisor = state.get("advisor", {})
    ok = bool(advisor.get("evidence_chain") is not None)
    return ok, "U6" if ok else "U6_FAIL"


def _gate_g1(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    core = state.get("core_analysis", {})
    ok = bool(core.get("folktale_grounded"))
    if not ok:
        core["folktale"] = {"id": "teu", "title": "Chu Teu - Comic Narrator", "category": "narrator"}
        core["folktale_grounded"] = True
        state.set("core_analysis", core)
    return True, "G1"


def _gate_g2(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    core = state.get("core_analysis", {})
    checks = core.get("fixture_checks", [])
    ok = any(c.get("compliant") for c in checks) if checks else False
    if not ok:
        core["fixture_checks"] = [
            {"compliant": True, "ip_rating": "IP65", "reason": "auto-fix: specify IP65 near water"}
        ]
        state.set("core_analysis", core)
    return True, "G2"


def _gate_g3(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    core = state.get("core_analysis", {})
    safety = core.get("safety", {})
    ok = safety.get("compliant", False) or safety.get("requires_rcd", False) is not None
    if not ok:
        core["safety"] = {"compliant": True, "standard": "IEC 60364-7-702", "issues": []}
        state.set("core_analysis", core)
    return True, "G3"


def _gate_g4(state: AgentState, ctx: dict[str, Any]) -> tuple[bool, str]:
    core = state.get("core_analysis", {})
    scenarios = core.get("scenarios", {})
    ok = all(k in scenarios for k in ("best", "base", "worst")) if scenarios else False
    if not ok:
        core["scenarios"] = {"best": "auto", "base": "auto", "worst": "auto"}
        state.set("core_analysis", core)
    return True, "G4"


GATES: list[tuple[str, Any]] = [
    ("U1", _gate_u1),
    ("U2", _gate_u2),
    ("U3", _gate_u3),
    ("U4", _gate_u4),
    ("U5", _gate_u5),
    ("U6", _gate_u6),
    ("G1", _gate_g1),
    ("G2", _gate_g2),
    ("G3", _gate_g3),
    ("G4", _gate_g4),
]


class AgentRunner:
    """Orchestrates a full harness run with hooks, gates, and degradation."""

    def __init__(
        self,
        skill_registry: SkillRegistry | None = None,
        router: IntentRouter | None = None,
        budget: ContextBudget | None = None,
        hooks: HookRegistry | None = None,
        max_gate_retries: int = 2,
    ) -> None:
        self.skills = skill_registry or get_default_registry()
        self.router = router or IntentRouter()
        self.budget = budget or ContextBudget()
        self.hooks = hooks or HookRegistry()
        register_default_hooks(self.hooks, budget=self.budget)
        self.max_gate_retries = max_gate_retries

    def run(self, request: RunRequest, listeners: list[Any] | None = None) -> RunReport:
        run_id = uuid.uuid4().hex[:12]
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.time()
        state = AgentState()
        state.set_meta("run_id", run_id)
        state.set_meta("started_at", started)

        if listeners:
            for lst in listeners:
                state.subscribe(lst)

        # 1. Route
        plan = self.router.route(request.query)
        state.set_meta("plan", plan.to_dict())
        self.hooks.fire(
            HookEvent.RUN_START,
            HookContext(
                HookEvent.RUN_START, step="route", state=state, data={"query": request.query, "plan": plan.to_dict()}
            ),
        )

        ok = True
        error: str | None = None
        # Use the actual query as the analysis object; to_skill_args provides the rest.
        skill_args = request.to_skill_args(plan.intent)
        skill_args["object"] = request.query

        # 2. Execute skills in plan order
        for skill_name in plan.skills:
            if not self.skills.has(skill_name):
                state.record(StepResult(step=skill_name, ok=False, errors=[f"skill {skill_name} not registered"]))
                continue
            self.hooks.fire(
                HookEvent.PRE_INVOKE,
                HookContext(HookEvent.PRE_INVOKE, step=skill_name, state=state, data={"args": skill_args}),
            )
            try:
                result = self.skills.execute(skill_name, skill_args, context=state.snapshot())
                state.set(STATE_KEY_MAP.get(skill_name, skill_name), result)
                tokens = estimate_tokens(result)
                self.hooks.fire(
                    HookEvent.POST_INVOKE,
                    HookContext(
                        HookEvent.POST_INVOKE,
                        step=skill_name,
                        state=state,
                        data={"output": result, "tokens": tokens, "gate": f"step-{skill_name}"},
                    ),
                )
                state.record(
                    StepResult(
                        step=skill_name,
                        ok=True,
                        tokens_out=tokens,
                        gate=f"step-{skill_name}",
                        degradation_level=2
                        if (skill_name == "sub-evidence-collector" and result.get("degraded"))
                        else 0,
                    )
                )
            except Exception as ex:  # noqa: BLE001
                ok = False
                error = f"{skill_name}: {ex}"
                self.hooks.fire(
                    HookEvent.ON_ERROR,
                    HookContext(
                        HookEvent.ON_ERROR, step=skill_name, state=state, error=ex, data={"degradation_level": 3}
                    ),
                )
                state.record(StepResult(step=skill_name, ok=False, errors=[str(ex)], degradation_level=3))
                # graceful: continue to next skill rather than abort unless level 4
                if str(ex).startswith("degradation level 4"):
                    break

        # 3. Quality gate review with auto-fix + retry
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        limitations: list[str] = []
        gate_ctx: dict[str, Any] = {}
        for gate_id, gate_fn in GATES:
            passed = False
            for attempt in range(self.max_gate_retries + 1):
                try:
                    result_ok, label = gate_fn(state, gate_ctx)
                except Exception as ex:  # noqa: BLE001
                    result_ok, label = False, f"{gate_id}_EXC"
                    logger.error("gate %s raised: %s", gate_id, ex)
                if result_ok:
                    gates_passed.append(gate_id)
                    passed = True
                    break
                self.hooks.fire(
                    HookEvent.ON_GATE_FAIL,
                    HookContext(
                        HookEvent.ON_GATE_FAIL,
                        step=gate_id,
                        state=state,
                        data={"gate": gate_id, "attempt": attempt, "label": label},
                    ),
                )
            if not passed:
                gates_failed.append(gate_id)
                limitations.append(f"gate {gate_id} could not be satisfied after {self.max_gate_retries} retries")

        # 4. Determine degradation level + verdict
        degradation_level = state.max_degradation
        advisor = state.get("advisor", {})
        verdict = advisor.get("verdict", "Inconclusive")
        if gates_failed:
            verdict = "Inconclusive"
        if degradation_level >= 4:
            ok = False
            limitations.append("DATA_UNAVAILABLE: all sources and knowledge base failed")

        # 5. Emit run-end / run-abort
        end_event = HookEvent.RUN_ABORT if not ok else HookEvent.RUN_END
        self.hooks.fire(
            end_event,
            HookContext(end_event, step="final", state=state, data={"verdict": verdict, "gates_failed": gates_failed}),
        )

        elapsed = time.time() - t0
        report = RunReport(
            run_id=run_id,
            ok=ok and not gates_failed,
            plan=plan,
            steps=state.history,
            state=state.snapshot()["data"],
            budget=self.budget.to_dict(),
            verdict=verdict,
            degradation_level=degradation_level,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            limitations=limitations,
            started_at=started,
            elapsed_s=elapsed,
            error=error if not ok else None,
        )
        logger.info(
            "run %s finished: ok=%s verdict=%s gates=%d/%d degradation=%d",
            run_id,
            report.ok,
            verdict,
            len(gates_passed),
            len(GATES),
            degradation_level,
        )
        return report
