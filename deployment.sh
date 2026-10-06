#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
profile="${PROJECT_PLANNER_DEPLOY_CONFIG:-$root_dir/.env.deploy}"
if [[ "${1:-}" == --help ]]; then
  echo "Usage: ./deployment.sh [--config FILE]"
  exit 0
fi
if [[ "${1:-}" == --config && -n "${2:-}" && $# -eq 2 ]]; then
  profile="$2"
elif (($#)); then
  echo "Usage: ./deployment.sh [--config FILE]" >&2
  exit 2
fi
[[ -f "$profile" && ! -L "$profile" ]] || { echo "Missing regular deployment profile: $profile" >&2; exit 1; }
[[ "$(stat -c %a "$profile")" == 600 ]] || { echo "Set profile permissions to 600: $profile" >&2; exit 1; }
# shellcheck disable=SC1090
source "$profile"
: "${DEPLOY_HOST:?Set DEPLOY_HOST in the profile}"
: "${DEPLOY_USER:?Set DEPLOY_USER in the profile}"
: "${DEPLOY_HOSTNAME:?Set DEPLOY_HOSTNAME in the profile}"
: "${DEPLOY_ROOT:?Set DEPLOY_ROOT in the profile}"
: "${DEPLOY_WEB_PORT:?Set DEPLOY_WEB_PORT in the profile}"
DEPLOY_SSH_PORT="${DEPLOY_SSH_PORT:-22}"
DEPLOY_IDENTITY_FILE="${DEPLOY_IDENTITY_FILE:-}"
DEPLOY_TARGET="${DEPLOY_TARGET:-production}"
DEPLOY_WEB_AUTH="${DEPLOY_WEB_AUTH:-basic}"
DEPLOY_TLS_EMAIL="${DEPLOY_TLS_EMAIL:-}"
[[ "$DEPLOY_TARGET" == test || "$DEPLOY_TARGET" == production ]] || { echo 'DEPLOY_TARGET must be test or production.' >&2; exit 2; }
[[ "$DEPLOY_WEB_AUTH" == basic || "$DEPLOY_WEB_AUTH" == none ]] || { echo 'DEPLOY_WEB_AUTH must be basic or none.' >&2; exit 2; }
if [[ "$DEPLOY_WEB_AUTH" == basic ]]; then
  : "${DEPLOY_WEB_USERNAME:?Set DEPLOY_WEB_USERNAME in the profile}"
  : "${DEPLOY_WEB_PASSWORD:?Set DEPLOY_WEB_PASSWORD in the profile}"
fi
if [[ "$DEPLOY_TARGET" == production ]]; then
  : "${DEPLOY_TLS_EMAIL:?Set DEPLOY_TLS_EMAIL for HTTPS issuance}"
fi
[[ "$DEPLOY_HOST" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*$ && "$DEPLOY_USER" =~ ^[a-z_][a-z0-9_-]*$ ]] || { echo 'Invalid SSH host or user.' >&2; exit 2; }
[[ "$DEPLOY_HOSTNAME" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]] || { echo 'Invalid public hostname.' >&2; exit 2; }
if [[ "$DEPLOY_WEB_AUTH" == basic ]]; then
  [[ "$DEPLOY_WEB_USERNAME" =~ ^[a-zA-Z0-9_-]+$ && ${#DEPLOY_WEB_PASSWORD} -ge 16 ]] || { echo 'Use a simple username and a password of at least 16 characters.' >&2; exit 2; }
fi
[[ "$DEPLOY_ROOT" =~ ^/[a-zA-Z0-9_./-]+$ && "$DEPLOY_ROOT" != / && "$DEPLOY_ROOT" != *..* ]] || { echo 'DEPLOY_ROOT must be a simple absolute path.' >&2; exit 2; }
for port in "$DEPLOY_SSH_PORT" "$DEPLOY_WEB_PORT"; do
  [[ "$port" =~ ^[0-9]+$ && "$port" -ge 1 && "$port" -le 65535 ]] || { echo "Invalid port: $port" >&2; exit 2; }
done
[[ -z "$DEPLOY_TLS_EMAIL" || "$DEPLOY_TLS_EMAIL" =~ ^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] || { echo 'Invalid TLS email.' >&2; exit 2; }
ssh_args=(-F /dev/null -p "$DEPLOY_SSH_PORT" -o BatchMode=yes)
scp_args=(-F /dev/null -P "$DEPLOY_SSH_PORT" -o BatchMode=yes)
if [[ -n "$DEPLOY_IDENTITY_FILE" ]]; then
  [[ -f "$DEPLOY_IDENTITY_FILE" ]] || { echo "Missing SSH identity: $DEPLOY_IDENTITY_FILE" >&2; exit 2; }
  ssh_args+=(-i "$DEPLOY_IDENTITY_FILE")
  scp_args+=(-i "$DEPLOY_IDENTITY_FILE")
fi
target="$DEPLOY_USER@$DEPLOY_HOST"
release_id="$(date -u +%Y%m%d%H%M%S)-$(git -C "$root_dir" rev-parse --short HEAD)"
staging="$(mktemp -d)"
trap 'rm -rf -- "$staging"' EXIT

echo '[deploy] Building Vue frontend'
npm --prefix "$root_dir/web" ci
npm --prefix "$root_dir/web" run build
tar -C "$root_dir" -czf "$staging/release.tar.gz" src web/dist deploy
sha256sum "$staging/release.tar.gz" | cut -d ' ' -f 1 > "$staging/release.sha256"
if [[ "$DEPLOY_WEB_AUTH" == basic ]]; then
  printf '%s:%s\n' "$DEPLOY_WEB_USERNAME" "$(printf '%s' "$DEPLOY_WEB_PASSWORD" | openssl passwd -6 -stdin)" > "$staging/web.htpasswd"
fi

echo "[deploy] Transferring release $release_id to $target"
ssh "${ssh_args[@]}" "$target" "mkdir -p '$DEPLOY_ROOT/incoming/$release_id'"
scp "${scp_args[@]}" "$staging/release.tar.gz" "$staging/release.sha256" "$target:$DEPLOY_ROOT/incoming/$release_id/"
if [[ "$DEPLOY_WEB_AUTH" == basic ]]; then
  scp "${scp_args[@]}" "$staging/web.htpasswd" "$target:$DEPLOY_ROOT/incoming/$release_id/"
fi
ssh "${ssh_args[@]}" "$target" \
  "bash -s -- '$DEPLOY_ROOT' '$release_id' '$DEPLOY_HOSTNAME' '$DEPLOY_WEB_PORT' '$DEPLOY_TLS_EMAIL' '$DEPLOY_TARGET' '$DEPLOY_WEB_AUTH'" \
  < "$root_dir/deploy/activate.sh"
