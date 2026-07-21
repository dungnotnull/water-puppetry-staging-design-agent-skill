# scripts/

Automation, ingestion, and local setup routines.

| Script | Purpose |
|--------|---------|
| `setup_env.py` | Local setup: venv, deps, .env, validation |
| `seed_knowledge_base.py` | Idempotently seed SECOND-KNOWLEDGE-BRAIN.md from curated references |
| `run_crawl.py` | Wrapper around the knowledge crawl pipeline |
| `orchestrate.py` | Run the agent harness end-to-end (offline, deterministic) |
| `validate_output.py` | Validate a generated final report against schema + audit |

Run as modules from the project root:

```bash
python -m scripts.orchestrate --query "Design a water-puppetry scenario for Le Loi" --json
python -m scripts.seed_knowledge_base --dry-run
python -m scripts.run_crawl --dry-run
python -m scripts.validate_output path/to/report.json
python -m scripts.setup_env --dev
```