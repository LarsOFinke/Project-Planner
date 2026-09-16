# Architecture map

```text
frontend -> application services -> repository ports <- SQLite adapters
                         |
                      domain
```

## Core

`src/project_planner/core/domain/`
: Immutable entities and enums grouped by projects, phases, links, and artifacts.

`src/project_planner/core/application/`
: Use cases grouped by feature. Planning strategies live under `planning`; managed image import
  is handled by `assets/image_asset_service.py`.

`src/project_planner/core/ports/`
: Repository protocols. Application logic depends on these boundaries rather than SQLite.

`src/project_planner/core/infrastructure/`
: SQLite connection, schema, and one repository adapter per file.

`src/project_planner/core/bootstrap/`
: Creates the database, adapters, services, and immutable `ApplicationContainer`.

`src/project_planner/core/configuration/`
: Typed settings and cfg/environment resolution.

## Frontend

`src/project_planner/frontend/shell/`
: Responsive application shell, project sidebar, and planning-level tabs.

`projects/`, `phases/`, `links/`
: Metadata workflows and list-based planning interfaces.

`diagram/`
: Node/edge editor with persisted version-1 JSON.

`workspace/`
: Freehand canvas, draggable shape/image objects, transforms, toolboxes, and version-3 JSON.

`shared/`
: Theme tokens and dialog helpers. White is intentionally replaced by pearl grey. Gold means
  primary/selected; red means destructive/blocked.

## Dependency rules

- `core` never imports `frontend` or Kivy.
- Domain entities never import application, infrastructure, or UI modules.
- Frontend does not execute SQL or copy assets directly; it calls container services.
- Repository adapters share `SQLiteDatabase`, but each adapter has one responsibility.
- Each source file contains at most one class.
