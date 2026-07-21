"""
run_test_scenarios.py — Skill 167: water-puppetry-staging-design
Production-grade structural & content validator. Verifies the 8-File Contract,
sub-skill content, knowledge base, test scenarios, and quality-gate coverage.

Usage:
    python tools/run_test_scenarios.py [--verbose] [--json] [--filter PATTERN]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.logger import setup_logger

logger = setup_logger("run_test_scenarios")

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

GATES = ["U1", "U2", "U3", "U4", "U5", "U6"] + ["G1", "G2", "G3", "G4"]

DOMAIN_GATE_DEFS: list[dict[str, str]] = [
    {
        "id": "G1",
        "check": "Scenario grounded in documented water-puppetry folk-tale repertoire",
        "fix": "Re-source folk tale from heritage references",
    },
    {
        "id": "G2",
        "check": "Lighting specifies IP-rated/water-safe fixtures per IEC/ESTA",
        "fix": "Specify water-safe fixtures per standards",
    },
    {"id": "G3", "check": "Safety plan (electrical + operator) present before effects", "fix": "Prepend safety plan"},
    {
        "id": "G4",
        "check": "Production scenarios (best/base/worst) present",
        "fix": "Build multi-scenario production plan",
    },
]

VERDICTS = ["Production-Ready Design", "Feasible with Refinements", "High-Risk Production", "Inconclusive"]


def read_file(path: Path) -> str:
    """Read a file as UTF-8, returning empty string if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


class CheckResult:
    """Accumulates test check results."""

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.failures: list[str] = []
        self.start_time = time.time()

    def check(self, condition: bool, label: str, skip: bool = False) -> None:
        if skip:
            self.skipped += 1
            return
        if condition:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append(label)

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    def summary(self) -> str:
        parts = [f"{self.passed}/{self.total} passed"]
        if self.skipped:
            parts.append(f"{self.skipped} skipped")
        if self.elapsed > 0.01:
            parts.append(f"{self.elapsed:.2f}s")
        return ", ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "failures": self.failures,
            "elapsed": round(self.elapsed, 3),
        }


