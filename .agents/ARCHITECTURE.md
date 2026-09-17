# Architecture map

```text
frontend -> application services -> repository ports <- SQLAlchemy adapters
                         |
                      domain
```

## Core

`src/project_planner/core/domain/`
: Immutable entities and enums grouped by projects, phases, links, and artifacts.

`src/project_planner/core/application/`
: Use cases grouped by feature. Planning strategies live under `planning`; managed image import
  is handled by `assets/ImageAssetService.py`.

`src/project_planner/core/application/projects/`
: Project CRUD is separated from workflow orchestration and read projections. The workflow
  service coordinates projects with phase templates; the query service produces overview,
  choice, and flattened-tree models for the frontend.

`src/project_planner/core/application/artifacts/`
: Artifact persistence remains generic. Diagram and workspace codecs own JSON validation,
  version compatibility, and typed document conversion.

`src/project_planner/core/ports/`
: Repository protocols. Application logic depends on these boundaries rather than SQLite.

`src/project_planner/core/infrastructure/`
: SQLAlchemy connection/session boundary, Alembic migrations, isolated seeds, versioned transfer
  service, and one repository adapter per file. SQLite is the default configured dialect.

`src/project_planner/core/bootstrap/`
: Creates the database, adapters, services, and immutable `ApplicationContainer`.

`src/project_planner/core/configuration/`
: Typed settings and cfg/environment resolution.

## Frontend

`src/project_planner/frontend/shell/`
: Responsive application shell, project sidebar, and planning-level tabs.

`projects/`, `phases/`, `links/`, `todos/`
: Metadata workflows, contextual To-Do management, project relationships in Overview, and
  separate web/filesystem resource links.

`diagram/`
: Node/edge editor with persisted version-1 JSON.

`workspace/`
: Freehand canvas, draggable shape/image objects, transforms, toolboxes, and version-3 JSON.

`shared/`
: Theme tokens, dialog helpers, and the reusable categorized-toolbox control. White is
  intentionally replaced by pearl grey. Gold means primary/selected; red means
  destructive/blocked.

## Dependency rules

- `core` never imports `frontend` or Kivy.
- Domain entities never import application, infrastructure, or UI modules.
- Frontend does not execute SQL or copy assets directly; it calls container services.
- Feature panels receive only the services they use; only the frontend composition root sees the
  complete `ApplicationContainer`.
- Kivy canvases render typed documents and do not parse persisted JSON structures.
- Repository adapters share `Database`, but each adapter has one responsibility and no
  dialect-specific SQL.
- Each source file contains at most one class, and class modules use the exact PascalCase class
  name as their filename.
