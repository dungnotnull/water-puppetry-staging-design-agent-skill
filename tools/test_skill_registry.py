"""
test_skill_registry.py - Tests for tools/skill_registry.py.
Run: pytest tools/test_skill_registry.py -v
"""

from __future__ import annotations

import pytest

from tools.exceptions import ValidationError
from tools.skill_registry import get_default_registry


@pytest.fixture(scope="module")
def reg():
    return get_default_registry()


class TestRegistry:
    def test_all_skills_registered(self, reg) -> None:
        expected = {
            "water-puppetry-staging-design",
            "sub-gather-requirements",
            "sub-evidence-collector",
            "sub-core-analysis",
            "sub-knowledge-updater",
            "sub-advisor",
        }
        assert expected.issubset(set(reg.names()))

    def test_resolve_unknown_raises(self, reg) -> None:
        with pytest.raises(ValidationError):
            reg.resolve("nope")

    def test_by_capability(self, reg) -> None:
        assert len(reg.by_capability("research")) >= 2

    def test_graph(self, reg) -> None:
        g = reg.graph()
        assert "nodes" in g and "edges" in g
        assert any(e["from"] == "water-puppetry-staging-design" for e in g["edges"])


class TestGatherRequirements:
    def test_ok(self, reg) -> None:
        r = reg.execute("sub-gather-requirements", {"object": "Le Loi legend"})
        assert r["object"] == "Le Loi legend"
        assert r["analysis_type"] == "combined"

    def test_missing_object_raises(self, reg) -> None:
        with pytest.raises(ValidationError):
            reg.execute("sub-gather-requirements", {"scope": "x"})


class TestEvidenceCollector:
    def test_degraded_when_empty(self, reg) -> None:
        r = reg.execute("sub-evidence-collector", {"sources": []})
        assert r["degraded"] is True

    def test_tiered(self, reg) -> None:
        r = reg.execute(
            "sub-evidence-collector",
            {
                "sources": [
                    {"title": "IEC", "url": "https://iec.ch", "venue": "iec", "date": "2010"},
                    {"title": "blog", "url": "https://b", "venue": "blog", "date": "2024"},
                ]
            },
        )
        assert r["authoritative_docs"][0]["tier"] == 1
        assert r["recent_news"][0]["tier"] == 4


class TestCoreAnalysis:
    def test_full(self, reg) -> None:
        r = reg.execute(
            "sub-core-analysis",
            {
                "theme": "Le Loi returns the sword",
                "venue": {"pool_length_m": 9, "pool_width_m": 9, "pool_depth_m": 1.0},
                "equipment": {"fixtures": [{"ip_rating": "IP65", "near_water": True}]},
                "lighting": {"angle_degrees": 22, "color_temp_k": 3200},
                "safety": {"rcd_trip_ma": 30, "distance_to_water_m": 1.0},
            },
        )
        assert r["folktale_grounded"] is True
        assert r["pool"]["meets_repertoire_standard"] is True
        assert r["scenarios"]["best"]


class TestKnowledgeUpdater:
    def test_lookup(self, reg) -> None:
        r = reg.execute("sub-knowledge-updater", {"keywords": ["water puppetry", "lighting"]})
        assert r["coverage"] in ("Strong", "Moderate", "Weak")


class TestAdvisor:
    def test_verdict(self, reg) -> None:
        r = reg.execute(
            "sub-advisor",
            {
                "risks": [{"description": "x", "probability": 2, "impact": 4}],
                "evidence_strength": 0.85,
                "data_available": True,
                "scenarios": {"best": "b", "base": "x", "worst": "w"},
            },
        )
        assert r["verdict"] in (
            "Production-Ready Design",
            "Feasible with Refinements",
            "High-Risk Production",
            "Inconclusive",
        )
        assert r["disclosure"]

    def test_safe_execute_error(self, reg) -> None:
        r = reg.safe_execute("sub-advisor", {"risks": "not-a-list"})
        assert r["ok"] is False
