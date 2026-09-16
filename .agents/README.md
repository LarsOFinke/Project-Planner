# Agent workspace

This directory is the durable, token-efficient handoff layer for AI agents.

Read in this order:

1. `ONBOARDING.md` for the working contract.
2. `PROJECT_CACHE.md` for the compact current state.
3. `ARCHITECTURE.md` only when changing module boundaries or persistence.
4. `debugging/README.md` only when investigating a problem.

Do not recursively read the repository before consulting the cache. The cache identifies the
smallest relevant paths and the canonical validation commands.

Maintenance rules:

- Update `PROJECT_CACHE.md` after meaningful behavior or configuration changes.
- Record durable architectural choices in `DECISIONS.md`.
- Keep generated diagnostic output under `debugging/reports/`; never commit reports.
- Do not place credentials, full environment dumps, database contents, or user images here.
