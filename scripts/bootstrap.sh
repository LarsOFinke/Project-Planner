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

install_project_python() {
    local runtime_root=".tools/python/cpython-3.13"
    local runtime_python="$runtime_root/bin/python3.13"
    local metadata_file
    local archive_file
    local asset_file
    local staging_directory
    local asset_url
    local asset_sha256

    if [[ -x "$runtime_python" ]]; then
        printf '%s\n' "$runtime_python"
        return
    fi

    if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
        echo "No compatible system Python was found, and project-local Python bootstrap supports Linux x86_64 only." >&2
        return 1
    fi
    if ! command -v curl >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
        echo "Project-local Python bootstrap requires curl and tar." >&2
        return 1
    fi

    mkdir -p .tools/python
    metadata_file="$(mktemp .tools/python/python-release.XXXXXX.json)"
    archive_file="$(mktemp .tools/python/python-runtime.XXXXXX.tar.gz)"
    asset_file="$(mktemp .tools/python/python-asset.XXXXXX.txt)"
    staging_directory="$(mktemp -d .tools/python/python-runtime.XXXXXX)"
    trap 'rm -f "$metadata_file" "$archive_file" "$asset_file"; rm -rf "$staging_directory"' RETURN

    echo "Downloading a project-local CPython 3.13 runtime" >&2
    if ! curl --fail --location --silent --show-error \
        https://api.github.com/repos/astral-sh/python-build-standalone/releases/latest \
        --output "$metadata_file"; then
        echo "Could not download Python runtime metadata." >&2
        return 1
    fi
    if ! python3 - "$metadata_file" > "$asset_file" <<'PY'
import json
import sys

assets = json.load(open(sys.argv[1], encoding="utf-8"))["assets"]
suffix = "-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
for item in assets:
    if item["name"].startswith("cpython-3.13.") and item["name"].endswith(suffix):
        digest = item.get("digest", "")
        if digest.startswith("sha256:"):
            print(item["browser_download_url"])
            print(digest.removeprefix("sha256:"))
            break
else:
    raise SystemExit("No CPython 3.13 Linux x86_64 runtime was published in the latest release.")
PY
    then
        return 1
    fi
    readarray -t asset < "$asset_file"
    asset_url="${asset[0]:-}"
    asset_sha256="${asset[1]:-}"
    if [[ -z "$asset_url" || -z "$asset_sha256" ]]; then
        echo "Could not resolve a checksummed CPython 3.13 runtime." >&2
        return 1
    fi
    if ! curl --fail --location --silent --show-error "$asset_url" --output "$archive_file"; then
        echo "Could not download the CPython runtime." >&2
        return 1
    fi
    if ! printf '%s  %s\n' "$asset_sha256" "$archive_file" | sha256sum --check --status; then
        echo "Downloaded CPython runtime failed checksum verification." >&2
        return 1
    fi
    if ! tar -xzf "$archive_file" -C "$staging_directory"; then
        echo "Could not extract the CPython runtime." >&2
        return 1
    fi
    if [[ ! -x "$staging_directory/python/bin/python3.13" ]]; then
        echo "Downloaded Python runtime has an unexpected layout." >&2
        return 1
    fi
    rm -rf "$runtime_root"
    mv "$staging_directory/python" "$runtime_root"
    printf '%s\n' "$runtime_python"
}

if [[ -z "$compatible_python" ]]; then
    compatible_python="$(install_project_python)" || exit 1
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
    if [[ -d .venv ]]; then
        echo "Replacing unusable environment in .venv"
        "$compatible_python" -m venv --clear .venv
    else
        "$compatible_python" -m venv .venv
    fi
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
