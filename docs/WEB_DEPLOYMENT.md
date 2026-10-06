# Vue frontend and server deployment

The Vue client lives in `web/` beside the Kivy client. Both use the same FastAPI
`/api/v1` contract and SQLite data. The web workspace follows Kivy's directory,
Overview, Plan Roadmap, Diagram, Workspace, Links, and Admin layout. Editing uses
Vue-controlled HTML forms and confirmation dialogs. Diagram and Workspace have
interactive SVG editors, undo/redo, automatic saves, and saved revisions. The
Kivy client remains available for desktop use.

## Local development

Start the API in one terminal with a compatible Python environment:

```bash
.venv/bin/project-planner-api --host 127.0.0.1 --port 8000
```

Start Vue in another terminal:

```bash
cd web
npm ci
npm run dev
```

Vite proxies `/api` to the localhost API. `VITE_API_PROXY_TARGET` can override
the proxy target (default `http://127.0.0.1:8000`). Leave
`PROJECT_PLANNER_API_TOKEN` unset for this local development arrangement. The
web build and test commands are `npm run build` and `npm test` from `web/`.

## VPS preparation

The target needs Docker Engine with Compose v2, `curl`, `openssl`, and the
Linux-Utilities `vps-gateway` module installed. The SSH deployment account must
be able to run Docker and the gateway commands with noninteractive sudo:
`vps-gateway-init --empty`, `vps-gateway-site-import`, `test`, `grep`, `install`,
and `certbot` for the first HTTPS setup. Review and scope that sudo policy on
the target. The deployer needs a writable absolute `DEPLOY_ROOT`; the example
uses its home directory. The target hostname's DNS must point to the server,
and ports 80 and 443 must be reachable for Certbot.

Copy `.env.deploy.example` to `.env.deploy`, set the target and a dedicated
loopback port, then run `chmod 600 .env.deploy`. Use a unique port for this
project. The example uses `DEPLOY_WEB_AUTH=none`, so the browser needs no
login. Production also requires `DEPLOY_TLS_EMAIL` for HTTPS. To require a
login, use `DEPLOY_WEB_AUTH=basic` with a username and a strong password; only
its salted hash is transferred. The API bearer token is generated on the server,
stays in `shared/runtime.env` and `shared/api.env`, and is injected by the
internal web proxy. It is never built into browser JavaScript.

```bash
./deployment.sh
# or: ./deployment.sh --config /path/to/private-profile
```

The script runs `npm ci`, builds Vue, packages the backend and deployment files,
checks the archive hash on the target, builds Compose images, and waits for the
loopback API health endpoint. It uses `vps-gateway-init --empty` if the gateway
core is absent, imports the site through `vps-gateway-site-import`, and asks
Certbot to install HTTPS on first registration when `DEPLOY_TLS_EMAIL` is set.
Existing production gateway sites are preserved, including their Certbot edits.
An existing test site is replaced so its authentication mode can change. A site
that points to another port stops deployment for manual review.
To change authentication on an existing production site, review its TLS
configuration and gateway route manually before rerunning deployment.

The server layout is:

```text
DEPLOY_ROOT/
  current -> releases/<id>
  releases/<id>/
  shared/runtime.env, shared/api.env
  shared/data/                 # SQLite and managed images
  shared/backups/              # API backup before each update
```

The web container binds only `127.0.0.1:DEPLOY_WEB_PORT`; the API has no host
port. VPS-Gateway routes the public hostname to this loopback port. Gateway
HTTP Basic Auth can be enabled for the app and API. New installations create a
private API bearer token. Updates reuse it and the persistent data directory.
A failed health gate restores the previous Compose release. Database migrations
may change the shared database, so inspect compatibility before deploying a
schema change; the pre-update archive is retained for recovery.

The public site exposes backup import/export endpoints. With
`DEPLOY_WEB_AUTH=none`, anyone who can reach the hostname can use them. Keep
network access scoped to your intended users. If Basic Auth is enabled, keep
the profile password private and rotate it if exposed. Complete the first TLS
issuance before using a public site.

For an isolated `.test` hostname on a trusted network, set `DEPLOY_TARGET=test`,
`DEPLOY_WEB_AUTH=none`, and leave `DEPLOY_TLS_EMAIL` empty. No login or password
is needed to use the site. The same no-login setting works for a production
hostname, where HTTPS is still required.
