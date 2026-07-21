"""
hooks.py - Lifecycle hook system for the agent harness.

Hooks let external logic plug into the harness lifecycle without modifying the
core runner. The hook registry supports ordered, named handlers for a fixed set
of lifecycle events (see ``HookEvent``). Handlers receive a ``HookContext``
carrying the event name, the agent state snapshot, the active step, and a
mutable ``data`` dict for cross-handler chaining. Handlers may return
``HookDecision`` values to influence the runner (skip, retry, abort, inject).

Built-in hooks (registered by ``register_default_hooks``):
  - logging_hook        : structured event log to the logger
  - token_budget_hook   : consume tokens into ContextBudget; trigger compaction
  - gate_audit_hook     : record gate outcomes into state history
  - degradation_hook    : escalate graceful-degradation level on failures
  - event_emitter_hook  : fan-out to user-supplied listeners (state sync / SSE)

Usage:
    from tools.hooks import HookRegistry, HookEvent, register_default_hooks
    reg = HookRegistry()
    register_default_hooks(reg, budget=budget, logger=log)
    reg.fire(HookEvent.PRE_INVOKE, ctx)
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from tools.context import ContextBudget, estimate_tokens
from tools.logger import setup_logger
from tools.state import AgentState

logger = setup_logger("hooks")


class HookEvent(str, enum.Enum):
    """Fixed set of harness lifecycle events."""

    RUN_START = "run_start"
    PRE_INVOKE = "pre_invoke"
    POST_INVOKE = "post_invoke"
    ON_GATE_FAIL = "on_gate_fail"
    ON_ERROR = "on_error"
    ON_DEGRADE = "on_degrade"
    RUN_END = "run_end"
    RUN_ABORT = "run_abort"


@dataclass
class HookDecision:
    """A hook may return a decision to steer the runner."""

    action: str = "continue"  # continue | skip | retry | abort | inject
    retry_step: str = ""
    inject: dict[str, Any] | None = None
    reason: str = ""


@dataclass
class HookContext:
    """Payload passed to every hook handler."""

    event: HookEvent
    step: str = ""
    state: AgentState | None = None
    data: dict[str, Any] = field(default_factory=dict)
    error: BaseException | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.value,
            "step": self.step,
            "data": dict(self.data),
            "error": repr(self.error) if self.error else None,
            "extras": dict(self.extras),
        }


HookHandler = Callable[[HookContext], HookDecision | None]


class HookRegistry:
    """Ordered registry of hook handlers keyed by event."""

    def __init__(self) -> None:
        self._handlers: dict[HookEvent, list[tuple[str, HookHandler, int]]] = {}

    def register(
        self,
        event: HookEvent,
        name: str,
        handler: HookHandler,
        priority: int = 100,
    ) -> None:
        bucket = self._handlers.setdefault(event, [])
        # idempotent by name: replace any existing handler with the same name
        bucket[:] = [t for t in bucket if t[0] != name]
        bucket.append((name, handler, priority))
        bucket.sort(key=lambda t: t[2])

    def unregister(self, event: HookEvent, name: str) -> bool:
        bucket = self._handlers.get(event, [])
        before = len(bucket)
        self._handlers[event] = [t for t in bucket if t[0] != name]
        return len(self._handlers[event]) != before

    def names(self, event: HookEvent) -> list[str]:
        return [t[0] for t in self._handlers.get(event, [])]

    def fire(self, event: HookEvent, ctx: HookContext) -> list[HookDecision]:
        """Invoke all handlers for ``event`` in priority order. Returns decisions."""
        decisions: list[HookDecision] = []
        for name, handler, _ in list(self._handlers.get(event, [])):
            try:
                result = handler(ctx)
            except Exception as ex:  # noqa: BLE001 - hook errors must not kill the run
                logger.error("hook %s for %s raised: %s", name, event.value, ex)
                continue
            if result is not None:
                decisions.append(result)
        return decisions

    def events(self) -> Iterable[HookEvent]:
        return self._handlers.keys()


# ---------------------------------------------------------------------------
# Built-in hooks
# ---------------------------------------------------------------------------


def logging_hook(level: int = logging.INFO) -> HookHandler:
    log = setup_logger("hooks.audit")

    def handler(ctx: HookContext) -> None:
        log.log(level, "event=%s step=%s data=%s", ctx.event.value, ctx.step, ctx.data)
        if ctx.error is not None:
            log.error("event=%s error=%r", ctx.event.value, ctx.error)

    return handler


def token_budget_hook(budget: ContextBudget) -> HookHandler:
    def handler(ctx: HookContext) -> HookDecision | None:
        if ctx.event == HookEvent.POST_INVOKE:
            payload = ctx.data.get("output")
            tokens = ctx.data.get("tokens") or estimate_tokens(payload)
            budget.consume(stage=ctx.step or "unknown", tokens=int(tokens))
            ctx.extras["budget"] = budget.to_dict()
            if budget.exceeded():
                logger.warning("context budget exceeded after step %s: %s", ctx.step, budget.compaction_hint())
                return HookDecision(action="continue", reason=budget.compaction_hint())
        return None

    return handler


def gate_audit_hook() -> HookHandler:
    def handler(ctx: HookContext) -> None:
        if ctx.event == HookEvent.ON_GATE_FAIL:
            gate = ctx.data.get("gate", "?")
            attempt = ctx.data.get("attempt", 0)
            logger.warning("gate %s failed (attempt %s)", gate, attempt)
        elif ctx.event == HookEvent.POST_INVOKE:
            gate = ctx.data.get("gate")
            if gate:
                logger.info("step %s passed gate %s", ctx.step, gate)

    return handler


def degradation_hook() -> HookHandler:
    def handler(ctx: HookContext) -> HookDecision | None:
        if ctx.event == HookEvent.ON_ERROR:
            level = int(ctx.data.get("degradation_level", 1))
            logger.warning("degradation escalated to level %d on step %s", level, ctx.step)
            if level >= 4:
                return HookDecision(action="abort", reason="degradation level 4: data unavailable")
        elif ctx.event == HookEvent.ON_DEGRADE:
            level = int(ctx.data.get("degradation_level", 0))
            logger.info("degradation level set to %d", level)
        return None

    return handler


def event_emitter_hook(listeners: list[Callable[[str, dict[str, Any]], None]]) -> HookHandler:
    def handler(ctx: HookContext) -> None:
        payload = ctx.to_dict()
        for listener in list(listeners):
            try:
                listener(ctx.event.value, payload)
            except Exception as ex:  # noqa: BLE001
                logger.error("event listener raised: %s", ex)

    return handler


def register_default_hooks(
    registry: HookRegistry,
    budget: ContextBudget | None = None,
    listeners: list[Callable[[str, dict[str, Any]], None]] | None = None,
    log_level: int = logging.INFO,
) -> HookRegistry:
    """Register the built-in hook set in priority order."""
    registry.register(HookEvent.RUN_START, "logging", logging_hook(log_level), priority=10)
    registry.register(HookEvent.PRE_INVOKE, "logging", logging_hook(log_level), priority=10)
    registry.register(HookEvent.POST_INVOKE, "logging", logging_hook(log_level), priority=10)
    registry.register(HookEvent.ON_GATE_FAIL, "logging", logging_hook(logging.WARNING), priority=10)
    registry.register(HookEvent.ON_ERROR, "logging", logging_hook(logging.ERROR), priority=10)
    registry.register(HookEvent.ON_DEGRADE, "logging", logging_hook(logging.WARNING), priority=10)
    registry.register(HookEvent.RUN_END, "logging", logging_hook(log_level), priority=10)
    registry.register(HookEvent.RUN_ABORT, "logging", logging_hook(logging.ERROR), priority=10)

    registry.register(HookEvent.ON_GATE_FAIL, "gate_audit", gate_audit_hook(), priority=20)
    registry.register(HookEvent.POST_INVOKE, "gate_audit", gate_audit_hook(), priority=20)

    if budget is not None:
        registry.register(HookEvent.POST_INVOKE, "token_budget", token_budget_hook(budget), priority=30)

    registry.register(HookEvent.ON_ERROR, "degradation", degradation_hook(), priority=30)
    registry.register(HookEvent.ON_DEGRADE, "degradation", degradation_hook(), priority=30)

    if listeners:
        registry.register(HookEvent.RUN_START, "emitter", event_emitter_hook(listeners), priority=40)
        registry.register(HookEvent.POST_INVOKE, "emitter", event_emitter_hook(listeners), priority=40)
        registry.register(HookEvent.ON_ERROR, "emitter", event_emitter_hook(listeners), priority=40)
        registry.register(HookEvent.RUN_END, "emitter", event_emitter_hook(listeners), priority=40)

    return registry
