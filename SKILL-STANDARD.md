# SKILL-STANDARD.md — Library-wide skill standard

> Applies to all skills in the Claude Code skill library. Each skill project
> must satisfy the 8-File Contract and implement the quality gates defined below.

---

## 8-File Contract

Every production-ready skill project must contain at minimum these 8 deliverables:

| # | File | Purpose |
|---|------|---------|
| 1 | `CLAUDE.md` | Skill identity, harness flow, sub-skill catalog, tool list, data sources, dev tasks |
| 2 | `PROJECT-detail.md` | Full technical specification: executive summary, problem statement, architecture, E2E execution flow, design decisions |
| 3 | `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` | Build roadmap with phases, tasks, success criteria, and completion percentages |
| 4 | `README.md` | Public-facing: features, installation, usage, testing, roadmap, license |
| 5 | `SECOND-KNOWLEDGE-BRAIN.md` | Self-improving knowledge base with 7 sections (core concepts, key papers, SOTA, data sources, frameworks, self-update protocol, update log) |
| 6 | `skills/main.md` | Main harness entry point — orchestrates sub-skills, quality gates, error handling |
| 7 | `tools/knowledge_updater.py` | Crawl pipeline for automatic knowledge base updates |
| 8 | `tests/test-scenarios.md` | 5+ E2E test scenarios with gate coverage matrix |

Additionally, these files are expected for open-source readiness:
- `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`
- `pyproject.toml`, `Makefile`, `.pre-commit-config.yaml`, `.editorconfig`, `ruff.toml`

---

## Skill Registry Pattern (Phase 7)

In addition to the markdown skill files in `skills/`, the harness is backed by a
runtime skill registry (`tools/skill_registry.py`) documented in `SKILL.md`.
Skills are registered declaratively, resolved by name or capability, executed
through schema-validated handlers, and validated against JSON schemas in
`assets/schemas/`. A chain-of-thought router (`tools/router.py`) selects the
ordered skill plan; lifecycle hooks (`tools/hooks.py`) emit audit/state events.
This keeps the markdown prompts as the human-authored source of truth while the
Python registry provides deterministic execution, validation, and testing.

New skills MUST be: (1) added to `config/skill_registry.yaml`; (2) given a
handler + registration in `tools/skill_registry.py::get_default_registry`;
(3) given an input and output schema in `assets/schemas/`; (4) covered by tests.

## Universal Quality Gates (U1–U6)

These gates apply to every skill's final output regardless of domain. They are
enforced at the harness level (Step 6 in `main.md`).

| Gate | Check | Auto-Fix | Enforcement |
|------|-------|----------|-------------|
| U1 | >=3 sources cited, >=1 academic/authoritative | Fetch from knowledge base / evidence collector | Append missing sources before delivery |
| U2 | Disclosure/limitations before recommendation | Prepend standard disclosure | Block output until disclosure present |
| U3 | Evidence hierarchy stated per source (Tier 1–4) | Annotate source tiers | Tag each source with a tier label |
| U4 | Language matches user preference | Translate output | Run pre-flight language detection |
| U5 | Output uses declared template (all sections) | Reformat to template | Check mandatory sections present |
| U6 | Every claim traceable to >=1 source or flagged | Flag unsupported claims | Mark each claim with source or [analyst judgment] |

---

## Domain-Specific Quality Gates

Each skill defines its own domain gates (G1, G2, G3, ...) in `skills/main.md`.
These gates validate domain-appropriateness of the analysis output.

### Template for domain gates:

```markdown
| G{N} | {what it checks} | {auto-fix procedure} | {enforcement logic} |
```

---

## Sub-Skill File Specification

Every sub-skill markdown file (`skills/sub-*.md`) must contain:

```markdown
---
name: {skill-name}
description: {one-line summary}
---

## Role & Persona
## Workflow
### Step 1: Receive Inputs
### Step 2: Execute Core Task
### Step 3: Emit Outputs
## Tools
## Output Format
## Quality Gates
```

---

## Harness Execution Protocol

Every skill's `main.md` must implement:

1. **Pre-flight** — Language detection, input validation
2. **Sequential execution** — Steps 1–N in strict order; each must pass its gate before next step
3. **Graceful degradation** — Levels 0–4 fallback chain (full sources → secondary → KB-only → partial → unavailable)
4. **Quality gate review** — All gates (U1–U6 + domain gates) checked with auto-fix + 2-retry max
5. **Output template** — Standardized report format with mandatory sections

---

## Evidence Hierarchy

All skills use this 4-tier evidence hierarchy:

- **Tier 1:** Systematic review / meta-analysis / official standard (ISO, UNESCO, IEC, etc.)
- **Tier 2:** Peer-reviewed academic paper / RCT
- **Tier 3:** Industry report / professional association guideline
- **Tier 4:** News / blog / vendor material

---

## Graceful Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | All primary sources reachable | Full evidenced analysis |
| 1 | Some primary sources fail | Use secondary/aggregate sources; flag each substituted source |
| 2 | Most live sources fail | Knowledge base only; flag "historical context as of [date]" |
| 3 | A required input variable missing/stale | Proceed with available; mark missing "DATA UNAVAILABLE" |
| 4 | All sources AND knowledge base fail | Emit "DATA UNAVAILABLE" notice; do NOT fabricate output |
