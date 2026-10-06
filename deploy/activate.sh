#!/usr/bin/env bash
set -euo pipefail

root="$1"; release_id="$2"; hostname="$3"; web_port="$4"; tls_email="$5"; target="$6"; web_auth="$7"
incoming="$root/incoming/$release_id"
release="$root/releases/$release_id"
shared="$root/shared"
expected="$(cat "$incoming/release.sha256")"
actual="$(sha256sum "$incoming/release.tar.gz" | cut -d ' ' -f 1)"
[[ "$actual" == "$expected" ]] || { echo '[deploy] Release checksum mismatch.' >&2; exit 1; }
[[ ! -e "$release" ]] || { echo '[deploy] Release already exists.' >&2; exit 1; }
mkdir -p "$release" "$shared/data" "$shared/backups"
tar -xzf "$incoming/release.tar.gz" -C "$release"
chmod 700 "$shared"

if [[ ! -f "$shared/runtime.env" ]]; then
  command -v openssl >/dev/null || { echo '[deploy] openssl is required to create the API token.' >&2; exit 1; }
  token="$(openssl rand -hex 32)"
  umask 077
  printf 'PROJECT_PLANNER_API_TOKEN=%s\nWEB_PORT=%s\n' "$token" "$web_port" > "$shared/runtime.env"
  printf 'PROJECT_PLANNER_API_TOKEN=%s\nPROJECT_PLANNER_DB=/data/project_planner.sqlite3\nPROJECT_PLANNER_DATA_DIR=/data/files\n' "$token" > "$shared/api.env"
fi
chmod 600 "$shared/runtime.env" "$shared/api.env"
set -a
# shellcheck disable=SC1091
source "$shared/runtime.env"
set +a
[[ "$WEB_PORT" == "$web_port" ]] || { echo '[deploy] WEB_PORT differs from existing runtime configuration.' >&2; exit 1; }

previous=''
if [[ -L "$root/current" ]]; then previous="$(readlink -f "$root/current")"; fi
if [[ -f "$shared/data/project_planner.sqlite3" ]]; then
  backup="$shared/backups/pre-$release_id.tar.gz"
  if ! curl -fsS "http://127.0.0.1:$web_port/api/v1/backup/export" -o "$backup"; then
    rm -f -- "$backup"
    echo '[deploy] Live backup failed; release was not activated.' >&2
    exit 1
  fi
  echo "[deploy] Data backup: $backup"
fi
docker_command=(docker)
if ! docker info >/dev/null 2>&1; then docker_command=(sudo -n docker); fi
compose() { "${docker_command[@]}" compose --env-file "$shared/runtime.env" -f "$1/deploy/compose.yml" "${@:2}"; }
rollback() {
  if [[ -n "$previous" && -f "$previous/deploy/compose.yml" ]]; then
    compose "$previous" up -d --build --remove-orphans
    ln -sfn "$previous" "$root/current"
    echo '[deploy] Previous application release restored.' >&2
  else
    compose "$release" down || true
  fi
}
echo '[deploy] Building and starting containers'
if ! compose "$release" build || ! compose "$release" up -d --remove-orphans; then rollback; exit 1; fi
healthy=false
for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:$web_port/api/v1/health" >/dev/null; then healthy=true; break; fi
  sleep 2
done
if [[ "$healthy" != true ]]; then rollback; echo '[deploy] Application health check failed.' >&2; exit 1; fi

echo '[deploy] Registering VPS-Gateway site'
if ! command -v vps-gateway-site-import >/dev/null; then
  rollback; echo '[deploy] Install the Linux-Utilities vps-gateway module first.' >&2; exit 1
fi
if ! sudo -n test -f /etc/nginx/conf.d/vps-gateway.conf; then
  if ! sudo -n vps-gateway-init --empty; then rollback; exit 1; fi
fi
site="/etc/nginx/sites-available/$hostname.conf"
if [[ "$web_auth" == basic ]]; then
  sudo -n install -o root -g www-data -m 0640 "$incoming/web.htpasswd" "/etc/nginx/project-planner-$hostname.htpasswd"
fi
rendered="$incoming/site.conf"
sed -e "s/__HOSTNAME__/$hostname/g" -e "s/__PORT__/$web_port/g" "$release/deploy/gateway-site.conf.template" > "$rendered"
if [[ "$web_auth" == none ]]; then
  sed -i '/^[[:space:]]*auth_basic /d; /^[[:space:]]*auth_basic_user_file /d' "$rendered"
fi
if sudo -n test -f "$site"; then
  if ! sudo -n grep -Fq "proxy_pass http://127.0.0.1:$web_port;" "$site"; then
    rollback; echo "[deploy] Existing gateway site $site uses a different backend. Review it manually." >&2; exit 1
  fi
  if [[ "$target" == test ]]; then
    if ! sudo -n vps-gateway-site-import --host "$hostname" --file "$rendered" --replace; then rollback; exit 1; fi
  elif [[ "$web_auth" == basic ]] && ! sudo -n grep -Fq "project-planner-$hostname.htpasswd" "$site"; then
    rollback; echo '[deploy] Existing production site lacks expected authentication.' >&2; exit 1
  elif [[ "$web_auth" == none ]] && sudo -n grep -Eq '^[[:space:]]*auth_basic[[:space:]]+' "$site"; then
    rollback; echo '[deploy] Existing production site still has Basic Auth. Review its TLS config before changing authentication.' >&2; exit 1
  fi
else
  if ! sudo -n vps-gateway-site-import --host "$hostname" --file "$rendered"; then rollback; exit 1; fi
fi
if [[ "$target" == production ]] && ! sudo -n grep -Eq 'listen[[:space:]]+([^;]*:)?443' "$site"; then
  if ! sudo -n certbot --nginx -d "$hostname" --redirect --non-interactive --agree-tos -m "$tls_email"; then
    echo '[deploy] HTTP site is active; TLS issuance failed. Check DNS and retry Certbot.' >&2
    rollback; exit 1
  fi
fi
ln -sfn "$release" "$root/current"
echo "[deploy] Active release: $release"
