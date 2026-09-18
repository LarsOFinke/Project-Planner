.PHONY: setup run test lint lock validate

setup:
	./scripts/bootstrap.sh

run:
	.venv/bin/project-planner

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/ruff check src frontend/src tests
	.venv/bin/ruff format --check src frontend/src tests

lock:
	.venv/bin/python -m pip lock \
		'Kivy==2.3.1' 'SQLAlchemy==2.0.54' 'alembic==1.20.0' \
		'fastapi==0.141.1' 'httpx==0.28.1' 'python-multipart==0.0.32' \
		'starlette==0.52.1' 'uvicorn==0.53.0' 'pytest==9.1.1' 'ruff==0.16.8' \
		-o pylock.toml

validate:
	bash .agents/scripts/check-all.sh
