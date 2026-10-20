#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python_bin="${PYTHON_BIN:-.venv/bin/python}"
"$python_bin" -c 'import sys; sys.exit(not ((3, 11) <= sys.version_info[:2] < (3, 14)))' || {
    echo 'Python 3.11–3.13 is required to build the wheel.' >&2
    exit 1
}

mkdir -p dist/wheels
"$python_bin" -m pip wheel --no-deps --wheel-dir dist/wheels .
"$python_bin" scripts/wheel_path.py
