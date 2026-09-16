# Project cache

Last refreshed: 2026-09-17

## Hot context

- Product: local-first desktop project planner, prototype `0.1.0`.
- Runtime: Python `>=3.11,<3.14`; tested with Python 3.13.15 and Kivy 2.3.1.
- Setup: `make setup`; run: `.venv/bin/project-planner` or `make run`.
- Quality: `make test`, `make lint`, or `bash .agents/scripts/check-all.sh`.
- Current suite: 25 tests.
- Entry point: `project_planner.frontend.main:main`.
- Database: SQLite, default `~/.project_planner/project_planner.sqlite3`.
- Managed data: default `~/.project_planner/data`.
- UI scale: persistent top-right dropdown from 5%–500%; cfg/env accepts `auto` or `0.05`–`5.00`.
- Class modules: exact PascalCase class filenames; non-class helper modules remain snake_case.

## Implemented workflows

- hierarchical project browser with project status;
- overview metadata, timestamps, parent project, and planning method;
- editable Waterfall, Agile, and Custom phase objects with descriptions, statuses, and timestamps;
- project links and backlinks;
- draggable node/edge diagram editor;
- freehand workspace;
- movable, rotatable, scalable rectangle/ellipse/line/arrow objects;
- imported PNG/JPEG/GIF/BMP/WebP images copied into per-project managed storage;
- shared categorized-toolbox component;
- content-sized text and image dialogs with responsive bounds and keyboard submission;
- wrapping title/caption primitives and density-aware, horizontally scrollable planning tabs;
- workspace toolboxes: Shapes, Media, Colors, Transform, Manage;
- diagram toolboxes: Nodes, Relations, Manage;
- local artifact autosave with JSON payloads.
- project workflow orchestration for project/phase lifecycle operations;
- query projections for project trees, parent choices, and duplicate-title-safe selectors;
- resolved link projections with incoming/outgoing direction;
- typed diagram/workspace documents with version-aware codecs;
- narrow service injection into feature panels.

## Persistence facts

- Relational schema: `core/infrastructure/database/schema.py`.
- Projects, phases, links, and artifacts cascade from project deletion as defined by SQLite.
- Diagram JSON version: `1`.
- Workspace JSON version: `4`.
- Workspace JSON stores colored strokes and shapes plus images, position, size, and rotation.
- Phase rows persist description, status, created timestamp, and updated timestamp; startup migrates
  older phase tables in place with `planned` status and preserved rows.
- Artifact codecs reject unknown future versions and migrate supported older payloads when saved.
- Deleting an image object does not delete its managed source file.
- Image location: `<data_directory>/projects/<project-id>/images/<uuid>.<ext>`.

## Configuration precedence

1. packaged `src/project_planner/config/default.cfg`;
2. `./project_planner.cfg`;
3. `~/.config/project_planner/config.cfg`;
4. environment variables.

Important overrides:

- `PROJECT_PLANNER_DB`
- `PROJECT_PLANNER_DATA_DIR`
- `PROJECT_PLANNER_WINDOW_WIDTH`
- `PROJECT_PLANNER_WINDOW_HEIGHT`
- `PROJECT_PLANNER_AUTOSAVE_SECONDS`
- `PROJECT_PLANNER_UI_SCALE`

`PROJECT_PLANNER_UI_SCALE` accepts `auto` or a numeric value from `0.05` through `5.00`.
Dropdown choices are saved to `~/.config/project_planner/config.cfg`; environment overrides win.

## High-value paths

- Composition: `src/project_planner/core/bootstrap/container_builder.py`
- Workflows/queries: `src/project_planner/core/application/projects/`
- Artifact documents/codecs: `src/project_planner/core/application/artifacts/`
- Settings: `src/project_planner/core/configuration/`
- Models: `src/project_planner/core/domain/`
- Use cases: `src/project_planner/core/application/`
- SQLite adapters: `src/project_planner/core/infrastructure/`
- UI shell: `src/project_planner/frontend/shell/ProjectPlannerRoot.py`
- Theme: `src/project_planner/frontend/shared/theme.py`
- Workspace: `src/project_planner/frontend/workspace/`
- Diagram: `src/project_planner/frontend/diagram/`
- Tests: `tests/`

## Known environment behavior

- System `python3` is 3.14.4. Running `python3 -m venv .venv` recreates an incompatible venv.
  Use `make setup`; it locates Python 3.11–3.13 and replaces incompatible environments.
- On newer-Python target systems, install the managed interpreter bootstrap with
  `pipx install uv`; `make setup` then installs/finds Python 3.13 through `uv`.
- Missing `xclip`/`xsel` produces a scary but non-fatal Kivy Cutbuffer warning. SDL2 clipboard
  remains available. Distinguish that warning from the traceback that terminates the app.
- Kivy schedules some layout work after `build()`. Always exercise the event loop for UI work.

## Cache refresh triggers

Update this file when any of these change: Python/Kivy support, commands, entrypoints, module
boundaries, schema, artifact JSON versions, configuration keys, default paths, tests, or known
runtime warnings.
