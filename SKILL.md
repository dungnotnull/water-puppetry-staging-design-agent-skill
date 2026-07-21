# SKILL.md - Skill Registry Documentation

> **Authoritative reference for how skills are registered, resolved, executed,
> and validated** in the `water-puppetry-staging-design` harness. This document
> is the human-readable counterpart of the runtime registry in
> `tools/skill_registry.py` and the declarative configuration in
> `config/skill_registry.yaml`.

The harness uses a **modular skill-registry pattern**: a chain-of-thought router
classifies intent, a registry resolves skills by name (or capability), each
skill declares a JSON-schema input/output contract, executes through a pure
handler, and a lifecycle hook system emits events for audit/state-sync. This
replaces the rigid "main + 5 fixed sub-skills" reference with a composable,
extensible architecture while preserving the same domain bookends.

---

## 1. Concepts

| Term | Definition |
|------|------------|
| **Skill** | A named unit of work with a handler, an input schema, an output schema, declared tools, and gate bindings. |
| **Sub-skill** | A skill invoked by the main harness (step > 0). |
| **Tool** | A domain utility (schema-validated handler) an agent invokes dynamically. See `tools/tool_registry.py`. |
| **Hook** | A lifecycle handler fired at fixed events (pre_invoke, post_invoke, on_gate_fail, ...). See `tools/hooks.py`. |
| **Router** | The chain-of-thought intent classifier that selects the ordered skill plan. See `tools/router.py`. |
| **State** | The shared `AgentState` carrying each step's structured output + history. See `tools/state.py`. |
| **Gate** | A quality predicate (U1-U6 universal, G1-G4 domain) with auto-fix + 2-retry enforcement. |

---

## 2. Skill Registry

The registry (`tools/skill_registry.py::SkillRegistry`) is the single source of
truth for "which skills exist, what they accept/return, and how they are
invoked".

### 2.1 Registration

A skill is a `Skill` dataclass registered via `registry.register(skill)`. The
default registry is built by `get_default_registry()` and overlays metadata from
`config/skill_registry.yaml`:

```python
from tools.skill_registry import Skill, SkillRegistry, get_default_registry

reg = get_default_registry()
# or compose your own:
reg = SkillRegistry()
reg.register(Skill(
    name="sub-core-analysis",
    description="Design a water-puppetry scenario grounded in heritage + safety.",
    handler=my_handler,
    input_schema=load_schema("core-analysis"),
    output_schema=load_schema("core-analysis"),
    sub_skills=[],
    tools=["score_folktale_repertoire", "estimate_pool_volume", "validate_ip_rating",
           "lighting_angle_check", "electrical_safety_check"],
    gates=["G1", "G2", "G3", "G4"],
    capabilities=["design", "engineer"],
    step=3,
    category="sub-agent",
))
```

### 2.2 Resolution

Resolution precedence is declared in `config/skill_registry.yaml` under
`resolution.precedence`: `exact` (name match) -> `capability` (tag match) ->
`category` fallback. The default skill is `water-puppetry-staging-design`.

```python
skill = reg.resolve("sub-core-analysis")      # exact name
skills = reg.by_capability("research")        # capability match
skills = reg.by_category("sub-agent")         # category fallback
```

### 2.3 Execution

`registry.execute(name, args, context, validate_io=True)` validates `args`
against `input_schema`, invokes the handler, then validates the result against
`output_schema`. `safe_execute` wraps errors into `{ok, result|error}` for
graceful degradation.

```python
result = reg.execute("sub-core-analysis", {"theme": "Le Loi", "venue": {...}, ...})
```

### 2.4 Validation

Schemas live in `assets/schemas/<name>.schema.json` and are loaded by
`tools/schema.py::load_schema`. Validation supports the JSON-Schema subset used
by this project: `type`, `required`, `properties`, `enum`, `minimum`/`maximum`,
`minItems`/`maxItems`, `items`, `additionalProperties`, `oneOf`, `pattern`,
`const`. A `ValidationError` (gate=`schema`|`skill`) is raised on failure.

---

## 3. Registered Skills

| # | Skill | Step | Category | Capabilities | Tools | Gates | Input schema | Output schema |
|---|-------|------|----------|--------------|-------|-------|--------------|---------------|
| 1 | `water-puppetry-staging-design` | 0 | harness | analyze, design, advise, orchestrate | all 10 | U1-U6, G1-G4 | `harness-input` | `harness-output` |
| 2 | `sub-gather-requirements` | 1 | sub-agent | intake | - | G-REQ | `requirements` | `requirements` |
| 3 | `sub-evidence-collector` | 2 | sub-agent | research | `evidence_tier` | U1, U3 | `evidence-bundle` | `evidence-bundle` |
| 4 | `sub-core-analysis` | 3 | sub-agent | design, engineer | `score_folktale_repertoire`, `estimate_pool_volume`, `validate_ip_rating`, `lighting_angle_check`, `electrical_safety_check` | G1, G2, G3, G4 | `core-analysis` | `core-analysis` |
| 5 | `sub-knowledge-updater` | 4 | sub-agent | research, rag | `knowledge_lookup` | U1 | `knowledge-evidence` | `knowledge-evidence` |
| 6 | `sub-advisor` | 5 | sub-agent | advise, synthesize | `risk_matrix`, `verdict_classifier` | U2, U6 | `advisor-conclusion` | `advisor-conclusion` |

