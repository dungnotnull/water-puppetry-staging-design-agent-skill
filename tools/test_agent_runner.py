"""
test_agent_runner.py - Tests for tools/agent_runner.py (end-to-end orchestrator).
Run: pytest tools/test_agent_runner.py -v
"""

from __future__ import annotations


from tools.agent_runner import AgentRunner, RunRequest


def make_request(*, sources=None, evidence_strength=0.85) -> RunRequest:
    if sources is None:
        sources = [
            {"title": "UNESCO ICH", "url": "https://ich.unesco.org", "venue": "unesco", "date": "2023-01-01"},
            {"title": "IEC 60364-7-702", "url": "https://iec.ch", "venue": "iec", "date": "2010-01-01"},
            {
                "title": "Water Puppetry of Vietnam",
                "url": "10.1353/atj.2001.0013",
                "venue": "Asian Theatre Journal",
                "date": "2001-01-01",
            },
        ]
    return RunRequest(
        query="Design a water-puppetry scenario for the Le Loi legend",
        sources=sources,
        venue={"pool_length_m": 9, "pool_width_m": 9, "pool_depth_m": 1.0},
        equipment={"fixtures": [{"ip_rating": "IP65", "near_water": True}]},
        lighting={"angle_degrees": 22, "color_temp_k": 3200},
        safety={"rcd_trip_ma": 30, "distance_to_water_m": 1.0},
        risks=[{"description": "electrical near water", "probability": 2, "impact": 4}],
        keywords=["water puppetry", "lighting", "Le Loi"],
        evidence_strength=evidence_strength,
    )


class TestRunner:
    def test_full_run_passes_all_gates(self) -> None:
        report = AgentRunner().run(make_request())
        assert report.ok is True
        assert len(report.gates_failed) == 0
        assert report.verdict in ("Production-Ready Design", "Feasible with Refinements")
        assert report.degradation_level == 0
        assert len(report.steps) == 5

    def test_degraded_no_sources_inconclusive(self) -> None:
        report = AgentRunner().run(make_request(sources=[], evidence_strength=0.3))
        # without sources U3 fails -> Inconclusive
        assert report.verdict == "Inconclusive"
        assert report.degradation_level >= 1

    def test_budget_consumed(self) -> None:
        report = AgentRunner().run(make_request())
        assert report.budget["consumed"] > 0
        assert report.budget["exceeded"] is False

    def test_report_serializes(self) -> None:
        report = AgentRunner().run(make_request())
        d = report.to_dict()
        assert d["run_id"]
        assert "plan" in d
        assert "steps" in d

    def test_history_recorded(self) -> None:
        report = AgentRunner().run(make_request())
        assert all(s.step for s in report.steps)

    def test_gate_checklist_complete_on_success(self) -> None:
        report = AgentRunner().run(make_request())
        assert set(report.gates_passed) == {"U1", "U2", "U3", "U4", "U5", "U6", "G1", "G2", "G3", "G4"}
