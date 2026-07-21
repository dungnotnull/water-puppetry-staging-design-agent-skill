"""
validate_project.py — Skill 167: water-puppetry-staging-design
8-File Contract validator. Verifies all required deliverable files exist,
have correct structure, and pass content checks.

Usage:
    python tools/validate_project.py [--verbose] [--json]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.logger import setup_logger

logger = setup_logger(__name__)

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "CLAUDE.md",
    "PROJECT-detail.md",
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
    "README.md",
    "SECOND-KNOWLEDGE-BRAIN.md",
    "skills/main.md",
    "tools/knowledge_updater.py",
    "tests/test-scenarios.md",
]

OPTIONAL_OPENSOURCE_FILES = [
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "CITATION.cff",
    "pyproject.toml",
    "Makefile",
    ".pre-commit-config.yaml",
    ".editorconfig",
    ".env.example",
    "ruff.toml",
    "progression.json",
    "SKILL.md",
]

# Phase 7: flexible agent architecture, hooks, tools, modular directories
MODULAR_DIRS = ["scripts", "references", "assets", "config"]
NEW_MODULES = [
    "tools/schema.py",
    "tools/state.py",
    "tools/context.py",
    "tools/hooks.py",
    "tools/tool_registry.py",
    "tools/skill_registry.py",
    "tools/router.py",
    "tools/agent_runner.py",
    "tools/config_loader.py",
]
NEW_SCRIPTS = [
    "scripts/orchestrate.py",
    "scripts/seed_knowledge_base.py",
    "scripts/run_crawl.py",
    "scripts/setup_env.py",
    "scripts/validate_output.py",
]
NEW_CONFIGS = [
    "config/skill_registry.yaml",
    "config/tools.yaml",
    "config/hooks.yaml",
    "config/feature_flags.yaml",
    "config/llm_params.yaml",
    "config/sources.yaml",
]
REQUIRED_SCHEMAS = [
    "requirements",
    "evidence-bundle",
    "core-analysis",
    "knowledge-evidence",
    "advisor-conclusion",
    "harness-input",
    "harness-output",
    "final-report",
    "tool-call",
]

REQUIRED_SUB_SKILLS = [
    "sub-gather-requirements",
    "sub-evidence-collector",
    "sub-core-analysis",
    "sub-knowledge-updater",
    "sub-advisor",
]

MANDATORY_SECTIONS_MAIN = [
    "Role & Persona",
    "Harness Execution Protocol",
    "Quality Gates",
    "Graceful Degradation",
    "Output Format",
]

MANDATORY_SECTIONS_SUB = [
    "Role & Persona",
    "Workflow",
    "Output Format",
    "Quality Gates",
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---", re.S)


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


class ValidationResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.failures: list[str] = []

    def check(self, condition: bool, label: str, is_warning: bool = False) -> None:
        if condition:
            self.passed.append(label)
        elif is_warning:
            self.warnings.append(label)
        else:
            self.failures.append(label)

    @property
    def success(self) -> bool:
        return len(self.failures) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": len(self.passed),
            "warnings": len(self.warnings),
            "failures": len(self.failures),
            "passed_items": self.passed,
            "warning_items": self.warnings,
            "failure_items": self.failures,
        }


def validate(verbose: bool = False) -> ValidationResult:
    r = ValidationResult()

    # 1. Required files exist
    for f in REQUIRED_FILES:
        r.check((ROOT / f).exists(), f"Required file present: {f}")

    # 2. Open-source files
    for f in OPTIONAL_OPENSOURCE_FILES:
        r.check((ROOT / f).exists(), f"Open-source file present: {f}", is_warning=not (ROOT / f).exists())

    # 3. Sub-skills
    skills_dir = ROOT / "skills"
    existing_subs = [s.stem for s in skills_dir.glob("sub-*.md")]
    missing_subs = set(REQUIRED_SUB_SKILLS) - set(existing_subs)
    r.check(
        len(missing_subs) == 0,
        f"All 5 sub-skills present (missing: {missing_subs})" if missing_subs else "All 5 sub-skills present",
    )

    # 4. Sub-skill structure
    for sub_name in REQUIRED_SUB_SKILLS:
        sub_path = skills_dir / f"{sub_name}.md"
        txt = read_file(sub_path)
        m = FRONTMATTER_RE.search(txt)
        r.check(bool(m), f"{sub_name}: frontmatter present")
        if m:
            r.check("name:" in m.group(1), f"{sub_name}: frontmatter has 'name'")
            r.check("description:" in m.group(1), f"{sub_name}: frontmatter has 'description'")
        for sec in MANDATORY_SECTIONS_SUB:
            r.check(sec in txt, f"{sub_name}: section '{sec}'")

    # 5. Main.md structure
    main_txt = read_file(ROOT / "skills" / "main.md")
    m = FRONTMATTER_RE.search(main_txt)
    r.check(bool(m), "main.md: frontmatter present")
    if m:
        r.check("name:" in m.group(1), "main.md: frontmatter has 'name'")
        r.check("description:" in m.group(1), "main.md: frontmatter has 'description'")
    for sec in MANDATORY_SECTIONS_MAIN:
        r.check(sec in main_txt, f"main.md: section '{sec}'")
    r.check("Pre-Flight" in main_txt or "Language Detection" in main_txt, "main.md: pre-flight language detection")
    r.check("limitation" in main_txt.lower(), "main.md: limitation banner support")

    # 6. Quality gates
    universal_gates = [f"U{i}" for i in range(1, 7)]
    domain_gates = ["G1", "G2", "G3", "G4"]
    for g in universal_gates + domain_gates:
        r.check(g in main_txt, f"main.md: gate {g} defined")

    # 7. SECOND-KNOWLEDGE-BRAIN.md structure
    brain = read_file(ROOT / "SECOND-KNOWLEDGE-BRAIN.md")
    brain_sections = [
        "## 1. Core",
        "## 2. Key Research",
        "## 3. State-of-the-Art",
        "## 4. Authoritative Data Sources",
        "## 6. Self-Update Protocol",
        "## 7. Knowledge Update Log",
    ]
    for sec in brain_sections:
        r.check(sec in brain, f"brain: section '{sec}'")
    r.check("Tier 1" in brain and "Tier 4" in brain, "brain: evidence hierarchy tiers defined")
    dois = re.findall(r"10\.\d{4,9}/[^\s|]+", brain)
    r.check(len(dois) >= 2, f"brain: >=2 DOI references (found {len(dois)})")

    # 8. PROJECT-DEVELOPMENT-PHASE-TRACKING.md
    pdpt = read_file(ROOT / "PROJECT-DEVELOPMENT-PHASE-TRACKING.md")
    r.check("Phase 0" in pdpt and "Phase 5" in pdpt, "PDPT: Phase 0 and Phase 5 present")
    r.check("100%" in pdpt, "PDPT: 100% completion markers present")

    # 9. knowledge_updater.py structure
    ku = read_file(ROOT / "tools" / "knowledge_updater.py")
    r.check("load_config" in ku or "KNOWLEDGE_CONFIG" in ku, "knowledge_updater: config mechanism present")
    r.check("sha256" in ku, "knowledge_updater: SHA256 dedup mechanism")
    r.check("score_entry" in ku, "knowledge_updater: scoring function")
    r.check("logging" in ku[:500] or "from tools.logger" in ku, "knowledge_updater: uses logging")

    # 10. Test scenarios
    sc = read_file(ROOT / "tests" / "test-scenarios.md")
    r.check(sc.count("Scenario") >= 5, f"scenarios: >=5 defined (found {sc.count('Scenario')})")
    r.check("degraded" in sc.lower() or "missing" in sc.lower(), "scenarios: degraded-mode case present")

    # 10b. Phase 7: modular architecture
    for d in MODULAR_DIRS:
        r.check((ROOT / d).is_dir(), f"modular directory present: {d}/")
    for f in NEW_MODULES:
        r.check((ROOT / f).exists(), f"new module present: {f}")
    for f in NEW_SCRIPTS:
        r.check((ROOT / f).exists(), f"script present: {f}", is_warning=not (ROOT / f).exists())
    for f in NEW_CONFIGS:
        r.check((ROOT / f).exists(), f"config present: {f}")
    for s in REQUIRED_SCHEMAS:
        r.check((ROOT / "assets" / "schemas" / f"{s}.schema.json").exists(), f"schema present: {s}.schema.json")
    r.check((ROOT / "SKILL.md").exists(), "SKILL.md registry documentation present")
    # agent runtime wiring sanity
    ar = read_file(ROOT / "tools" / "agent_runner.py")
    r.check(
        "IntentRouter" in ar and "SkillRegistry" in ar and "HookRegistry" in ar,
        "agent_runner: router + registry + hooks wired",
    )
    sr = read_file(ROOT / "tools" / "skill_registry.py")
    r.check("get_default_registry" in sr and "SkillRegistry" in sr, "skill_registry: registry pattern")
    tr = read_file(ROOT / "tools" / "tool_registry.py")
    r.check("get_default_registry" in tr and "ToolRegistry" in tr, "tool_registry: registry pattern")

    # 11. PROGRESSION
    prog_path = ROOT / "progression.json"
    if prog_path.exists():
        try:
            data = json.loads(read_file(prog_path))
            r.check(data.get("skill_number") == 167, "progression: skill_number is 167")
            r.check(data.get("status") == "complete", "progression: status is complete")
        except Exception:
            r.check(False, "progression: valid JSON")

    return r


def main() -> None:
    parser = argparse.ArgumentParser(description="8-File Contract project validator")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show passing checks too")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = validate(verbose=args.verbose)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        total = len(result.passed) + len(result.warnings) + len(result.failures)
        print(
            f"[validate_project] {len(result.passed)} passed, {len(result.warnings)} warnings, {len(result.failures)} failures ({total} total checks)"
        )
        if result.warnings:
            for w in result.warnings:
                logger.warning("  WARN: %s", w)
        if result.failures:
            for f in result.failures:
                logger.error("  FAIL: %s", f)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