The skill dependency graph (who chains to whom) is returned by
`registry.graph()` and rendered in `assets/diagrams/skill-registry-flow.mmd`.

---

## 4. Input / Output JSON Schemas

All schemas are committed under `assets/schemas/`. Summary contracts:

### 4.1 `requirements` (sub-gather-requirements)

```json
{
  "object": "string (min 1)",
  "scope": "string",
  "timeframe": "string",
  "available_inputs": ["string"],
  "target_audience": "string",
  "language": "English | Vietnamese | en | vi",
  "analysis_type": "combined | design | risk | comparison",
  "assumptions": ["string"]
}
```

### 4.2 `evidence-bundle` (sub-evidence-collector)

```json
{
  "current_data":      [{"title","url","date","tier","tier_label"}],
  "authoritative_docs":[{"title","url","date","tier","tier_label"}],
  "recent_news":       [{"title","url","date","tier","tier_label"}],
  "reference_benchmarks": [{"title","url","tier"}],
  "degraded": "boolean",
  "limitation_flag": "string | null"
}
```

### 4.3 `core-analysis` (sub-core-analysis)

```json
{
  "theme": "string",
  "folktale": {"id","title","category","keywords","score","match_fraction"},
  "folktale_grounded": "boolean",
  "pool": {"length_m","width_m","depth_m","volume_m3","volume_liters","mass_kg","surface_m2","meets_repertoire_standard"},
  "lighting": {"angle_check": {...}, "color_temp_k": "integer"},
  "fixture_checks": [{"ip_rating","first_digit","second_digit","submerged","near_water","compliant","reason","standard"}],
  "safety": {"rcd_trip_ma","distance_to_water_m","has_galvanic_isolation","requires_rcd","rcd_compliant","isolation_compliant","compliant","issues","standard"},
  "effects": ["string"],
  "scenarios": {"best","base","worst"}
}
```

### 4.4 `knowledge-evidence` (sub-knowledge-updater)

```json
{
  "citations": [{"title","doi_or_url","tier","keyword_hits"}],
  "gaps": ["string"],
  "coverage": "Strong | Moderate | Weak",
  "count": "integer"
}
```

### 4.5 `advisor-conclusion` (sub-advisor)

```json
{
  "verdict": "Production-Ready Design | Feasible with Refinements | High-Risk Production | Inconclusive",
  "scenarios": {"best","base","worst"},
  "key_risks": [{"description","probability","impact","score","level","action"}],
  "evidence_chain": [{"claim","source","tier"}],
  "remediation": ["string"],
  "disclosure": "string (min 1)"
}
```

### 4.6 `harness-input` / `harness-output` (main harness)

`harness-input` requires `object` plus optional `sources`, `venue`, `equipment`,
`lighting`, `safety`, `effects`, `risks`, `keywords`, `evidence_strength` (0-1),
`evidence_chain`, `remediation`. `harness-output` requires the five step outputs
plus `verdict` and `degradation_level` (0-4).

### 4.7 `final-report` (human-facing)

The report emitted per the Output Format in `skills/main.md`. Required keys:
`title`, `date` (YYYY-MM-DD), `language`, `executive_summary`, `inputs_and_scope`,
`evidence_collected` (min 1), `analysis`, `action_plan` (min 1), `academic_evidence`,
`disclosure`, `recommendation.verdict` (enum), `gate_checklist`. Validate with
`python -m scripts.validate_output report.json` or the
`validate_report_schema` tool.

### 4.8 `tool-call` (envelope)

```json
{"tool": "string", "args": "object", "call_id": "string?", "validate_io": "boolean?"}
```

---

## 5. Tool Registry

Tools (`tools/tool_registry.py::ToolRegistry`) are schema-validated domain
utilities. The manifest is documented in `config/tools.yaml`. Available tools:

