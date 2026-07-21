"""
scripts/orchestrate.py - CLI to run the agent harness end-to-end.

Executes the full water-puppetry-staging-design harness (router -> sub-skills ->
quality gates) deterministically and offline, then prints the structured
RunReport. Use this to exercise the architecture without a live LLM.

Usage:
    python -m scripts.orchestrate --query "Design a water-puppetry scenario for Le Loi"
    python -m scripts.orchestrate --query "..." --json --log-level WARNING
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.agent_runner import AgentRunner, RunRequest
from tools.logger import configure_root_logger


def build_request(args: argparse.Namespace) -> RunRequest:
    sources = []
    if args.sources:
        for s in args.sources:
            if "://" in s:
                title, _, url = s.partition("=")
                sources.append({"title": title or url, "url": url, "venue": "", "date": ""})
    return RunRequest(
        query=args.query,
        sources=sources,
        venue={"pool_length_m": args.pool_length, "pool_width_m": args.pool_width, "pool_depth_m": args.pool_depth},
        equipment={"fixtures": [{"ip_rating": args.ip_rating, "near_water": True, "submerged": args.submerged}]},
        lighting={"angle_degrees": args.angle, "color_temp_k": args.color_temp},
        safety={"rcd_trip_ma": args.rcd, "distance_to_water_m": args.distance, "has_galvanic_isolation": True},
        risks=[{"description": "electrical near water", "probability": args.risk_p, "impact": args.risk_i}],
        keywords=args.keywords or [args.query],
        evidence_strength=args.evidence_strength,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the water-puppetry-staging-design harness")
    parser.add_argument("--query", required=True, help="The user request / object of analysis")
    parser.add_argument("--sources", nargs="*", help="Sources as title=url entries")
    parser.add_argument("--pool-length", type=float, default=8.0)
    parser.add_argument("--pool-width", type=float, default=8.0)
    parser.add_argument("--pool-depth", type=float, default=1.0)
    parser.add_argument("--ip-rating", default="IP65")
    parser.add_argument("--submerged", action="store_true")
    parser.add_argument("--angle", type=float, default=22.0, help="Lighting angle (degrees from water surface)")
    parser.add_argument("--color-temp", type=int, default=3200)
    parser.add_argument("--rcd", type=float, default=30.0, help="RCD trip current (mA)")
    parser.add_argument("--distance", type=float, default=1.0, help="Circuit distance to water (m)")
    parser.add_argument("--risk-p", type=int, default=2, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--risk-i", type=int, default=4, choices=[1, 2, 3, 4, 5])
    parser.add_argument("--keywords", nargs="*")
    parser.add_argument("--evidence-strength", type=float, default=0.5)
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    configure_root_logger(level=getattr(logging, args.log_level))
    request = build_request(args)
    report = AgentRunner().run(request)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"run_id={report.run_id} ok={report.ok} verdict={report.verdict}")
        print(f"gates: passed={report.gates_passed} failed={report.gates_failed}")
        print(f"degradation={report.degradation_level} limitations={report.limitations}")
        print(f"tokens_consumed={report.budget['consumed']} hint={report.budget['compaction_hint']}")

    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
