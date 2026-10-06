# Repository spring-cleaning standard

Use this guide for periodic repository-wide quality audits. It complements `ONBOARDING.md` and
`ARCHITECTURE.md`; it does not replace feature-specific testing.

## Canonical structure

```text
frontend/
└── src/project_planner_frontend/   # API-mirrored replaceable Kivy client
src/project_planner/
├── api/                            # FastAPI composition and feature API modules
│   └── <feature>/
│       ├── <Feature>Controller.py  # route-owning controller at module root
│       └── dtos/                   # transport/read contracts
├── config/                         # packaged defaults
├── modules/                        # feature-first business modules
│   └── <feature>/
│       ├── entities/               # domain entities, enums, value types
│       ├── protocols/              # replaceable dependency contracts
│       ├── services/               # use cases, queries, workflows
│       ├── repositories/           # protocol implementations and persistence access
│       ├── mappers/                # entity/ORM translation where it reduces repository load
│       └── gateways/               # explicit external/system boundaries when truly needed
└── shared/                         # database, settings, narrow utilities
```

Business layer directories are created per module only when needed. Transport DTOs belong to the
matching API feature rather than business modules. Do not recreate global `entities`, `services`,
`protocols`, `repositories`, or `mappers` buckets, and do not introduce a generic `utils` dumping
ground. An empty `.codex` directory may be supplied by the execution environment and is not part
of the application architecture.

## Required quality invariants

- One source class per file, using the exact PascalCase class name as its filename.
- Dependencies follow the rules in `ARCHITECTURE.md` and point inward within each feature module.
- Backend code never imports Kivy or the frontend package.
- Frontend code never imports SQLAlchemy, database infrastructure, or concrete repositories.
- Feature controllers own their routes; there is no parallel router layer or aggregate container.
- Controller route setup is grouped into resource-specific helper methods; `_register_routes()` is
  only the concise feature route index.
- API features keep controllers at their module root and DTOs in their local `dtos/` directory.
- Agile, Custom, phases, and Waterfall remain one backend `planning` module.
- Frontend feature roots mirror the Project, Planning, Collaboration, Artifact, and System
  controllers and keep their clients beside their views.
- Persisted schema, export, and artifact changes remain backward-compatible and versioned.
- Migrations and user-managed database/data directories are never removed during cleanup.
- UI work remains usable at the 100% Full-HD and 200% laptop profiles.

The AST-based architecture tests in `tests/test_structure.py` enforce import boundaries, direct
import cycles, and class/file rules across both source roots.

## Cleanup checklist

1. Read `ONBOARDING.md`, `PROJECT_CACHE.md`, and `ARCHITECTURE.md`.
2. Confirm the worktree state; preserve unrelated changes.
3. Run `bash .agents/scripts/doctor.sh`.
4. Find empty or obsolete directories, distinguishing runtime-owned mounts from source folders.
5. Delete only derived caches, bytecode, editable metadata, and build output inside the repository.
6. Search for stale names, dead compatibility paths, documentation drift, and cross-layer imports.
7. Review large modules for mixed responsibilities before splitting; length alone is insufficient.
8. Verify migrations, seeds, configuration examples, package discovery, and documented versions.
9. Run the complete validation set and a real Kivy event-loop smoke test when UI code changed.

## Canonical validation

```bash
bash .agents/scripts/doctor.sh
npm --prefix web ci
make validate
.venv/bin/python -m pip check
git diff --check
```

`check-all.sh` runs Ruff linting/formatting, Python and Vue tests, the Vue build,
compilation across backend and Kivy roots, shell syntax checks, Kivy event-loop
smokes, and the strict Python line-length guard.

## Safe generated-data cleanup

The following derived data may be removed when no process uses it: `__pycache__/`, `*.pyc`,
`.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, and local `build/` or `dist/` output. Never
remove `.venv`, configured databases, managed assets, migrations, or user diagnostics as cleanup.

## 2026-09-18 baseline audit

- Replaced the former horizontal `core` layers with feature-owned module layers.
- Separated the Kivy client into its own root source package and retained a backend API boundary.
- Added dependency-boundary/import-cycle enforcement and complete formatting verification.
- Confirmed class/file invariants, migration continuity, dependencies, configuration, and scripts.
- Consolidated planning strategies and mirrored API feature boundaries in the Kivy client.

## 2026-09-19 follow-up audit

- Removed the superseded database-transfer CLI package and entry point; Admin is the supported UI.
- Consolidated category and parent changes behind one cycle-safe, transactional subtree move path.
- Removed generated caches and checked for stale CLI/category-assignment references and empty source
  directories.
- Reconfirmed dependency boundaries, class/file invariants, documentation, and both UI scales.

## 2026-09-23 follow-up audit

- Tracked source and documentation contain no developer-home paths, contact addresses, or
  machine-specific absolute paths. Published Git authorship and the remote account identify a
  person; anonymizing that metadata would require a separate history/hosting decision.
- Kept the feature-first module boundaries. Large planning and project UI files still have one
  coherent feature owner; file length alone does not justify a breaking module split.
- Added configurable HTTP/backup timeouts and an unpacked-backup size limit to defaults,
  example cfg, and environment loading; checked dependency health and empty source directories.
- Strengthened backup import with bounded extraction, duplicate-record rejection, atomic file
  publication, and fault-path rollback tests. Normal exceptions roll back; a process or power
  failure between file publication and database commit still needs a future recovery journal.
  Remote HTTP ingress also needs an upload-body limit before multipart buffering.
- Updated the roadmap, database guide, architecture map, cache, and known-issues note to match
  current behavior.

## 2026-10-06 follow-up audit

- Confirmed that tracked files contain no generated caches, build products, private deployment
  profiles, machine-specific server addresses, or empty source directories.
- Added Vue tests/build and deployment shell syntax to the full local validation gate; CI now
  provisions its own Python virtual environment and Node dependencies for that gate.
- Made first artifact creation safe when concurrent requests both read an absent artifact, with a
  regression test using separate SQLite sessions.
- Reformatted the Vue stylesheet for review without changing its compiled CSS, and corrected
  backup-recovery notes that predated the durable import journal.
