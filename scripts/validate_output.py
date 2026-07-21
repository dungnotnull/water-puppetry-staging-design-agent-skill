"""
scripts/validate_output.py - Validate a generated report against its schema.

Loads a final-report JSON file and validates it against
assets/schemas/final-report.schema.json, then runs a content audit (gate
coverage, disclosure presence, verdict membership). Exits non-zero on failure.

Usage:
    python -m scripts.validate_output path/to/report.json
    python -m scripts.validate_output --report-json '{...}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.exceptions import ValidationError
from tools.logger import setup_logger
from tools.schema import load_schema, validate
from tools.tool_registry import VERDICTS

logger = setup_logger("validate_output")

REQUIRED_GATES = ["U1", "U2", "U3", "U4", "U5", "U6", "G1", "G2", "G3", "G4"]


def audit(report: dict) -> list[str]:
    issues: list[str] = []
    if report.get("recommendation", {}).get("verdict") not in VERDICTS:
        issues.append(f"verdict not in declared set {VERDICTS}")
    if not report.get("disclosure"):
        issues.append("disclosure missing (U2)")
    checklist = report.get("gate_checklist", [])
    missing = [g for g in REQUIRED_GATES if not any(g in c for c in checklist)]
    if missing:
        issues.append(f"gate checklist missing: {missing}")
    if not report.get("evidence_collected"):
        issues.append("evidence_collected empty (U1)")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a final report against schema + audit")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("path", nargs="?", help="Path to report JSON file")
    group.add_argument("--report-json", help="Inline report JSON string")
    args = parser.parse_args()

    if args.report_json:
        try:
            report = json.loads(args.report_json)
        except json.JSONDecodeError as ex:
            print(f"invalid JSON: {ex}", file=sys.stderr)
            return 2
    else:
        try:
            report = json.loads(Path(args.path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as ex:
            print(f"cannot load report: {ex}", file=sys.stderr)
            return 2

    schema = load_schema("final-report")
    schema_errors: list[str] = []
    try:
        validate(report, schema)
    except ValidationError as ex:
        schema_errors.append(str(ex))

    audit_issues = audit(report)

    if schema_errors or audit_issues:
        for e in schema_errors:
            print(f"SCHEMA FAIL: {e}")
        for e in audit_issues:
            print(f"AUDIT FAIL: {e}")
        return 1
    print("report valid: schema + audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
