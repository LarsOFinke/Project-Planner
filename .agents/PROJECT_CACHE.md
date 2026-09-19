# Project cache

Last refreshed: 2026-09-19

## Hot context

- Product: local-first desktop project planner, prototype `0.1.0`.
- Runtime: Python `>=3.11,<3.14`; tested with Python 3.13.15 and Kivy 2.3.1.
- Setup: `make setup`; run: `.venv/bin/project-planner` or `make run`.
- Quality: `make test`, `make lint`, or `make validate`.
- Current suite: 84 tests plus automated Kivy event-loop smoke runs at 200% and 100%.
- Entry point: `project_planner_frontend.main:main`.
- HTTP API entry point: `project-planner-api`; versioned resources live below `/api/v1`.
- Desktop transport: embedded Uvicorn on an ephemeral localhost port; optional remote API URL.
- Remote API: optional bearer token; standalone non-loopback binding requires one.
- Database: SQLAlchemy ORM with Alembic migrations; SQLite default at
  `~/.project_planner/project_planner.sqlite3`.
- Managed data: default `~/.project_planner/data`.
- UI scale: persistent top-right dropdown from 5%–500%; cfg/env accepts `auto` or `0.05`–`5.00`.
- Window: native fullscreen by default; cfg/env can opt into windowed mode.
- Fullscreen exit: persistent bottom-left Exit button; shutdown flushes editor autosaves.
- Window mode: persistent top-right Windowed/Fullscreen toggle beside the scale selector.
- Diagnostics: unexpected Kivy event errors are recovered, stored in SQLite, and visible in Admin.
- Class modules: exact PascalCase class filenames; non-class helper modules remain snake_case.
- Architecture boundaries are enforced by AST tests; the cleanup standard is documented in
  `.agents/REPOSITORY_SPRING_CLEANING.md`.
- Agile, Custom, phase, and Waterfall backend code is consolidated in `modules/planning`.
- Frontend `projects`, `planning`, `collaboration`, `artifacts`, and `system` boundaries mirror
  the five API feature controllers and colocate their clients and views.
- API feature modules keep their controller at the module root and transport DTOs in `dtos/`;
  business modules contain no transport DTO directories.
- Visual system: shared low-glare palette, rounded controls, bordered surfaces, section hierarchy,
  and a collapsible project directory with compact scale-aware icon controls and branch guides.
- Project switching reuses the loaded directory projection and loads only the visible feature tab;
  each tab is fetched once per selected project until its data is invalidated.

## Implemented workflows

- category-based project directory with add/rename/remove controls, child hierarchy, and project
  status;
- category rows own their add-project action, row-level gear menus hold Rename/Add child/Archive,
  and deletable category/project rows expose compact red bin controls on the relevant item;
- categories and projects with descendants have independent disclosure controls; selecting a
  hidden project through another view automatically expands its category and ancestor chain;
- confirmed project Archive and Delete actions; archive retains data with archived status, while
  delete removes owned planning data and promotes child projects to roots;
- overview metadata, timestamps, parent project, and planning method;
- Agile backlog, multiple planned sprints, completed work, and simple sprint history;
- Roadmap views preserve completed sections in sequence; Agile keeps planned and completed sprints
  in one directory and opens sprint work in separate To Do/In Progress/Done overlay tabs;
- Waterfall phases, tasks, and chronological timeline;
- ordered Custom sections that independently use Free, Agile, or Waterfall structures;
- shared calendar-module service and reusable Date picker across all planning date fields;
- project links and backlinks;
- draggable node/edge diagram editor;
- freehand workspace with explicit Select and Draw interaction modes;
- movable, rotatable, scalable rectangle/ellipse/line/arrow objects;
- imported PNG/JPEG/GIF/BMP/WebP images copied into per-project managed storage;
- shared categorized-toolbox component;
- top-anchored, scrollable editor forms with persistent bottom action rows at every UI scale;
- content-sized text and image dialogs with responsive bounds and keyboard submission;
- wrapping title/caption primitives and density-aware, horizontally scrollable planning tabs;
- workspace toolboxes: Mode, Shapes, Media, Colors, Transform, Manage;
- diagram toolboxes: Nodes, Relations, Manage;
- local artifact autosave with JSON payloads.
- project workflow orchestration for project/phase lifecycle operations;
- query projections for project trees, parent choices, and duplicate-title-safe selectors;
- resolved link projections with incoming/outgoing direction;
- typed diagram/workspace documents with version-aware codecs;
- typed HTTP-client injection into feature panels; backend services never enter the Kivy widget
  tree, and one controller coordinates each FastAPI feature area.
- contextual To-Dos surfaced from Overview, individual phases, and Links; Diagram and Workspace
  each expose a dedicated nested To-Dos tab beside their Canvas tab;
- project relationships managed from Overview, with Links reserved for web URLs and local files;
- Links separates Web URLs, Local Files, and contextual To-Dos into dedicated nested tabs while
  retaining one normalized resource-link persistence model;
- save confirmations and direct navigation from real project links;
- versioned database JSON export/import with rollback-backed dry-run by default.

