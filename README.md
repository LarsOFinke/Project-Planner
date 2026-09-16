# Project Planner

A local-first desktop application for moving from a project overview to phase plans,
structured diagrams, and a free-form workspace without splitting knowledge across tools.

## Prototype 0.1

- file-browser-style project hierarchy
- project status, description, planning method, and timestamps
- editable project links and backlinks
- editable Waterfall, Agile, and Custom phase plans
- local SQLite persistence
- modular Kivy desktop UI with project browser and tabbed planning levels
- persistent node/edge diagram editor with draggable nodes
- persistent freehand workspace with local autosave, movable/rotatable/scalable shapes and images

The core is deliberately independent from Kivy and SQLite details. This keeps the business
rules testable and lets visual editors evolve without becoming coupled to project metadata.

## Run locally

The project pins Python 3.13 because Kivy 2.3.1 does not provide a Python 3.14 wheel. The
bootstrap script explicitly locates Python 3.11–3.13, replaces an incompatible `.venv`,
installs the application, and runs its tests:

```bash
make setup
make run
```

Do not recreate the environment with `python3 -m venv .venv` on a machine whose `python3`
is 3.14; that command ignores `.python-version` and puts the incompatible interpreter back.
Use `make setup` whenever the environment needs to be rebuilt.

By default the database is created at `~/.project_planner/project_planner.sqlite3`.
Configuration is read in this order: packaged defaults, `./project_planner.cfg`,
`~/.config/project_planner/config.cfg`, then environment variables. Copy
`project_planner.cfg.example` to either configuration location when you want file-based
settings. Available environment overrides are `PROJECT_PLANNER_DB`,
`PROJECT_PLANNER_WINDOW_WIDTH`, `PROJECT_PLANNER_WINDOW_HEIGHT`, and
`PROJECT_PLANNER_AUTOSAVE_SECONDS`. UI density can be adjusted with
`PROJECT_PLANNER_UI_SCALE`; the high-readability default is `2.00`.
Imported workspace images are copied below `~/.project_planner/data` by default. Override
that location with `PROJECT_PLANNER_DATA_DIR` or `[storage] data_directory` in the `.cfg`.
PNG, JPEG, GIF, BMP, and WebP imports are supported; deleting a canvas object does not delete
its managed source file, protecting imported data from accidental loss.

Run the core tests without installing Kivy:

```bash
python -m pytest
```

## Architectural shape

```text
frontend/ -> core/application/ -> core/ports/ <- core/infrastructure/
                         |
                    core/domain/
```

- each class has its own file
- related classes are grouped by feature subpackage
- `project_planner/core/domain`: entities and value types
- `project_planner/core/application`: use cases and planning strategies
- `project_planner/core/ports`: narrow repository contracts
- `project_planner/core/infrastructure`: SQLite database and repository adapters
- `project_planner/core/configuration`: `.cfg` and environment configuration
- `project_planner/frontend`: Kivy shell and feature panels; it depends on `core`, never the
  reverse

See [docs/ROADMAP.md](docs/ROADMAP.md) for the incremental product plan.
