# water-puppetry-staging-design

**Water-Puppetry (Roi Nuoc) Scenario Design & Modern Lighting/Effects Integration**

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-blue)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/contributor/water-puppetry-staging-design/actions/workflows/ci.yml/badge.svg)](https://github.com/contributor/water-puppetry-staging-design/actions/workflows/ci.yml)

A professional-grade Claude Code harness for **Traditional Performing Arts Staging & Production Design** -- gathers real-time
authoritative data, applies recognized domain methods, integrates academic
research, and delivers evidence-backed, risk-disclosed outputs.

## Features

- Real-time data aggregation from authoritative Traditional Performing Arts Staging & Production Design sources
- Systematic domain analysis methods with evidence-graded frameworks
- Academic research integration with auto-updating knowledge base
- Risk/limitation-disclosed outputs with scenario coverage
- Self-improving knowledge pipeline (ArXiv + Semantic Scholar crawl)
- Bilingual support (Vietnamese / English)
- 10 quality gates (U1-U6 universal + G1-G4 domain)
- Graceful degradation (Levels 0-4) with explicit limitation flags

## Agent Architecture (v1.1.0)

A composable, production-grade runtime backs the harness (see `SKILL.md`):

- **IntentRouter** (`tools/router.py`) -- chain-of-thought intent classification with an auditable reasoning trace.
- **SkillRegistry** (`tools/skill_registry.py`) -- resolve by name/capability; execute + validate I/O against JSON schemas.
- **ToolRegistry** (`tools/tool_registry.py`) -- 12 schema-validated domain tools (`validate_ip_rating`, `compute_dmx_address`, `estimate_pool_volume`, `lighting_angle_check`, `electrical_safety_check`, `score_folktale_repertoire`, `evidence_tier`, `risk_matrix`, `verdict_classifier`, `knowledge_lookup`, `estimate_tokens`, `validate_report_schema`).
- **HookRegistry** (`tools/hooks.py`) -- 8 lifecycle events with logging, gate audit, token budget, degradation, and event emission hooks.
- **AgentState** (`tools/state.py`) + **ContextBudget** (`tools/context.py`) -- shared state, step history, token budgets, compaction hints.
- **AgentRunner** (`tools/agent_runner.py`) -- orchestrates router + registries + hooks + 10 quality gates with 2-retry auto-fix and graceful degradation.

```
USER INPUT -> IntentRouter -> [sub-skills via SkillRegistry] -> Quality Gates -> RunReport
                                  |                              |
                          ToolRegistry (dynamic)         HookRegistry (lifecycle)
                                  |                              |
                       SECOND-KNOWLEDGE-BRAIN            AgentState + ContextBudget
```

Modular directories: `/scripts` (automation), `/references` (domain knowledge +
prompt templates for RAG), `/assets` (diagrams + JSON schemas), `/config`
(type-safe declarative configuration). Run offline:

```bash
python -m scripts.orchestrate --query "Design a water-puppetry scenario for Le Loi" --json
```

## Installation

```bash
pip install -r requirements.txt
```

For development (includes test runners, linters, type checkers):

```bash
pip install -r requirements.txt
pip install -e ".[dev]"
```

Install skill files to `~/.claude/skills/` or use via project `CLAUDE.md`.

## Usage

### As a Claude Code Skill

```bash
/water-puppetry-staging-design [your query]
```

### Knowledge Base Maintenance

```bash
# Dry-run the crawl pipeline (fetch but don't write)
make run

# Live crawl (appends to SECOND-KNOWLEDGE-BRAIN.md)
python tools/knowledge_updater.py

# Only fetch RSS/news sources
python tools/knowledge_updater.py --news-only

# Custom keywords
python tools/knowledge_updater.py --keywords "modern stage lighting" "DMX control"

# Debug mode with file logging
python tools/knowledge_updater.py --log-level DEBUG --log-file logs/crawl.log
```

### Testing

```bash
# Run all Python tests
make test

# Run with coverage
make test-cov

# Validate project structure (8-File Contract)
make validate

# Run scenario validator
python tools/run_test_scenarios.py --all
```

## Architecture

Harness flow: requirements -> evidence -> core analysis -> knowledge -> synthesis -> quality gate.
See `PROJECT-detail.md` for the full architecture diagram.

```
USER INPUT
    |
    v
[main.md -- water-puppetry-staging-design]
    |
    +-- sub-gather-requirements.md  -> Structured requirements
    +-- sub-evidence-collector.md   -> Evidence bundle
    +-- sub-core-analysis.md        -> Scenario + engineering + lighting + safety
    +-- sub-knowledge-updater.md    -> Academic citations + gap flags
    +-- sub-advisor.md              -> Risk-disclosed conclusion
    |
    +-- [QUALITY GATE -- main.md]
            U1-U6 (universal) + G1-G4 (domain)
```

## Quality Gates

### Universal (U1-U6)
- U1: >=3 sources, >=1 academic/authoritative
- U2: Disclosure before recommendation
- U3: Evidence hierarchy per source (Tier 1-4)
- U4: Language matches user preference
- U5: Output uses declared template
- U6: Every claim traceable to source

### Domain (G1-G4)
- G1: Scenario grounded in documented folk-tale repertoire
- G2: Lighting specifies IP-rated/water-safe fixtures (IEC/ESTA)
- G3: Safety plan present before effects
- G4: Production scenarios (best/base/worst)

## Data Sources

- UNESCO ICH -- Vietnamese water puppetry
- OISTAT (International Association of Theatre Designers)
- USITT (US Institute for Theatre Technology)
- ESTA/ANSI E1 stage lighting control (DMX/sACN)
- PLASA entertainment technology standards
- IEC safety standards for stage lighting
- Vietnam National Puppet Theatre
- Theatre Journal, Performance Research, Asian Theatre Journal, and more

## Development

```bash
make install-dev    # Install all dev dependencies
make lint           # Run ruff checks
make lint-fix       # Auto-fix lint issues
make test           # Run tests
make validate       # Validate project structure
```

## Project Layout

```
skills/        # main.md + 5 sub-skill markdown prompts
tools/         # Python runtime: registries, router, hooks, runner, config, crawl
scripts/       # automation: orchestrate, seed, crawl, setup, validate-output
references/    # domain knowledge + prompt templates (RAG grounding)
assets/        # diagrams + JSON schemas
config/        # declarative YAML config (skills, tools, hooks, flags, llm, sources)
tests/         # E2E scenario specs + results
SECOND-KNOWLEDGE-BRAIN.md  # self-improving knowledge base
SKILL.md       # skill registry documentation
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed:
```bash
cp .env.example .env
```

Key environment variables:
- `WPSD_LOG_LEVEL` -- Logging level (DEBUG/INFO/WARNING/ERROR)
- `WPSD_LOG_FILE` -- Log file path
- `WPSD_DRY_RUN` -- Set to "true" for dry-run mode
- `WPSD_RSS_FEEDS` -- JSON array of RSS feed URLs

## Roadmap

- [x] Phase 0: Architecture
- [x] Phase 1: Core sub-skills
- [x] Phase 2: Main harness + gates
- [x] Phase 3: Knowledge pipeline
- [x] Phase 4: Testing
- [x] Phase 5: Integration & polish
- [x] Phase 6: Production-grade hardening & open-source readiness
- [x] Phase 7: Flexible agent architecture (router/registry/hooks/tools) + modular directories + SKILL.md

## License

MIT -- see [LICENSE](LICENSE).

## Citation

```bibtex
@software{water-puppetry-staging-design,
  title = {water-puppetry-staging-design: Water-Puppetry (Roi Nuoc) Scenario Design & Modern Lighting/Effects Integration},
  year = {2026},
  version = {1.0.0}
}
```

Also see [CITATION.cff](CITATION.cff).