## Persistence facts

- ORM models: `shared/database/models/`.
- Unexpected UI-event failures are stored in `application_issues`; Admin shows the latest 50.
- Ordered schema revisions: `shared/database/migrations/versions/`.
- Optional idempotent seeds: `shared/database/seeds/`.
- Relational project metadata is 3NF; artifact JSON is an intentional opaque document aggregate.
- Phase To-Dos reference `phases.id` and survive reorder/edit operations; real phase deletion
  cascades the matching To-Dos.
- `project_links` stores project relationships; `resource_links` stores web/file targets.
- Projects, phases, links, and artifacts cascade from project deletion as defined by SQLite.
- Diagram JSON version: `1`.
- Workspace JSON version: `5`.
- Workspace JSON stores colored strokes and shapes plus images, position, size, and rotation;
  managed images use portable `managed://images/<filename>` references.
- Migration head: `0011`; database export format: `5`.
- Phase rows persist dates, description, normalized lifecycle status, optional Custom section,
  created timestamp, and updated timestamp; older phase rows are preserved and mapped forward.
- Artifact codecs reject unknown future versions and migrate supported older payloads when saved.
- Deleting an image object does not delete its managed source file.
- Image location: `<data_directory>/projects/<project-id>/images/<uuid>.<ext>`.
- Remote clients materialize managed images below `~/.cache/project_planner/images/<project-id>/`.
- Image uploads default to a 20 MiB limit and validate supported file signatures.

## Configuration precedence

1. packaged `src/project_planner/config/default.cfg`;
2. `./project_planner.cfg`;
3. `~/.config/project_planner/config.cfg`;
4. environment variables.

Important overrides:

- `PROJECT_PLANNER_DB`
- `PROJECT_PLANNER_DB_URL`
- `PROJECT_PLANNER_DATA_DIR`
- `PROJECT_PLANNER_WINDOW_WIDTH`
- `PROJECT_PLANNER_WINDOW_HEIGHT`
- `PROJECT_PLANNER_FULLSCREEN`
- `PROJECT_PLANNER_AUTOSAVE_SECONDS`
- `PROJECT_PLANNER_UI_SCALE`
- `PROJECT_PLANNER_API_URL`
- `PROJECT_PLANNER_API_CORS_ORIGINS`
- `PROJECT_PLANNER_API_TOKEN`
- `PROJECT_PLANNER_MAX_IMAGE_BYTES`

`PROJECT_PLANNER_UI_SCALE` accepts `auto` or a numeric value from `0.05` through `5.00`.
Dropdown choices are saved to `~/.config/project_planner/config.cfg`; environment overrides win.

## High-value paths

- FastAPI/composition: `src/project_planner/api/`
- API feature contracts: `src/project_planner/api/<feature>/dtos/`
- Kivy HTTP transport/facade: `frontend/src/project_planner_frontend/api/`
- Kivy feature clients/views: `frontend/src/project_planner_frontend/{projects,planning,collaboration,artifacts,system}/`
- Feature modules: `src/project_planner/modules/`
- Project entities/protocols/services/repositories/mappers:
  `src/project_planner/modules/projects/`
- Artifact persisted documents/codecs: `src/project_planner/modules/artifacts/`
- Settings: `src/project_planner/shared/settings/`
- Database/migrations: `src/project_planner/shared/database/`
- UI shell: `frontend/src/project_planner_frontend/shell/ProjectPlannerRoot.py`
- Theme: `frontend/src/project_planner_frontend/shared/theme.py`
- Workspace: `frontend/src/project_planner_frontend/artifacts/views/workspace/`
- Diagram: `frontend/src/project_planner_frontend/artifacts/views/diagram/`
- Tests: `tests/`

## Known environment behavior

- System `python3` is 3.14.4. Running `python3 -m venv .venv` recreates an incompatible venv.
  Use `make setup`; it locates Python 3.11–3.13 and replaces incompatible environments.
- `uv` is optional and is not an application dependency. Standard `venv` + `pip` is preferred
  when Python 3.11–3.13 is installed. On systems that only provide newer Python, `pipx install uv`
  can supply the compatible interpreter used by `make setup`.
- Startup forces Kivy's bundled SDL2 clipboard. A narrow log filter suppresses only Kivy 2.3.1's
  failed optional X11 cutbuffer probe when `xclip`/`xsel` are absent; real clipboard/window
  failures remain visible.
- Desktop mouse input disables Kivy's right/middle-click multitouch emulation, preventing simulated
  touch markers from appearing during conventional pointer use.
- Kivy schedules some layout work after `build()`. Always exercise the event loop for UI work.
- `pyproject.toml` pins direct dependencies exactly; `pylock.toml` pins and hashes the transitive
  Python 3.13 Linux graph. Refresh intentionally with `make lock`.

## Cache refresh triggers

Update this file when any of these change: Python/Kivy support, commands, entrypoints, module
boundaries, schema, artifact JSON versions, configuration keys, default paths, tests, or known
runtime warnings.
