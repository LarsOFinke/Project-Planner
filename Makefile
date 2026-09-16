.PHONY: setup run test lint

setup:
	./scripts/bootstrap.sh

run:
	.venv/bin/project-planner

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check src tests
