#!/usr/bin/env bash
set -euo pipefail

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$agent_root"

if [[ ! -x .venv/bin/python ]]; then
    echo "Missing .venv. Run: make setup" >&2
    exit 1
fi

.venv/bin/ruff check src frontend/src tests .agents/scripts/kivy-event-loop-smoke.py
.venv/bin/ruff format --check src frontend/src tests .agents/scripts/kivy-event-loop-smoke.py
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src frontend/src tests .agents/scripts/kivy-event-loop-smoke.py
bash -n scripts/bootstrap.sh
bash -n .agents/scripts/doctor.sh
bash -n .agents/scripts/check-all.sh
bash -n .agents/scripts/collect-diagnostics.sh
bash -n .agents/scripts/kivy-event-loop-smoke.sh
bash -n deployment.sh
bash -n deploy/activate.sh

if [[ ! -d web/node_modules ]]; then
    echo "Missing web/node_modules. Run: npm --prefix web ci" >&2
    exit 1
fi
npm --prefix web test
npm --prefix web run build
bash .agents/scripts/kivy-event-loop-smoke.sh

long_lines="$(awk 'length($0) > 100 { print FILENAME ":" FNR }' $(rg --files -g '*.py'))"
if [[ -n "$long_lines" ]]; then
    echo "Python lines longer than 100 columns:" >&2
    echo "$long_lines" >&2
    exit 1
fi

echo "All Project Planner checks passed."
