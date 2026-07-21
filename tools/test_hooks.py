"""
test_hooks.py - Tests for tools/hooks.py (lifecycle hook system).
Run: pytest tools/test_hooks.py -v
"""

from __future__ import annotations

from tools.context import ContextBudget
from tools.hooks import (
    HookContext,
    HookDecision,
    HookEvent,
    HookRegistry,
    register_default_hooks,
)
from tools.state import AgentState


class TestRegistry:
    def test_register_and_fire(self) -> None:
        reg = HookRegistry()
        calls: list[str] = []

        def handler(ctx: HookContext) -> None:
            calls.append(ctx.event.value)

        reg.register(HookEvent.RUN_START, "h1", handler, priority=10)
        reg.register(HookEvent.RUN_START, "h2", handler, priority=5)
        reg.fire(HookEvent.RUN_START, HookContext(HookEvent.RUN_START))
        # priority ascending: h2 (5) fires before h1 (10)
        assert calls == ["run_start", "run_start"]

    def test_priority_order(self) -> None:
        reg = HookRegistry()
        order: list[str] = []
        reg.register(HookEvent.PRE_INVOKE, "late", lambda c: order.append("late"), priority=100)
        reg.register(HookEvent.PRE_INVOKE, "early", lambda c: order.append("early"), priority=1)
        reg.fire(HookEvent.PRE_INVOKE, HookContext(HookEvent.PRE_INVOKE))
        assert order == ["early", "late"]

    def test_unregister(self) -> None:
        reg = HookRegistry()
        reg.register(HookEvent.RUN_END, "h", lambda c: None)
        assert reg.unregister(HookEvent.RUN_END, "h") is True
        assert reg.names(HookEvent.RUN_END) == []

    def test_handler_exception_isolated(self) -> None:
        reg = HookRegistry()

        def bad(ctx: HookContext) -> None:
            raise RuntimeError("boom")

        reg.register(HookEvent.RUN_END, "bad", bad)
        reg.register(HookEvent.RUN_END, "good", lambda c: None)
        # should not raise
        reg.fire(HookEvent.RUN_END, HookContext(HookEvent.RUN_END))

    def test_decision_returned(self) -> None:
        reg = HookRegistry()
        reg.register(HookEvent.ON_ERROR, "d", lambda c: HookDecision(action="abort", reason="x"), priority=10)
        decisions = reg.fire(HookEvent.ON_ERROR, HookContext(HookEvent.ON_ERROR))
        assert len(decisions) == 1
        assert decisions[0].action == "abort"


class TestDefaultHooks:
    def test_token_budget_consumes(self) -> None:
        budget = ContextBudget(model_limit=10000, reserve_for_output=1000)
        reg = HookRegistry()
        register_default_hooks(reg, budget=budget)
        state = AgentState()
        ctx = HookContext(
            HookEvent.POST_INVOKE,
            step="sub-evidence-collector",
            state=state,
            data={"output": {"a": "x" * 100}, "tokens": 500},
        )
        reg.fire(HookEvent.POST_INVOKE, ctx)
        assert budget.consumed == 500

    def test_register_default_is_idempotent(self) -> None:
        budget = ContextBudget()
        reg = HookRegistry()
        register_default_hooks(reg, budget=budget)
        names_before = reg.names(HookEvent.POST_INVOKE)
        register_default_hooks(reg, budget=budget)
        # re-registration overwrites same names, not duplicates
        assert reg.names(HookEvent.POST_INVOKE) == names_before
