# CLAUDE.md -- Skill 167: water-puppetry-staging-design

## Skill Identity
- **Skill Name:** `water-puppetry-staging-design`
- **Tagline:** Water-Puppetry (Roi Nuoc) Scenario Design & Modern Lighting/Effects Integration -- Traditional Performing Arts Staging & Production Design analysis & decision-support harness.
- **Current Phase:** Phase 7 -- Flexible Agent Architecture, Hooks, Tools & Modular Directories (COMPLETE)
- **Version:** 1.1.0
- **Folder:** `D:\972026\167-water-puppetry-staging-design\`

---

## Problem This Skill Solves

This skill provides a structured, evidence-backed analytical workflow for
**Traditional Performing Arts Staging & Production Design**. It gathers authoritative real-time and reference data, applies
recognized domain methods, cross-references academic research, and delivers
actionable outputs that are fully evidenced, risk/limitation-disclosed, and
traceable to authoritative sources -- continuously self-improving through an
automated knowledge crawl pipeline.

---

## Harness Flow Summary

```
/water-puppetry-staging-design invoked
|
+- Step 1: sub-gather-requirements   -> Clarify the object of analysis, constraints, timeframe, available inputs, target audience, and language before any data fetching.
+- Step 2: sub-evidence-collector   -> Fetch authoritative real-time and reference data for the object: current status/parameters, authoritative documents/standards, and recent developments from domain and academic sources.
+- Step 3: sub-core-analysis   -> Analyze and design a water-puppetry scenario integrating traditional folk storytelling with modern lighting and physical effects, grounded in heritage and safety.
+- Step 4: sub-knowledge-updater   -> Query SECOND-KNOWLEDGE-BRAIN.md for authoritative academic and professional evidence; surface citations with tier labels and flag gaps for the crawl pipeline.
+- Step 5: sub-advisor   -> Synthesize all prior analysis into a risk-disclosed conclusion with a full evidence chain and recommended actions.
+- Step 6: main (quality gate)       -> verify evidence hierarchy, disclosure, output polish
```

---

## Agent Runtime Architecture (Phase 7)

The harness is backed by a composable runtime in `tools/` (documented in
`SKILL.md`):

- **`tools/router.py`** -- chain-of-thought `IntentRouter` (intent classification + ordered skill plan + language detection).
- **`tools/skill_registry.py`** -- `SkillRegistry` (resolve / execute / validate against `assets/schemas/*.json`).
- **`tools/tool_registry.py`** -- 12 schema-validated domain tools agents invoke dynamically.
- **`tools/hooks.py`** -- lifecycle hook system (8 events, 5 built-in hooks, `HookDecision`).
- **`tools/state.py`** -- thread-safe shared `AgentState` + step history.
- **`tools/context.py`** -- `ContextBudget` + token estimation + compaction hints.
- **`tools/agent_runner.py`** -- production orchestrator (router + registries + hooks + 10 gates).
- **`tools/schema.py`** -- dependency-free JSON-Schema-style validation.
- **`tools/config_loader.py`** -- typed loader for `config/*.yaml` with env-overridable feature flags.

Modular directories: `/scripts` (automation/ingestion), `/references` (domain
knowledge + prompt templates for RAG), `/assets` (diagrams + JSON schemas),
`/config` (declarative, type-safe configuration). Run end-to-end offline via
`python -m scripts.orchestrate --query "..."`.

## Sub-Skills

| File | Purpose |
|------|---------|
| `skills/sub-gather-requirements.md` | Clarify the object of analysis, constraints, timeframe, available inputs, target audience, and language before any data fetching. |
| `skills/sub-evidence-collector.md` | Fetch authoritative real-time and reference data for the object: current status/parameters, authoritative documents/standards, and recent developments from domain and academic sources. |
| `skills/sub-core-analysis.md` | Analyze and design a water-puppetry scenario integrating traditional folk storytelling with modern lighting and physical effects, grounded in heritage and safety. |
| `skills/sub-knowledge-updater.md` | Query SECOND-KNOWLEDGE-BRAIN.md for authoritative academic and professional evidence; surface citations with tier labels and flag gaps for the crawl pipeline. |
| `skills/sub-advisor.md` | Synthesize all prior analysis into a risk-disclosed conclusion with a full evidence chain and recommended actions. |

---

## Tools Required

- **WebSearch** -- live domain news, reports, standards updates
- **WebFetch** -- scrape Traditional Performing Arts Staging & Production Design authoritative sources
- **Read / Write** -- read SECOND-KNOWLEDGE-BRAIN.md; append knowledge entries
- **Bash** -- run `tools/knowledge_updater.py` for periodic crawl
- **Skill** -- invoke sub-skills sequentially through the harness

---

## Knowledge Sources

### Domain Authoritative Sources
- UNESCO ICH -- Vietnamese water puppetry
- OISTAT (International Association of Theatre Designers) -- oistat.org
- USITT (US Institute for Theatre Technology) -- usitt.org
- ESTA/ANSI E1 stage lighting control (DMX/sACN)
- PLASA entertainment technology standards
- IEC safety standards for stage lighting
- Vietnam National Puppet Theatre

### Academic & Research Sources
- Theatre Journal -- Johns Hopkins UP
- Performance Research -- Taylor & Francis
- Journal of Theatre and Performance Design -- Taylor & Francis
- Lighting Research & Technology -- SAGE
- Entertainment Computing -- Elsevier
- Asian Theatre Journal -- Project MUSE

### Academic Crawl Targets
- Semantic Scholar / Google Scholar for "Traditional Performing Arts Staging & Production Design" keyword clusters
- Domain preprint servers where applicable
- Standards bodies and professional associations (see data sources)

---

## Supporting Python Tools

| File | Purpose |
|------|---------|
| `tools/knowledge_updater.py` | Crawl pipeline: fetches latest papers + news -> appends to SECOND-KNOWLEDGE-BRAIN.md |
| `tools/test_knowledge_updater.py` | pytest test suite for hash, scoring, formatting, and edge cases |
| `tools/run_test_scenarios.py` | Structural & content validator for 8-File Contract |
| `tools/validate_project.py` | 8-File Contract project validator |
| `tools/logger.py` | Centralized structured logging (ANSI colors, file output) |
| `tools/exceptions.py` | Domain-specific exception hierarchy |
| `tools/config.py` | Configuration loader with env var support |
| `tools/schema.py` | JSON-Schema-style validation for skill/tool I/O |
| `tools/state.py` | Shared, thread-safe execution state + history |
| `tools/context.py` | Context-window / token-budget management |
| `tools/hooks.py` | Lifecycle hook system (8 events, 5 built-in hooks) |
| `tools/tool_registry.py` | 12 schema-validated domain tool handlers |
| `tools/skill_registry.py` | Skill registry: resolve / execute / validate |
| `tools/router.py` | Chain-of-thought intent router |
| `tools/agent_runner.py` | Production orchestrator (router + registries + hooks + gates) |
| `tools/config_loader.py` | Typed loader for config/*.yaml + feature flags |

---

## Scripts (Phase 7)

| Script | Purpose |
|--------|---------|
| `scripts/orchestrate.py` | Run the harness end-to-end (offline, deterministic) |
| `scripts/seed_knowledge_base.py` | Idempotently seed the brain from curated references |
| `scripts/run_crawl.py` | Wrapper around the knowledge crawl pipeline |
| `scripts/setup_env.py` | Local setup: venv, deps, .env, validation |
| `scripts/validate_output.py` | Validate a final report against schema + audit |

## Automated Knowledge Update Schedule

```cron
# Weekly academic update (Mondays 8:00 AM)
0 8 * * 1 cd D:/972026/167-water-puppetry-staging-design && python tools/knowledge_updater.py >> logs/knowledge_update.log 2>&1

# Daily news update (Daily 7:00 AM)
0 7 * * * cd D:/972026/167-water-puppetry-staging-design && python tools/knowledge_updater.py --news-only >> logs/knowledge_news.log 2>&1
```

Manual: `python tools/knowledge_updater.py --dry-run` | `--keywords "..."` | `--news-only` | `--log-level DEBUG`

---

## Active Development Tasks

- [x] Phase 0: Architecture & source map
- [x] Phase 1: Core sub-skills (production-grade)
- [x] Phase 2: Main harness + quality gates + degradation
- [x] Phase 3: Knowledge pipeline + tests + cron
- [x] Phase 4: Testing & validation
- [x] Phase 5: Integration & polish
- [x] Phase 6: Production-grade hardening & open-source readiness
- [x] Phase 7: Flexible agent architecture, hooks, tools & modular directories

---

## References

- `PROJECT-detail.md` -- full technical specification
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` -- build roadmap
- `SKILL-STANDARD.md` -- library-wide skill standard (8-File Contract, quality gates U1-U6, sub-skill spec)
- `SECOND-KNOWLEDGE-BRAIN.md` -- self-improving knowledge base
- `progression.json` -- skill progression tracker
- `SKILL.md` -- skill registry documentation (registration, resolution, execution, validation, I/O schemas)
- Reference impl: `D:\vn-finance-analysis-hd-skill`
