# Contributing to water-puppetry-staging-design

## Development Setup

```bash
git clone <repo-url>
cd 167-water-puppetry-staging-design

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
pip install -e ".[dev]"
pre-commit install
```

## Development Commands

```bash
make install  # Install all dependencies including dev
make lint     # Run ruff linting and formatting checks
make test     # Run all tests
make run      # Dry-run the knowledge updater
```

## Code Style

- Python 3.11+ with type hints on all public functions
- Formatting via `ruff format` (Black-compatible)
- Linting via `ruff check`
- Max line length: 120 characters
- Use `logging` module (never `print()`) for application output
- Custom exceptions in `tools/exceptions.py`
- Docstrings follow Google style for public modules

## Pull Request Process

1. Fork and create a feature branch
2. Ensure `make test` passes
3. Ensure `make lint` passes
4. Update documentation if needed
5. Add changes to `CHANGELOG.md` under `[Unreleased]`
6. Submit a PR with a clear description

## Testing

```bash
pytest                                    # All tests
pytest --cov=tools --cov-report=term      # With coverage
pytest tools/test_knowledge_updater.py -v # Specific file
```

## Sub-Skill Development

Sub-skills follow the spec in `SKILL-STANDARD.md`. Each must have:
- Frontmatter with `name` and `description`
- `## Role & Persona` section
- `## Workflow` section with numbered steps
- `## Tools` section
- `## Output Format` section
- `## Quality Gates` section
