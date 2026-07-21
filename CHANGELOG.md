## [1.1.0] - 2026-07-20

### Added
- Flexible agent architecture: chain-of-thought `IntentRouter` (`tools/router.py`).
- Modular `SkillRegistry` and `ToolRegistry` with JSON-schema-validated I/O (`tools/skill_registry.py`, `tools/tool_registry.py`).
- Lifecycle hook system with 8 events and 5 built-in hooks (`tools/hooks.py`).
- Shared `AgentState` and `ContextBudget` for state sync and context-window management (`tools/state.py`, `tools/context.py`).
- Production `AgentRunner` orchestrator wiring router + registries + hooks + 10 quality gates with 2-retry auto-fix and graceful degradation (`tools/agent_runner.py`).
- Dependency-free JSON-Schema-style validation (`tools/schema.py`) and typed YAML config loader (`tools/config_loader.py`).
- 12 schema-validated domain tools (IP rating, DMX addressing, pool volume, lighting angle, electrical safety, folktale repertoire, evidence tier, risk matrix, verdict classifier, knowledge lookup, token estimation, report validation).
- 21 JSON schemas in `assets/schemas/` and 3 Mermaid diagrams in `assets/diagrams/`.
- Modular directories: `/scripts` (5 scripts), `/references` (5 references + 6 prompt templates), `/config` (6 YAML configs).
- `SKILL.md` comprehensive skill registry documentation.
- 81 new tests across 7 test modules (116 total).

### Changed
- `skills/main.md` gains a "Modular Architecture" section referencing the new runtime.
- `tools/validate_project.py` and `tools/run_test_scenarios.py` extended with modular-architecture checks (133 + 143 total) and path bootstrap fixes.
- Bumped version to 1.1.0.

# Changelog

All notable changes to water-puppetry-staging-design will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-10

### Added
- Complete 5-sub-skill harness architecture for water-puppetry staging design
- `skills/main.md` — orchestrator with 6-step execution protocol, 10 quality gates (U1–U6 + G1–G4), graceful degradation (Levels 0–4), and bilingual (vi/en) support
- `skills/sub-gather-requirements.md` — intake specialist for requirements clarification
- `skills/sub-evidence-collector.md` — data librarian for real-time + cached evidence fetching
- `skills/sub-core-analysis.md` — production designer for folk-tale scenario, puppet mechanics, lighting, effects, and safety design
- `skills/sub-knowledge-updater.md` — research librarian for knowledge-base evidence retrieval and gap detection
- `skills/sub-advisor.md` — senior advisor for risk-disclosed synthesis and conclusion
- `SECOND-KNOWLEDGE-BRAIN.md` — seeded living knowledge base with 7 sections
- `tools/knowledge_updater.py` — ArXiv + Semantic Scholar crawl pipeline with SHA256 dedup and composite scoring
- `tools/test_knowledge_updater.py` — pytest test suite for dedup, scoring, formatting, and edge cases
- `tools/run_test_scenarios.py` — structural and content validator for 8-File Contract
- `tests/test-scenarios.md` — 5 E2E test scenarios covering all gates and verdicts
- Production-grade infrastructure: logging system, custom exceptions, config loader
- Open-source files: LICENSE, CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CITATION.cff
- CI/CD: GitHub Actions for lint + test, PyPI release workflow
- Developer tooling: pyproject.toml, Makefile, ruff.toml, .editorconfig, .pre-commit-config.yaml
- `SKILL-STANDARD.md` — library-wide skill standard with 8-File Contract and quality gates
- `tools/validate_project.py` — 8-File Contract project validator
- `progression.json` — skill progression tracker
