"""
context.py - Context-window management utilities for the agent harness.

Estimates token usage of structured payloads, enforces per-run budgets,
and produces compact "summarization hints" the main agent can use to keep
large evidence bundles within a model's context window. Token estimation is
a deterministic heuristic (no network) so the harness can degrade gracefully
offline.

Usage:
    budget = ContextBudget(model_limit=200_000, reserve_for_output=4096)
    budget.consume(stage="evidence", tokens=context.estimate_tokens(bundle))
    if budget.exceeded(): ... # trigger summarization/compaction
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# Empirical chars-per-token heuristic for mixed English/Vietnamese Markdown.
# Vietnamese diacritics inflate bytes-per-token, so we use a conservative ratio.
_CHARS_PER_TOKEN = 3.6


def estimate_text_tokens(text: str) -> int:
    """Estimate token count for a raw string using a chars-per-token heuristic."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / _CHARS_PER_TOKEN))


def estimate_tokens(obj: Any) -> int:
    """Estimate token count for a structured object by serializing to compact text."""
    if obj is None:
        return 0
    if isinstance(obj, str):
        return estimate_text_tokens(obj)
    import json

    try:
        text = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        text = str(obj)
    return estimate_text_tokens(text)


def summarize(obj: Any, max_tokens: int = 512) -> str:
    """Produce a compact textual summary of ``obj`` truncated to ~max_tokens."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        text = obj
    else:
        import json

        try:
            text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True)
        except (TypeError, ValueError):
            text = str(obj)
    budget_chars = max(1, int(max_tokens * _CHARS_PER_TOKEN))
    if len(text) <= budget_chars:
        return text
    return text[: budget_chars - 3].rstrip() + "..."


@dataclass
class BudgetEntry:
    stage: str
    tokens: int


@dataclass
class ContextBudget:
    """Tracks cumulative token consumption against a per-run context budget."""

    model_limit: int = 200_000
    reserve_for_output: int = 8192
    soft_cap_ratio: float = 0.80
    entries: list[BudgetEntry] = field(default_factory=list)

    @property
    def available(self) -> int:
        return max(0, self.model_limit - self.reserve_for_output - self.consumed)

    @property
    def consumed(self) -> int:
        return sum(e.tokens for e in self.entries)

    @property
    def soft_cap(self) -> int:
        """Token count at which compaction should kick in."""
        return int((self.model_limit - self.reserve_for_output) * self.soft_cap_ratio)

    def consume(self, stage: str, tokens: int) -> None:
        if tokens < 0:
            tokens = 0
        self.entries.append(BudgetEntry(stage=stage, tokens=tokens))

    def would_exceed(self, tokens: int) -> bool:
        return self.consumed + tokens > (self.model_limit - self.reserve_for_output)

    def exceeded(self) -> bool:
        return self.consumed > (self.model_limit - self.reserve_for_output)

    def near_limit(self) -> bool:
        return self.consumed >= self.soft_cap

    def compaction_hint(self) -> str:
        """Return a human-readable hint for when compaction should run."""
        if self.exceeded():
            return "CONTEXT_EXCEEDED: summarize evidence bundles and drop Tier-4 sources"
        if self.near_limit():
            return "CONTEXT_NEAR_LIMIT: prefer Tier-1/2 sources, compact Tier-4 entries"
        return "OK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_limit": self.model_limit,
            "reserve_for_output": self.reserve_for_output,
            "consumed": self.consumed,
            "available": self.available,
            "soft_cap": self.soft_cap,
            "near_limit": self.near_limit(),
            "exceeded": self.exceeded(),
            "compaction_hint": self.compaction_hint(),
            "stages": [{"stage": e.stage, "tokens": e.tokens} for e in self.entries],
        }
