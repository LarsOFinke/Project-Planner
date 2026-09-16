#!/usr/bin/env bash
set -u

agent_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
report_dir="$agent_root/.agents/debugging/reports"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

report="$(mktemp "$report_dir/diagnostics-$timestamp-XXXXXX.log" 2>/dev/null)" || {
    report_dir="${TMPDIR:-/tmp}/project-planner-diagnostics"
    mkdir -p "$report_dir" || {
        echo "Unable to create a diagnostics directory." >&2
        exit 1
    }
    report="$(mktemp "$report_dir/diagnostics-$timestamp-XXXXXX.log")" || exit 1
    echo "The repository report directory is read-only; using $report_dir." >&2
}

status=0

{
    echo "Project Planner diagnostics"
    echo "generated-utc: $timestamp"
    echo
    bash "$agent_root/.agents/scripts/doctor.sh" || status=$?
    echo
    echo "Validation"
    bash "$agent_root/.agents/scripts/check-all.sh" || status=$?
} >"$report" 2>&1

echo "Diagnostic report: $report"
exit "$status"
