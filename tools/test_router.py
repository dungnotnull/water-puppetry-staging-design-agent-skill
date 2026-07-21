"""
test_router.py - Tests for tools/router.py (chain-of-thought intent router).
Run: pytest tools/test_router.py -v
"""

from __future__ import annotations

from tools.router import IntentRouter, detect_language


class TestLanguageDetection:
    def test_english(self) -> None:
        assert detect_language("design a water puppetry scenario") == "en"

    def test_vietnamese_diacritics(self) -> None:
        assert detect_language("thiết kế kịch bản múa rối nước") == "vi"


class TestRouting:
    def test_design_intent(self) -> None:
        p = IntentRouter().route("Design a water-puppetry scenario with lighting")
        assert p.intent == "design"
        assert p.needs_core_analysis is True
        assert "sub-core-analysis" in p.skills

    def test_compare_intent(self) -> None:
        p = IntentRouter().route("Compare two water-puppetry scenarios for safety")
        assert p.intent == "compare"
        assert p.multi_object is True
        assert any("COMPARISON" in f for f in p.flags)

    def test_risk_intent(self) -> None:
        p = IntentRouter().route("Assess the risk of submerged electrical fixtures")
        assert p.intent == "risk_assessment"
        assert any("RISK" in f for f in p.flags)

    def test_explain_intent_skips_core(self) -> None:
        p = IntentRouter().route("Explain what DMX512 is")
        assert p.intent == "explain"
        assert p.needs_core_analysis is False
        assert "sub-core-analysis" not in p.skills

    def test_degraded_intent(self) -> None:
        p = IntentRouter().route("Analyze offline with missing data")
        assert p.intent == "degraded"
        assert any("DEGRADATION" in f for f in p.flags)

    def test_bookends_always_present(self) -> None:
        for q in ["design", "compare X vs Y", "explain DMX", "assess risk"]:
            p = IntentRouter().route(q)
            assert "sub-gather-requirements" == p.skills[0]
            assert "sub-advisor" == p.skills[-1]

    def test_confidence_in_range(self) -> None:
        p = IntentRouter().route("design")
        assert 0.0 <= p.confidence <= 1.0

    def test_reasoning_recorded(self) -> None:
        p = IntentRouter().route("design a scenario")
        assert len(p.reasoning) >= 3

    def test_vietnamese_design(self) -> None:
        p = IntentRouter().route("thiết kế kịch bản múa rối nước")
        assert p.language_hint == "vi"
