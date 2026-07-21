# DEVELOPMENT-TRACKING.md - Agent memory log (water-puppetry-staging-design)

> Working memory for continuous development of skill 167. Updated each session.
> Authoritative phase status lives in `PROJECT-DEVELOPMENT-PHASE-TRACKING.md`.

## Current State (2026-07-20)

- **Version:** 1.1.0
- **Phases:** 0-7 all COMPLETE (100%)
- **Status:** PRODUCTION READY, OPEN-SOURCE READY

## Session Log

### 2026-07-20 - Phase 7 delivery

**Goal:** Upgrade to a flexible, production-grade agent architecture with hooks,
tools, a skill registry, `SKILL.md`, and modular directories (`/scripts`,
`/references`, `/assets`, `/config`).

**Implemented:**
- 9 runtime modules in `tools/`: `schema.py`, `state.py`, `context.py`,
  `hooks.py`, `tool_registry.py`, `skill_registry.py`, `router.py`,
  `agent_runner.py`, `config_loader.py`.
- 12 schema-validated domain tools + 6 skills with JSON-schema I/O contracts.
- Chain-of-thought `IntentRouter` with auditable reasoning trace + language detection.
- Lifecycle hook system (8 events, 5 built-in hooks, `HookDecision`).
- `AgentRunner` orchestrator: router + registries + hooks + 10 quality gates
  (U1-U6 + G1-G4) with 2-retry auto-fix and graceful degradation (levels 0-4).
- 21 JSON schemas in `assets/schemas/`, 3 Mermaid diagrams in `assets/diagrams/`.
- 6 YAML configs in `config/` (skill_registry, tools, hooks, feature_flags,
  llm_params, sources) + typed `config_loader.py` with env-overridable flags.
- 5 scripts in `scripts/` (orchestrate, seed_knowledge_base, run_crawl,
  setup_env, validate_output).
- 5 references + 6 prompt templates in `references/`.
- `SKILL.md` comprehensive registry documentation.
- 81 new tests (116 total); updated validators (133 + 143 checks).

**Verification:**
- `pytest tools/` -> 116 passed
- `python tools/validate_project.py` -> 133/133
- `python tools/run_test_scenarios.py` -> 143/143
- `ruff check` + `ruff format --check` -> clean
- `python -m scripts.orchestrate` -> all 10 gates pass end-to-end (offline)

## Key Design Decisions

1. Skill registry as runtime counterpart of markdown prompts; markdown remains
   the human-authored source of truth, Python registry provides deterministic
   execution + validation + testing.
2. Lenient INPUT schemas (only user-required fields) + strict OUTPUT schemas
   (handlers fill defaults, so input validation must not over-constrain).
3. Offline-first: tools are deterministic and require no network; live fetch is
   a feature flag (off by default).
4. Fixed bookends (gather-requirements -> evidence -> knowledge -> advisor)
   always present; router only decides core-analysis insertion -> composable
   without breaking the domain contract.
5. Hooks are isolated: a hook exception never kills a run.

## Next Opportunities (not blocking)

- Wire live evidence collection behind `enable_live_fetch` (WebSearch/WebFetch).
- Add `pydantic`-based schema variant for stricter runtime typing (optional).
- Expand folk-tale repertoire beyond the 12 seeded entries.
- Add a `scripts/render_report.py` to render a RunReport into the markdown
  Output Format from `skills/main.md`.