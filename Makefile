.PHONY: setup run test lint validate

setup:
	./scripts/bootstrap.sh

run:
	.venv/bin/project-planner

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check src frontend/src tests
	.venv/bin/ruff format --check src frontend/src tests

validate:
	bash .agents/scripts/check-all.sh
