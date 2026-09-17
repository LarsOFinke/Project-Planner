# Project Planner

A local-first desktop application for moving from a project overview to phase plans,
structured diagrams, and a free-form workspace without splitting knowledge across tools.

## Prototype 0.1

- file-browser-style project hierarchy
- shared project setup with dates, owner, assignee, notes, status, and planning model
- project relationships and backlinks managed directly from Overview
- web URLs and local file links in the dedicated Links module
- contextual To-Dos in Overview, individual phases, and Links, plus dedicated nested To-Do tabs
  inside Diagram and Workspace
- Agile planning with an ordered backlog, a collection of planned sprints, completion handling,
  and history
- Waterfall planning with editable ordered phases, phase tasks, and a simple chronological timeline
- Custom planning with ordered Free, Agile, and Waterfall sections that can be mixed freely
- shared calendar date picker backed by framework-independent core month/date logic
- SQLAlchemy persistence with SQLite as the local default and ordered Alembic migrations
- recoverable UI errors with a local diagnostics log and Admin health view
- modular Kivy desktop UI with project browser and tabbed planning levels
- shared low-glare visual system with structural tree indentation, rounded controls, and clear
  section hierarchy
- persistent node/edge diagram editor with draggable nodes
- persistent freehand workspace with explicit Select/Draw modes, selectable stroke/shape colors,
  local autosave, and movable, rotatable, scalable shapes and images
- categorized diagram and workspace toolboxes that keep dense actions readable across scale profiles

The core is deliberately independent from Kivy and SQLite details. Application workflows own
cross-feature operations, query services provide UI-ready read models, and versioned codecs keep
artifact JSON outside Kivy canvases. Feature panels receive only the services they use.

The Plan Roadmap tab follows the selected project's model. Agile keeps a backlog beside a sprint
directory; opening a planned or completed sprint shows its To Do, In Progress, and Done work in
an overlay. Waterfall supplies Phases & Tasks plus Timeline. Custom keeps every Free, Agile, or
Waterfall section in one stable ordered roadmap, including completed sections. Changing a Custom
section model preserves its existing records and adds the selected template structure, leaving
any reorganization to the user.

Every planning date field remains keyboard-editable and includes the same Date button. The shared
calendar supports month navigation, adjacent-month days, Today, and Clear, while ISO parsing and
month calculations remain in `core/application/calendar` rather than individual UI modules.

## Run locally

The project currently supports Python 3.11–3.13 because Kivy 2.3.1 does not provide a Python
3.14 wheel. A standard library virtual environment and `pip` are the baseline setup:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

The bootstrap script automates the same process, locates a compatible interpreter, replaces an
incompatible `.venv`, installs the application, and runs its tests:

```bash
make setup
make run
```

Do not recreate the environment with `python3 -m venv .venv` on a machine whose `python3`
is 3.14; that command ignores `.python-version` and puts the incompatible interpreter back.
Use `make setup` whenever the environment needs to be rebuilt.

`uv` is not an application dependency and is not required when Python 3.11–3.13 is installed.
If a target system only provides Python 3.14 or newer, it can optionally bootstrap a compatible
interpreter; install it in an isolated environment with `pipx`:

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
`PROJECT_PLANNER_DB_URL`,
`PROJECT_PLANNER_WINDOW_WIDTH`, `PROJECT_PLANNER_WINDOW_HEIGHT`, and
`PROJECT_PLANNER_AUTOSAVE_SECONDS`. The application starts in native fullscreen mode by default;
set `PROJECT_PLANNER_FULLSCREEN=false` or `[window] fullscreen = false` for a normal window.
The bottom-left Exit button closes the fullscreen application after flushing pending Diagram and
Workspace changes. The top-right Windowed/Fullscreen button switches modes immediately and saves
the selection for the next launch.
UI density can be adjusted with
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

On Linux, startup explicitly selects Kivy's bundled SDL2 clipboard. Kivy 2.3.1 also probes the
optional X11 primary-selection tools `xclip` and `xsel`; Project Planner suppresses only that known
non-fatal probe message when those tools are absent. Normal copy/paste continues through SDL2, and
all other Kivy critical errors remain visible.

### Database export and import

Export all relational project data to a versioned JSON document:

```bash
project-planner-db export planner-backup.json
```

Import is a transactional dry run by default. It validates and flushes the records, then rolls the
transaction back so the database remains untouched:

```bash
project-planner-db import planner-backup.json --dry-run
project-planner-db import planner-backup.json --apply
```

Import merges records by primary key and does not delete unrelated local records. Managed image
files are outside the database and therefore must be backed up from the configured data directory
separately. See [docs/DATABASE.md](docs/DATABASE.md) for migrations, seeds, and normalization.

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
- `project_planner/core/infrastructure`: SQLAlchemy database, migrations, seeds, transfer service,
  and repository adapters
- `project_planner/core/configuration`: `.cfg` and environment configuration
- `project_planner/frontend`: Kivy shell and feature panels; it depends on `core`, never the
  reverse

See [docs/ROADMAP.md](docs/ROADMAP.md) for the incremental product plan.
