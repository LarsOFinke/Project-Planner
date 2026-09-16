# Project cache

Last refreshed: 2026-09-16

## Hot context

- Product: local-first desktop project planner, prototype `0.1.0`.
- Runtime: Python `>=3.11,<3.14`; tested with Python 3.13.15 and Kivy 2.3.1.
- Setup: `make setup`; run: `.venv/bin/project-planner` or `make run`.
- Quality: `make test`, `make lint`, or `bash .agents/scripts/check-all.sh`.
- Current suite: 10 tests.
- Entry point: `project_planner.frontend.main:main`.
- Database: SQLite, default `~/.project_planner/project_planner.sqlite3`.
- Managed data: default `~/.project_planner/data`.
- UI scale: default `2.00`.

## Implemented workflows

- hierarchical project browser with project status;
- overview metadata, timestamps, parent project, and planning method;
- editable Waterfall, Agile, and Custom phases;
- project links and backlinks;
- draggable node/edge diagram editor;
- freehand workspace;
- movable, rotatable, scalable rectangle/ellipse/line/arrow objects;
- imported PNG/JPEG/GIF/BMP/WebP images copied into per-project managed storage;
- workspace toolboxes: Shapes, Media, Transform, Manage;
- local artifact autosave with JSON payloads.

## Persistence facts

- Relational schema: `core/infrastructure/database/schema.py`.
- Projects, phases, links, and artifacts cascade from project deletion as defined by SQLite.
- Diagram JSON version: `1`.
- Workspace JSON version: `3`.
- Workspace JSON stores strokes, shapes, images, position, size, and rotation.
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

## High-value paths

- Composition: `src/project_planner/core/bootstrap/container_builder.py`
- Settings: `src/project_planner/core/configuration/`
- Models: `src/project_planner/core/domain/`
- Use cases: `src/project_planner/core/application/`
- SQLite adapters: `src/project_planner/core/infrastructure/`
- UI shell: `src/project_planner/frontend/shell/project_planner_root.py`
- Theme: `src/project_planner/frontend/shared/theme.py`
- Workspace: `src/project_planner/frontend/workspace/`
- Diagram: `src/project_planner/frontend/diagram/`
- Tests: `tests/`

## Known environment behavior

- System `python3` is 3.14.4. Running `python3 -m venv .venv` recreates an incompatible venv.
  Use `make setup`; it locates Python 3.11–3.13 and replaces incompatible environments.
- Missing `xclip`/`xsel` produces a scary but non-fatal Kivy Cutbuffer warning. SDL2 clipboard
  remains available. Distinguish that warning from the traceback that terminates the app.
- Kivy schedules some layout work after `build()`. Always exercise the event loop for UI work.

## Cache refresh triggers

Update this file when any of these change: Python/Kivy support, commands, entrypoints, module
boundaries, schema, artifact JSON versions, configuration keys, default paths, tests, or known
runtime warnings.
