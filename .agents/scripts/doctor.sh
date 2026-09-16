#!/usr/bin/env bash
set -u

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$agent_root"

echo "Project Planner doctor"
echo "workspace: $agent_root"
echo "system-python: $(python3 --version 2>&1 || echo unavailable)"

if [[ -x .venv/bin/python ]]; then
    echo "venv-python: $(.venv/bin/python --version 2>&1)"
    .venv/bin/python -c 'import sys; print("executable:", sys.executable)'
    .venv/bin/python -c 'import sqlite3; print("sqlite:", sqlite3.sqlite_version)'
    .venv/bin/python -c 'import kivy; print("kivy:", kivy.__version__)' 2>/dev/null \
        || echo "kivy: unavailable"
else
    echo "venv-python: missing (run make setup)"
fi
echo "display: ${DISPLAY:-unset}"
echo "wayland-display: ${WAYLAND_DISPLAY:-unset}"
echo "xclip: $(command -v xclip || echo unavailable)"
echo "xsel: $(command -v xsel || echo unavailable)"
echo "database-override: ${PROJECT_PLANNER_DB:-unset}"
echo "data-dir-override: ${PROJECT_PLANNER_DATA_DIR:-unset}"
echo "ui-scale-override: ${PROJECT_PLANNER_UI_SCALE:-unset}"

if [[ -x .venv/bin/python ]]; then
    .venv/bin/python - <<'PY'
from project_planner.core.configuration.settings_loader import load_settings

settings = load_settings()
print("resolved-database:", settings.database_path)
print("resolved-data-directory:", settings.data_directory)
print("resolved-window:", f"{settings.window_width}x{settings.window_height}")
print("resolved-ui-scale:", settings.ui_scale)
PY
fi
