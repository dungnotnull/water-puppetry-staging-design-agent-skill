"""
state.py - Shared, thread-safe execution state for the agent harness.

Holds the rolling context produced by each sub-agent step (requirements ->
evidence -> core analysis -> knowledge -> advisor), supports token-budget
accounting, and emits change events for the hooks system. This is the single
source of truth the router, hooks, and agent_runner read/write against.

Usage:
    state = AgentState()
    state.set("requirements", {"object": "...", ...})
    reqs = state.get("requirements")
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    """Outcome of a single harness step."""

    step: str
    ok: bool
    output: Any = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    gate: str = ""
    degradation_level: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "gate": self.gate,
            "degradation_level": self.degradation_level,
        }


class AgentState:
    """Thread-safe shared state bag for one harness invocation.

    Keys hold the structured output of each sub-agent step. ``history``
    accumulates StepResults for audit/replay. ``meta`` holds arbitrary
    per-run metadata (language, started_at, run_id, feature flags snapshot).
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._data: dict[str, Any] = {}
        self._history: list[StepResult] = []
        self._meta: dict[str, Any] = {}
        self._listeners: list[Callable[[str, Any], None]] = []
        self._frozen = False

    # -- core accessors -----------------------------------------------------
    def set(self, key: str, value: Any) -> None:
        if self._frozen:
            raise RuntimeError("AgentState is frozen; cannot mutate")
        with self._lock:
            self._data[key] = value
            self._emit("set", {"key": key, "value": value})

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._data.keys())

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "data": dict(self._data),
                "meta": dict(self._meta),
                "history": [r.to_dict() for r in self._history],
            }

    # -- meta ---------------------------------------------------------------
    def set_meta(self, key: str, value: Any) -> None:
        with self._lock:
            self._meta[key] = value
            self._emit("meta", {"key": key, "value": value})

    def meta(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._meta.get(key, default)

    # -- history ------------------------------------------------------------
    def record(self, result: StepResult) -> None:
        with self._lock:
            self._history.append(result)
            self._emit("step", result.to_dict())

    @property
    def history(self) -> list[StepResult]:
        with self._lock:
            return list(self._history)

    # -- events -------------------------------------------------------------
    def subscribe(self, listener: Callable[[str, Any], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def _emit(self, event: str, payload: Any) -> None:
        for listener in list(self._listeners):
            try:
                listener(event, payload)
            except Exception:  # noqa: BLE001 - listeners must never break the run
                pass

    # -- lifecycle ----------------------------------------------------------
    def freeze(self) -> None:
        with self._lock:
            self._frozen = True

    @property
    def frozen(self) -> bool:
        with self._lock:
            return self._frozen

    def reset(self) -> None:
        with self._lock:
            self._data.clear()
            self._history.clear()
            self._meta.clear()
            self._frozen = False

    # -- token accounting helpers ------------------------------------------
    @property
    def total_tokens(self) -> int:
        with self._lock:
            return sum(r.tokens_in + r.tokens_out for r in self._history)

    @property
    def max_degradation(self) -> int:
        with self._lock:
            return max((r.degradation_level for r in self._history), default=0)