| Tool | Category | Input schema | Description |
|------|----------|--------------|-------------|
| `validate_ip_rating` | safety | `tool-validate-ip-rating` | Validate luminaire IP rating (IEC 60529) near/under water |
| `compute_dmx_address` | lighting | `tool-compute-dmx-address` | DMX512-A start address + footprint validation |
| `estimate_pool_volume` | engineering | `tool-estimate-pool-volume` | Pool volume, mass, surface area |
| `lighting_angle_check` | lighting | `tool-lighting-angle-check` | Glare/reflection angle zone check |
| `electrical_safety_check` | safety | `tool-electrical-safety-check` | RCD + isolation check (IEC 60364-7-702) |
| `score_folktale_repertoire` | heritage | `tool-score-folktale-repertoire` | Match query against tich tro repertoire |
| `evidence_tier` | evidence | `tool-evidence-tier` | 4-tier evidence classification |
| `risk_matrix` | advisory | `tool-risk-matrix` | 1-25 risk score from probability x impact |
| `verdict_classifier` | advisory | `tool-verdict-classifier` | Map profile to one of 4 verdicts |
| `knowledge_lookup` | knowledge | `tool-knowledge-lookup` | Query SECOND-KNOWLEDGE-BRAIN.md |
| `estimate_tokens` | context | `tool-estimate-tokens` | Token-count estimation |
| `validate_report_schema` | validation | `tool-validate-report-schema` | Validate a final report |

Policy (`config/tools.yaml::policy`): offline-first (`allow_network_tools: false`),
input validation required, max 50 calls per run.

---

## 6. Hooks & Lifecycle

Hook events (fixed): `run_start`, `pre_invoke`, `post_invoke`, `on_gate_fail`,
`on_error`, `on_degrade`, `run_end`, `run_abort`. Built-in hooks (priority
ascending): `logging` (10), `gate_audit` (20), `token_budget` (30),
`degradation` (30), `event_emitter` (40, disabled by default). A hook may return
a `HookDecision` (`continue | skip | retry | abort | inject`). See
`config/hooks.yaml` and `tools/hooks.py`. Wiring rendered in
`assets/diagrams/hooks-lifecycle.mmd`.

---

## 7. End-to-End Execution Flow

1. `AgentRunner.run(RunRequest)` creates an `AgentState` and `ContextBudget`.
2. `IntentRouter.route(query)` classifies intent and emits the ordered skill plan
   (chain-of-thought reasoning is recorded in `RoutingPlan.reasoning`).
3. Each skill in the plan: `pre_invoke` hook -> `registry.execute` (schema-
   validated) -> state update -> `post_invoke` hook (token budget consumed).
4. On error: `on_error` / `on_degrade` hooks fire; degradation level escalates;
   the runner continues unless level 4 (abort).
5. Quality gates U1-U6 + G1-G4 run with auto-fix + 2-retry max; failures emit
   `on_gate_fail` and become explicit limitations.
6. `run_end` (or `run_abort`) hook fires; a `RunReport` is returned with the
   full state, budget, gate outcomes, limitations, and verdict.

Run it:

```bash
python -m scripts.orchestrate --query "Design a water-puppetry scenario for Le Loi" --json
```

---

## 8. Extension Guide

- **Add a skill**: append to `config/skill_registry.yaml`, add a handler in
  `tools/skill_registry.py`, add `assets/schemas/<name>.schema.json`, register
  in `get_default_registry()`.
- **Add a tool**: add a handler + `Tool(...)` in `tools/tool_registry.py`, add
  `config/tools.yaml` entry and `assets/schemas/tool-<name>.schema.json`.
- **Add a hook**: write a `HookHandler` and `registry.register(event, name, handler, priority)`.
- **Add a gate**: append `(gate_id, predicate)` to `GATES` in `tools/agent_runner.py`
  and document it in `skills/main.md`.
- **Add domain reference**: drop a file in `references/` and reference it from the
  relevant skill/tool; it is the curated ground truth for RAG grounding.

---

## 9. Related Files

| File | Role |
|------|------|
| `tools/skill_registry.py` | Runtime skill registry + built-in handlers |
| `tools/tool_registry.py` | Runtime tool registry + built-in handlers |
| `tools/router.py` | Chain-of-thought intent router |
| `tools/hooks.py` | Lifecycle hook system |
| `tools/state.py` | Shared execution state + history |
| `tools/context.py` | Context-window / token-budget management |
| `tools/agent_runner.py` | Production orchestrator (router + registry + hooks + gates) |
| `tools/schema.py` | JSON-Schema-style validation |
| `tools/config_loader.py` | Typed loader for `config/*.yaml` |
| `config/skill_registry.yaml` | Declarative skill metadata |
| `config/tools.yaml` | Declarative tool metadata + policy |
| `config/hooks.yaml` | Hook wiring catalog |
| `config/feature_flags.yaml` | System-wide feature flags |
| `config/llm_params.yaml` | LLM parameters + context policy |
| `config/sources.yaml` | Tiered authoritative + academic sources |
| `assets/schemas/*.schema.json` | I/O JSON schemas |
| `assets/diagrams/*.mmd` | Architecture diagrams |
| `references/*` | Curated domain knowledge + prompt templates |