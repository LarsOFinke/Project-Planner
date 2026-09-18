#!/usr/bin/env bash
set -euo pipefail

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$agent_root"

if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "Kivy smoke test requires DISPLAY/WAYLAND_DISPLAY or xvfb-run" >&2
    exit 1
fi

.venv/bin/python .agents/scripts/kivy-event-loop-smoke.py --scale 2.0 --width 1280 --height 800
.venv/bin/python .agents/scripts/kivy-event-loop-smoke.py --scale 1.0 --width 1920 --height 1080
echo "Kivy event-loop smoke tests passed at 200% and 100%."
