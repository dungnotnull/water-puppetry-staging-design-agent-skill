.PHONY: install install-dev lint lint-fix test test-cov run run-live validate scenarios orchestrate seed clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .
	ruff format --check .

lint-fix:
	ruff check . --fix
	ruff format .

test:
	pytest -v

test-cov:
	pytest --cov=tools --cov-report=term --cov-report=html

run:
	python tools/knowledge_updater.py --dry-run

run-live:
	python tools/knowledge_updater.py

validate:
	python tools/validate_project.py

scenarios:
	python tools/run_test_scenarios.py

orchestrate:
	python -m scripts.orchestrate --query "Design a water-puppetry scenario for the Le Loi legend" --log-level WARNING

seed:
	python -m scripts.seed_knowledge_base --dry-run

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
