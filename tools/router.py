"""
router.py - Chain-of-thought intent router for the agent harness.

The router inspects the raw user request, classifies the intent, and selects
which sub-skills the main agent must run (and in what order). It is a
deterministic, offline chain-of-thought classifier: it emits an explicit
"reasoning" trace (the "chain of thought") then a routing plan, so the main
agent's decisions are auditable rather than opaque.

Routing respects the harness contract: the fixed bookends
(gather-requirements -> evidence -> knowledge -> advisor) are always present;
the router only decides whether the domain core-analysis step is needed and
whether a comparison/risk sub-plan applies.

Usage:
    from tools.router import IntentRouter
    plan = IntentRouter().route("Compare two water-puppetry scenarios for safety")
    print(plan.to_dict())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# Intent signals mapped to capabilities. Order matters: more specific first.
_INTENT_RULES: list[tuple[str, list[str], list[str]]] = [
    (
        "compare",
        ["compare", "versus", " vs ", "comparison", "contrast", "side-by-side", "so sanh"],
        [
            "sub-gather-requirements",
            "sub-evidence-collector",
            "sub-core-analysis",
            "sub-knowledge-updater",
            "sub-advisor",
        ],
    ),
    (
        "risk_assessment",
        ["risk", "feasibility", "feasible", "danger", "safe", "hazard", "conflict", "rush", "rui ro", "kha thi"],
        [
            "sub-gather-requirements",
            "sub-evidence-collector",
            "sub-core-analysis",
            "sub-knowledge-updater",
            "sub-advisor",
        ],
    ),
    (
        "degraded",
        ["offline", "unreachable", "no data", "missing", "unavailable", "khong co du lieu"],
        ["sub-gather-requirements", "sub-evidence-collector", "sub-knowledge-updater", "sub-advisor"],
    ),
    (
        "explain",
        ["explain", "what is", "how does", "teach", "learn", "education", "giai thich", "hoc"],
        ["sub-gather-requirements", "sub-knowledge-updater", "sub-advisor"],
    ),
    (
        "design",
        ["design", "stage", "lighting", "scenario", "produce", "production", "thiet ke", "kich ban", "anh sang"],
        [
            "sub-gather-requirements",
            "sub-evidence-collector",
            "sub-core-analysis",
            "sub-knowledge-updater",
            "sub-advisor",
        ],
    ),
]

# Fixed bookends that must always run, in order.
_FIXED_BOOKENDS = ["sub-gather-requirements", "sub-evidence-collector", "sub-knowledge-updater", "sub-advisor"]


@dataclass
class RoutingPlan:
    """Output of the router: intent + chain-of-thought + ordered skill plan."""

    intent: str
    confidence: float
    reasoning: list[str]
    skills: list[str]
    needs_core_analysis: bool
    multi_object: bool
    language_hint: str
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "reasoning": list(self.reasoning),
            "skills": list(self.skills),
            "needs_core_analysis": self.needs_core_analysis,
            "multi_object": self.multi_object,
            "language_hint": self.language_hint,
            "flags": list(self.flags),
        }


_VIETNAMESE_RE = re.compile(r"[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựýỳỷỹỵ]", re.UNICODE)


def detect_language(text: str) -> str:
    """Detect Vietnamese vs English from diacritics and common words."""
    if _VIETNAMESE_RE.search(text):
        return "vi"
    vi_words = ["va", "cua", "va", "nhung", "mot", "duoc", "cho", "voi", "khi", "thi"]
    lowered = text.lower()
    if sum(1 for w in vi_words if re.search(rf"\b{w}\b", lowered)) >= 2:
        return "vi"
    return "en"


class IntentRouter:
    """Deterministic chain-of-thought intent router."""

    def route(self, query: str) -> RoutingPlan:
        text = (query or "").lower().strip()
        reasoning: list[str] = []
        language = detect_language(query or "")
        reasoning.append(f"language: detected {language} from input diacritics/lexicon")

        # Count objects to detect comparison (e.g. "compare X and Y").
        multi_object = bool(
            re.search(r"\b(compare|versus| vs |contrast)\b", text) or (" and " in text and text.count(",") >= 1)
        )
        reasoning.append(f"multi_object: {multi_object} (comparison signals scanned)")

        # Score intents by signal hits.
        scores: list[tuple[str, float, list[str]]] = []
        for intent, signals, _skills in _INTENT_RULES:
            hits = sum(1 for s in signals if s in text)
            if hits:
                scores.append((intent, float(hits), signals))
        reasoning.append(f"intent signal scores: {[(i, s) for i, s, _ in scores]}")

        if scores:
            scores.sort(key=lambda t: t[1], reverse=True)
            intent, hits, signals = scores[0]
            total_signals = sum(s for _, s, _ in scores)
            confidence = round(min(hits / max(total_signals, 1) + 0.4, 1.0), 2)
            reasoning.append(f"selected intent '{intent}' via signals {signals[:3]}")
        else:
            intent, confidence = "design", 0.5
            reasoning.append("no explicit intent signals; defaulting to 'design'")

        # Determine if core analysis is needed (compare/risk/design need it).
        needs_core = intent in {"compare", "risk_assessment", "design"}
        reasoning.append(f"needs_core_analysis: {needs_core} for intent '{intent}'")

        # Build the ordered skill plan respecting fixed bookends + core insertion.
        skills = list(_FIXED_BOOKENDS)
        if needs_core and "sub-core-analysis" not in skills:
            # Insert core-analysis after evidence-collector (position 2) and before knowledge-updater.
            skills.insert(2, "sub-core-analysis")
        reasoning.append(f"ordered skill plan: {skills}")

        flags: list[str] = []
        if intent == "degraded":
            flags.append("DEGRADATION_EXPECTED: prepare LIMITATION banner")
        if multi_object:
            flags.append("COMPARISON: apply sub-core-analysis per object")
        if intent == "risk_assessment":
            flags.append("RISK: produce best/base/worst scenarios")

        return RoutingPlan(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            skills=skills,
            needs_core_analysis=needs_core,
            multi_object=multi_object,
            language_hint=language,
            flags=flags,
        )
