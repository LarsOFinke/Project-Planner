#!/usr/bin/env bash
set -euo pipefail

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$agent_root"

if [[ ! -x .venv/bin/python ]]; then
    echo "Missing .venv. Run: make setup" >&2
    exit 1
fi

.venv/bin/ruff check src tests
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
bash -n scripts/bootstrap.sh
bash -n .agents/scripts/doctor.sh
bash -n .agents/scripts/check-all.sh
bash -n .agents/scripts/collect-diagnostics.sh

long_lines="$(awk 'length($0) > 100 { print FILENAME ":" FNR }' $(rg --files -g '*.py'))"
if [[ -n "$long_lines" ]]; then
    echo "Python lines longer than 100 columns:" >&2
    echo "$long_lines" >&2
    exit 1
fi

echo "All Project Planner checks passed."
