#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
[[ "$(uname -s)" == Linux ]] || { echo 'AppImage builds require Linux.' >&2; exit 1; }
[[ "$(uname -m)" == x86_64 ]] || { echo 'AppImage builds currently require x86_64.' >&2; exit 1; }

python_bin="${PYTHON_BIN:-.venv/bin/python}"
"$python_bin" -c 'import sys; sys.exit(not ((3, 11) <= sys.version_info[:2] < (3, 14)))' || {
    echo 'Python 3.11–3.13 is required to build the AppImage.' >&2
    exit 1
}

mkdir -p build/logs dist/linux
run_logged() {
    local name="$1"
    shift
    local log="$PWD/build/logs/$name.log"
    echo "Running $name (details: $log)"
    if "$@" >"$log" 2>&1; then
        tail -n 8 "$log"
    else
        echo "$name failed; last 80 log lines:" >&2
        tail -n 80 "$log" >&2
        return 1
    fi
}

build_python="$PWD/.build-venv/bin/python"
if [[ ! -x "$build_python" ]] || ! "$build_python" -c \
    'import sys; sys.exit(not ((3, 11) <= sys.version_info[:2] < (3, 14)))'; then
    "$python_bin" -m venv --clear .build-venv
fi

run_logged wheel env PYTHON_BIN="$build_python" bash scripts/build-wheel.sh
wheel="$($build_python scripts/wheel_path.py)"
run_logged install "$build_python" -m pip install --upgrade "$wheel" 'pyinstaller==6.22.3'
run_logged reinstall-wheel "$build_python" -m pip install --force-reinstall --no-deps "$wheel"
run_logged pyinstaller "$build_python" -m PyInstaller --log-level=WARN \
    --clean --noconfirm --onefile --windowed \
    --name ProjectPlanner \
    --collect-submodules sqlalchemy.dialects.sqlite \
    --add-data "$PWD/src/project_planner/config/default.cfg:project_planner/config" \
    --add-data "$PWD/src/project_planner/shared/database/migrations:project_planner/shared/database/migrations" \
    --distpath dist/linux --workpath build/pyinstaller --specpath build \
    scripts/frozen_entry.py

tool="${APPIMAGETOOL:-$PWD/build/tools/appimagetool-x86_64.AppImage}"
if [[ -z "${APPIMAGETOOL:-}" && ! -f "$tool" ]]; then
    mkdir -p build/tools
    curl --fail --location --retry 3 --silent --show-error \
        https://github.com/AppImage/appimagetool/releases/download/1.9.1/appimagetool-x86_64.AppImage \
        --output "$tool.partial"
    printf '%s  %s\n' \
        'ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0' \
        "$tool.partial" | sha256sum --check --status
    mv "$tool.partial" "$tool"
fi
[[ -f "$tool" ]] || { echo "appimagetool not found: $tool" >&2; exit 1; }
[[ -n "${APPIMAGETOOL:-}" ]] || chmod +x "$tool"

appdir="$PWD/build/ProjectPlanner.AppDir"
mkdir -p "$appdir/usr/bin"
cp dist/linux/ProjectPlanner "$appdir/usr/bin/ProjectPlanner"
cp packaging/linux/ProjectPlanner.desktop "$appdir/ProjectPlanner.desktop"
cp packaging/linux/ProjectPlanner.svg "$appdir/ProjectPlanner.svg"
cp packaging/linux/AppRun "$appdir/AppRun"
chmod +x "$appdir/AppRun"

runtime="$PWD/build/tools/runtime-x86_64"
if [[ -n "${APPIMAGE_RUNTIME:-}" ]]; then
    runtime="$APPIMAGE_RUNTIME"
    [[ -f "$runtime" ]] || { echo "AppImage runtime not found: $runtime" >&2; exit 1; }
else
    mkdir -p build/tools
    offset="$(APPIMAGE_EXTRACT_AND_RUN=1 "$tool" --appimage-offset)"
    [[ "$offset" =~ ^[0-9]+$ && "$offset" -gt 0 ]] || {
        echo "Could not read the embedded AppImage runtime from $tool" >&2
        exit 1
    }
    head -c "$offset" "$tool" > "$runtime"
fi

output="$PWD/dist/linux/ProjectPlanner-x86_64.AppImage"
run_logged appimagetool env ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$tool" --no-appstream \
    --runtime-file "$runtime" "$appdir" "$output"
chmod +x "$output"

mkdir -p build/smoke-data
XDG_DATA_HOME="$PWD/build/smoke-data" KIVY_NO_FILELOG=1 \
    APPIMAGE_EXTRACT_AND_RUN=1 "$output" --check-imports
XDG_DATA_HOME="$PWD/build/smoke-data" KIVY_NO_FILELOG=1 \
    APPIMAGE_EXTRACT_AND_RUN=1 "$output" --smoke-ui
echo "Built $output"
