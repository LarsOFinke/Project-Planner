# Project Planner

A local-first desktop application for moving from a project overview to phase plans,
structured diagrams, and a free-form workspace without splitting knowledge across tools.

## Prototype 0.1

- file-browser-style project hierarchy
- project status, description, planning method, and timestamps
- editable project links and backlinks
- editable Waterfall, Agile, and Custom phase objects with descriptions, statuses, and timestamps
- local SQLite persistence
- modular Kivy desktop UI with project browser and tabbed planning levels
- persistent node/edge diagram editor with draggable nodes
- persistent freehand workspace with explicit Select/Draw modes, selectable stroke/shape colors,
  local autosave, and movable, rotatable, scalable shapes and images
- categorized diagram and workspace toolboxes that keep dense actions readable across scale profiles

The core is deliberately independent from Kivy and SQLite details. Application workflows own
cross-feature operations, query services provide UI-ready read models, and versioned codecs keep
artifact JSON outside Kivy canvases. Feature panels receive only the services they use.

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

If the target system only provides Python 3.14 or newer, install `uv` in an isolated environment
with `pipx`. This was verified on the development system:

```bash
pipx install uv
make setup
```

If `uv` is not immediately available, run `pipx ensurepath`, start a new shell, and retry.
`make setup` asks `uv` for Python 3.13, creates the project `.venv` with that interpreter,
installs the application, and runs the test suite. Do not manually create `.venv` with the newer
system `python3`. See the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
for alternative platforms and installation methods.

By default the database is created at `~/.project_planner/project_planner.sqlite3`.
Configuration is read in this order: packaged defaults, `./project_planner.cfg`,
`~/.config/project_planner/config.cfg`, then environment variables. Copy
`project_planner.cfg.example` to either configuration location when you want file-based
settings. Available environment overrides are `PROJECT_PLANNER_DB`,
`PROJECT_PLANNER_WINDOW_WIDTH`, `PROJECT_PLANNER_WINDOW_HEIGHT`, and
`PROJECT_PLANNER_AUTOSAVE_SECONDS`. UI density can be adjusted with
`PROJECT_PLANNER_UI_SCALE`. The top-right scale dropdown provides 5%–500% in 5% steps, applies
changes immediately, and saves the choice to `~/.config/project_planner/config.cfg`. The initial
`auto` profile uses the configured window dimensions as a fallback: 200% for 1280×800 and 100%
for 1920×1080 or larger. Set a numeric cfg/environment value from `0.05` through `5.00` to
override it; an environment override remains authoritative over the saved dropdown preference.
The selected project remains open when the scale changes.
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

- each class has its own matching PascalCase file
- related classes are grouped by feature subpackage
- `project_planner/core/domain`: entities and value types
- `project_planner/core/application`: use cases, workflow orchestration, query projections,
  planning strategies, and artifact codecs
- `project_planner/core/ports`: narrow repository contracts
- `project_planner/core/infrastructure`: SQLite database and repository adapters
- `project_planner/core/configuration`: `.cfg` and environment configuration
- `project_planner/frontend`: Kivy shell and feature panels; it depends on `core`, never the
  reverse

See [docs/ROADMAP.md](docs/ROADMAP.md) for the incremental product plan.
