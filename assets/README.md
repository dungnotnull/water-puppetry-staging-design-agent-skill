# assets/

Static resources, system diagrams, and JSON schemas.

## Contents

| Path | Purpose |
|------|---------|
| `diagrams/harness-architecture.mmd` | Mermaid diagram of the agent harness flow |
| `diagrams/skill-registry-flow.mmd` | Mermaid diagram of skill registry resolution |
| `diagrams/hooks-lifecycle.mmd` | Mermaid sequence diagram of the hook lifecycle |
| `schemas/*.schema.json` | JSON-Schema input/output contracts for skills and tools |

Render Mermaid diagrams with any Mermaid viewer (e.g. GitHub renders `.mmd` in
fenced ```mermaid blocks; or use `mermaid-cli`: `mmdc -i assets/diagrams/harness-architecture.mmd -o out.svg`).

## Schema Index

| Schema | Bound to |
|--------|----------|
| `requirements` | sub-gather-requirements I/O |
| `evidence-bundle` | sub-evidence-collector I/O |
| `core-analysis` | sub-core-analysis I/O |
| `knowledge-evidence` | sub-knowledge-updater I/O |
| `advisor-conclusion` | sub-advisor I/O |
| `harness-input` / `harness-output` | main harness I/O |
| `final-report` | human-facing final report |
| `tool-call` | envelope for a dynamic tool invocation |
| `tool-*` | per-tool input contracts |