class ScenarioValidator:
    """Runs all validation checks against the project."""

    def __init__(self, verbose: bool = False, filter_pattern: str = "") -> None:
        self.verbose = verbose
        self.filter_pattern = filter_pattern
        self.results: list[CheckResult] = []

    def _should_run(self, name: str) -> bool:
        if not self.filter_pattern:
            return True
        return self.filter_pattern.lower() in name.lower()

    def _add_result(self, r: CheckResult) -> None:
        self.results.append(r)
        logger.info("[%s] %s", "PASS" if r.failed == 0 else "FAIL", r.summary())
        if r.failures and self.verbose:
            for f in r.failures:
                logger.error("  FAIL: %s", f)

    def check_file_structure(self) -> CheckResult:
        r = CheckResult("File Structure")
        if not self._should_run("file"):
            return r

        required = [
            "CLAUDE.md",
            "PROJECT-detail.md",
            "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
            "README.md",
            "SECOND-KNOWLEDGE-BRAIN.md",
            "skills/main.md",
            "tools/knowledge_updater.py",
            "tools/test_knowledge_updater.py",
            "tools/run_test_scenarios.py",
            "tests/test-scenarios.md",
            "tests/TEST_RESULTS.md",
        ]
        for f in required:
            r.check((ROOT / f).exists(), f"present: {f}")

        subs = sorted(SKILLS_DIR.glob("sub-*.md"))
        r.check(len(subs) >= 5, f"at least 5 sub-skills (found {len(subs)})")
        expected = {
            "sub-gather-requirements",
            "sub-evidence-collector",
            "sub-core-analysis",
            "sub-knowledge-updater",
            "sub-advisor",
        }
        got = {s.stem for s in subs}
        r.check(got == expected, f"sub-skill set correct ({'OK' if got == expected else f'missing: {expected - got}'})")

        self._add_result(r)
        return r

    def check_frontmatter(self) -> CheckResult:
        r = CheckResult("Frontmatter & Sections")
        if not self._should_run("frontmatter"):
            return r

        fm_re = re.compile(r"^---\s*\n(.*?\n)---", re.S)
        for sub_path in sorted(SKILLS_DIR.glob("sub-*.md")):
            txt = read_file(sub_path)
            m = fm_re.search(txt)
            r.check(bool(m), f"{sub_path.name}: frontmatter")
            if m:
                r.check("name:" in m.group(1), f"{sub_path.name}: frontmatter has 'name'")
                r.check("description:" in m.group(1), f"{sub_path.name}: frontmatter has 'description'")
            for sec in ["Role & Persona", "Workflow", "Output Format", "Quality Gates"]:
                r.check(sec in txt, f"{sub_path.name}: section '{sec}'")

        main_txt = read_file(ROOT / "skills" / "main.md")
        for sec in ["Role & Persona", "Quality Gates", "Graceful Degradation"]:
            r.check(sec in main_txt, f"main.md: section '{sec}'")
        r.check(
            "Harness Execution Protocol" in main_txt or "Workflow" in main_txt,
            "main.md: harness workflow heading",
        )
        r.check("Pre-Flight" in main_txt, "main.md: pre-flight language detection")
        r.check("limitation" in main_txt.lower(), "main.md: limitation banner support")

        self._add_result(r)
        return r

    def check_quality_gates(self) -> CheckResult:
        r = CheckResult("Quality Gates")
        if not self._should_run("gate"):
            return r

        main_txt = read_file(ROOT / "skills" / "main.md")
        for g in GATES:
            r.check(g in main_txt, f"gate {g} defined in main.md")

        adv_path = ROOT / "skills" / "sub-advisor.md"
        adv_txt = read_file(adv_path) if adv_path.exists() else ""
        for v in VERDICTS:
            r.check(v in adv_txt or v in main_txt, f"verdict '{v}' present")

        for gd in DOMAIN_GATE_DEFS:
            r.check(gd["check"] in main_txt or gd["check"][:20] in main_txt, f"domain gate {gd['id']}: check described")

        self._add_result(r)
        return r

    def check_knowledge_brain(self) -> CheckResult:
        r = CheckResult("Knowledge Brain")
        if not self._should_run("brain"):
            return r

        brain = read_file(ROOT / "SECOND-KNOWLEDGE-BRAIN.md")
        r.check("Tier 1" in brain and "Tier 4" in brain, "evidence hierarchy tiers (1-4)")
        dois = re.findall(r"10\.\d{4,9}/[^\s|]+", brain)
        r.check(len(dois) >= 2, f">=2 DOI references (found {len(dois)})")

        sections = [
            "## 1. Core",
            "## 2. Key Research",
            "## 3. State-of-the-Art",
            "## 4. Authoritative Data Sources",
            "## 6. Self-Update Protocol",
            "## 7. Knowledge Update Log",
        ]
        for sec in sections:
            r.check(sec in brain, f"section present: '{sec}'")

        self._add_result(r)
        return r

    def check_test_scenarios(self) -> CheckResult:
        r = CheckResult("Test Scenarios")
        if not self._should_run("scenario"):
            return r

        sc = read_file(ROOT / "tests" / "test-scenarios.md")
        scenario_count = sc.count("Scenario")
        r.check(scenario_count >= 5, f">=5 scenarios (found {scenario_count})")
        r.check(
            "degraded" in sc.lower() or "missing" in sc.lower(),
            "degraded-mode scenario present",
        )
        r.check(
            "conflict" in sc.lower() or "compare" in sc.lower() or "comparison" in sc.lower(),
            "comparison/conflict scenario present",
        )

        for g in ["G1", "G2", "G3"]:
            r.check(g in sc, f"scenario references gate {g}")

        self._add_result(r)
        return r

    def check_tools_python(self) -> CheckResult:
        r = CheckResult("Python Tools")
        if not self._should_run("python"):
            return r

        ku = read_file(ROOT / "tools" / "knowledge_updater.py")
        r.check("KNOWLEDGE_CONFIG" in ku or "load_config" in ku, "knowledge_updater: config present")
        r.check("sha256" in ku, "knowledge_updater: SHA256 dedup")
        r.check("score_entry" in ku, "knowledge_updater: scoring function")
        r.check("logging" in ku or "logger" in ku, "knowledge_updater: uses logging")

        self._add_result(r)
        return r

    def check_docs(self) -> CheckResult:
        r = CheckResult("Documentation")
        if not self._should_run("doc"):
            return r

        pdpt = read_file(ROOT / "PROJECT-DEVELOPMENT-PHASE-TRACKING.md")
        r.check("100%" in pdpt, "PDPT: 100% markers present")
        r.check("Phase 5" in pdpt, "PDPT: Phase 5 present")

        readme = read_file(ROOT / "README.md")
        r.check("Usage" in readme, "README: usage section")

        pd = read_file(ROOT / "PROJECT-detail.md")
        r.check("Harness Architecture" in pd, "PROJECT-detail: harness architecture")
        r.check("Idea (Vietnamese)" in pd or "Tạo skill" in pd, "PROJECT-detail: Vietnamese context")

        self._add_result(r)
        return r

    def check_modular_architecture(self) -> CheckResult:
        r = CheckResult("Modular Architecture")
        if not self._should_run("modular"):
            return r

        for d in ("scripts", "references", "assets", "config"):
            r.check((ROOT / d).is_dir(), f"directory present: {d}/")
        for f in (
            "tools/schema.py",
            "tools/state.py",
            "tools/context.py",
            "tools/hooks.py",
            "tools/tool_registry.py",
            "tools/skill_registry.py",
            "tools/router.py",
            "tools/agent_runner.py",
            "tools/config_loader.py",
        ):
            r.check((ROOT / f).exists(), f"module present: {f}")
        for f in (
            "config/skill_registry.yaml",
            "config/tools.yaml",
            "config/hooks.yaml",
            "config/feature_flags.yaml",
            "config/llm_params.yaml",
            "config/sources.yaml",
        ):
            r.check((ROOT / f).exists(), f"config present: {f}")
        for s in (
            "requirements",
            "evidence-bundle",
            "core-analysis",
            "knowledge-evidence",
            "advisor-conclusion",
            "harness-input",
            "harness-output",
            "final-report",
            "tool-call",
        ):
            r.check((ROOT / "assets" / "schemas" / f"{s}.schema.json").exists(), f"schema present: {s}.schema.json")
        r.check((ROOT / "SKILL.md").exists(), "SKILL.md present")
        for f in (
            "scripts/orchestrate.py",
            "scripts/seed_knowledge_base.py",
            "scripts/run_crawl.py",
            "scripts/setup_env.py",
            "scripts/validate_output.py",
        ):
            r.check((ROOT / f).exists(), f"script present: {f}")
        for f in (
            "references/folk-tale-repertoire.md",
            "references/lighting-standards.md",
            "references/water-stage-engineering.md",
            "references/safety-protocols.md",
            "references/domain-glossary.md",
        ):
            r.check((ROOT / f).exists(), f"reference present: {f}")
        for f in (
            "assets/diagrams/harness-architecture.mmd",
            "assets/diagrams/skill-registry-flow.mmd",
            "assets/diagrams/hooks-lifecycle.mmd",
        ):
            r.check((ROOT / f).exists(), f"diagram present: {f}")

        # runtime sanity: registry + router + hooks + tools load and are consistent
        try:
            from tools.skill_registry import get_default_registry as get_skills
            from tools.tool_registry import get_default_registry as get_tools
            from tools.router import IntentRouter
            from tools.config_loader import load_system_config

            skills = get_skills()
            tools = get_tools()
            r.check(len(skills.names()) >= 6, f"skill registry: >=6 skills (found {len(skills.names())})")
            r.check(len(tools.names()) >= 12, f"tool registry: >=12 tools (found {len(tools.names())})")
            plan = IntentRouter().route("design a water-puppetry scenario")
            r.check(plan.skills[0] == "sub-gather-requirements", "router: bookend start correct")
            r.check(plan.skills[-1] == "sub-advisor", "router: bookend end correct")
            cfg = load_system_config()
            r.check(
                len(cfg.skill_registry["skills"]) == len(skills.names()),
                "config/skill_registry.yaml matches runtime registry",
            )
            r.check(len(cfg.tools["tools"]) == len(tools.names()), "config/tools.yaml matches runtime tool registry")
        except Exception as ex:  # noqa: BLE001
            r.check(False, f"runtime sanity (registries/router/config): {ex}")

        self._add_result(r)
        return r

    def run_all(self) -> list[CheckResult]:
        self.check_file_structure()
        self.check_frontmatter()
        self.check_quality_gates()
        self.check_knowledge_brain()
        self.check_test_scenarios()
        self.check_tools_python()
        self.check_modular_architecture()
        self.check_docs()
        return self.results

    def overall_success(self) -> bool:
        return all(r.failed == 0 for r in self.results)

    def grand_total(self) -> dict[str, int]:
        return {
            "passed": sum(r.passed for r in self.results),
            "failed": sum(r.failed for r in self.results),
            "skipped": sum(r.skipped for r in self.results),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Production-grade structural & content validator for water-puppetry-staging-design",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show failing check details")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--filter", default="", help="Only run checks matching this pattern")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    args = parser.parse_args()

    validator = ScenarioValidator(verbose=args.verbose, filter_pattern=args.filter)
    results = validator.run_all()
    totals = validator.grand_total()

    if args.json:
        output = {
            "overall_success": validator.overall_success(),
            "totals": totals,
            "groups": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))
    else:
        total_checks = totals["passed"] + totals["failed"] + totals["skipped"]
        status = "PASS" if validator.overall_success() else "FAIL"
        logger.info("=" * 50)
        logger.info(
            "[run_test_scenarios] %s | %d/%d passed, %d failed, %d skipped",
            status,
            totals["passed"],
            total_checks,
            totals["failed"],
            totals["skipped"],
        )
        if not validator.overall_success():
            for r in results:
                if r.failed:
                    for f in r.failures:
                        logger.error("  FAIL [%s]: %s", r.name, f)
        logger.info("=" * 50)

    sys.exit(0 if validator.overall_success() else 1)


if __name__ == "__main__":
    main()
