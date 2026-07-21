"""
test_tool_registry.py - Tests for tools/tool_registry.py.
Run: pytest tools/test_tool_registry.py -v
"""

from __future__ import annotations

import pytest

from tools.exceptions import ValidationError
from tools.tool_registry import get_default_registry


@pytest.fixture(scope="module")
def reg():
    return get_default_registry()


class TestRegistry:
    def test_has_all_tools(self, reg) -> None:
        expected = {
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
            "estimate_tokens",
            "validate_report_schema",
        }
        assert expected.issubset(set(reg.names()))

    def test_manifest(self, reg) -> None:
        m = reg.manifest()
        assert len(m) == len(reg.names())
        assert all("name" in e for e in m)


class TestIpRating:
    def test_near_water_ip65_compliant(self, reg) -> None:
        r = reg.call("validate_ip_rating", {"ip_rating": "IP65", "submerged": False})
        assert r["compliant"] is True

    def test_submerged_requires_ip68(self, reg) -> None:
        assert reg.call("validate_ip_rating", {"ip_rating": "IP68", "submerged": True})["compliant"] is True
        assert reg.call("validate_ip_rating", {"ip_rating": "IP65", "submerged": True})["compliant"] is False

    def test_invalid_ip_raises(self, reg) -> None:
        with pytest.raises(ValidationError):
            reg.call("validate_ip_rating", {"ip_rating": "IPABC"})


class TestDmx:
    def test_fits(self, reg) -> None:
        r = reg.call("compute_dmx_address", {"start_address": 1, "channel_footprint": 16})
        assert r["fits_universe"] is True

    def test_overflow(self, reg) -> None:
        r = reg.call("compute_dmx_address", {"start_address": 500, "channel_footprint": 20})
        assert r["fits_universe"] is False
        assert r["overflow_channels"] == 7  # 500+20-1=519; 519-512=7


class TestPool:
    def test_volume(self, reg) -> None:
        r = reg.call("estimate_pool_volume", {"length_m": 9, "width_m": 9, "depth_m": 1.0})
        assert r["volume_m3"] == 81.0
        assert r["meets_repertoire_standard"] is True

    def test_nonstandard(self, reg) -> None:
        r = reg.call("estimate_pool_volume", {"length_m": 5, "width_m": 5, "depth_m": 0.5})
        assert r["meets_repertoire_standard"] is False


class TestLightingAngle:
    def test_optimal(self, reg) -> None:
        r = reg.call("lighting_angle_check", {"angle_degrees": 22})
        assert r["zone"] == "optimal"

    def test_unsafe(self, reg) -> None:
        r = reg.call("lighting_angle_check", {"angle_degrees": 80})
        assert r["zone"] == "unsafe-glare"


class TestElectricalSafety:
    def test_compliant(self, reg) -> None:
        r = reg.call("electrical_safety_check", {"rcd_trip_ma": 30, "distance_to_water_m": 1.0})
        assert r["compliant"] is True

    def test_noncompliant_rcd(self, reg) -> None:
        r = reg.call("electrical_safety_check", {"rcd_trip_ma": 100, "distance_to_water_m": 1.0})
        assert r["compliant"] is False


class TestFolktale:
    def test_match(self, reg) -> None:
        r = reg.call("score_folktale_repertoire", {"query": "Le Loi returns the sword"})
        assert r["grounded"] is True
        assert r["best_match"]["id"] == "hist-le-loi"

    def test_no_match(self, reg) -> None:
        r = reg.call("score_folktale_repertoire", {"query": "quantum computing"})
        assert r["grounded"] is False


class TestEvidenceTier:
    def test_standard_tier1(self, reg) -> None:
        r = reg.call("evidence_tier", {"source": "https://iec.ch", "venue": "iec"})
        assert r["tier"] == 1

    def test_news_tier4(self, reg) -> None:
        r = reg.call("evidence_tier", {"source": "https://blog.example.com", "venue": "blog"})
        assert r["tier"] == 4


class TestRiskAndVerdict:
    def test_risk_matrix(self, reg) -> None:
        r = reg.call("risk_matrix", {"probability": 5, "impact": 5})
        assert r["score"] == 25
        assert r["level"] == "critical"

    def test_verdict_production_ready(self, reg) -> None:
        r = reg.call("verdict_classifier", {"evidence_strength": 0.9, "max_risk_score": 4})
        assert r["verdict"] == "Production-Ready Design"

    def test_verdict_inconclusive_no_data(self, reg) -> None:
        r = reg.call("verdict_classifier", {"evidence_strength": 0.9, "max_risk_score": 4, "data_available": False})
        assert r["verdict"] == "Inconclusive"

    def test_verdict_high_risk(self, reg) -> None:
        r = reg.call("verdict_classifier", {"evidence_strength": 0.5, "max_risk_score": 20})
        assert r["verdict"] == "High-Risk Production"


class TestKnowledgeLookup:
    def test_lookup_returns_matches(self, reg) -> None:
        r = reg.call("knowledge_lookup", {"keywords": ["water puppetry"], "limit": 3})
        assert r["count"] >= 1

    def test_safe_call_on_error(self, reg) -> None:
        r = reg.safe_call("nonexistent_tool", {})
        assert r["ok"] is False


class TestReportSchema:
    def _good(self) -> dict:
        return {
            "title": "R",
            "date": "2026-07-20",
            "language": "English",
            "executive_summary": "x",
            "inputs_and_scope": "y",
            "evidence_collected": [{"a": 1}],
            "analysis": "z",
            "action_plan": ["a"],
            "academic_evidence": [],
            "disclosure": "d",
            "recommendation": {"verdict": "Inconclusive"},
            "gate_checklist": ["U1"],
        }

    def test_valid(self, reg) -> None:
        assert reg.call("validate_report_schema", {"report": self._good()})["valid"] is True

    def test_invalid(self, reg) -> None:
        bad = self._good()
        del bad["disclosure"]
        assert reg.call("validate_report_schema", {"report": bad})["valid"] is False
