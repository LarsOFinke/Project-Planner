#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

compatible_python=""
for candidate in python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
        compatible_python="$(command -v "$candidate")"
        break
    fi
done

if [[ -z "$compatible_python" ]] && command -v uv >/dev/null 2>&1; then
    uv python install 3.13
    compatible_python="$(uv python find 3.13)"
fi

if [[ -z "$compatible_python" ]]; then
    echo "No Kivy-compatible Python was found." >&2
    echo "Install Python 3.13 or run 'pipx install uv', then try again." >&2
    exit 1
fi

echo "Using $($compatible_python --version) at $compatible_python"

if [[ -x .venv/bin/python ]]; then
    current_version="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    case "$current_version" in
        3.11|3.12|3.13) ;;
        *)
            echo "Replacing incompatible Python $current_version environment in .venv"
            "$compatible_python" -m venv --clear .venv
            ;;
    esac
else
    "$compatible_python" -m venv .venv
fi

venv_version="$(.venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$venv_version" in
    3.11|3.12|3.13) ;;
    *)
        echo "Bootstrap created unsupported Python $venv_version" >&2
        exit 1
        ;;
esac

if [[ "$venv_version" == "3.13" && "$(uname -s)" == "Linux" && "$(uname -m)" == "x86_64" ]]; then
    .venv/bin/python -m pip install -r pylock.toml
    .venv/bin/python -m pip install --no-deps -e .
else
    echo "No platform lock for this interpreter; installing exact direct project pins."
    .venv/bin/python -m pip install -e '.[dev]'
fi
.venv/bin/python -m pytest -q

echo
echo "Project Planner is ready. Start it with:"
echo "  .venv/bin/project-planner"
