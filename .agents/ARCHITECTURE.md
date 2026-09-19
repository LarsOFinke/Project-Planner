# Architecture map

Project Planner is a feature-first modular monolith with a physically separate Kivy client.

```text
Kivy UI -> typed HTTP clients -> FastAPI /api/v1 feature controllers
                                                               |
entities <- services -> protocols <- repositories -> SQLAlchemy models
                              ^             |
                              └── mappers <-┘
```

## Backend

`src/project_planner/api/`
: FastAPI application factory, embedded/standalone Uvicorn hosts, and controller composition.
  Each `api/<feature>/` keeps its route-owning controller at the feature root and transport DTOs
  below `dtos/`. OpenAPI is the public contract; no aggregate application or service container
  exists.

`src/project_planner/modules/<feature>/`
: Business modules grouped vertically. A module owns only the layer directories it needs:
  `entities`, `protocols`, `services`, `repositories`, `mappers`, `documents`, and `models`.
  Transport DTOs do not live in business modules.

`src/project_planner/modules/transfer/gateways/`
: Explicit database import/export boundary. It is a gateway—not a repository—because it transfers
  a complete relational snapshot rather than managing one aggregate. The System API transports
  snapshot documents; the desktop System client owns local file selection and atomic writes.

`src/project_planner/modules/projects/`
: Project/category entities, repository protocols, workflows, persistence repositories, and
  entity/ORM mappers. API-specific directory and overview projections live under `api/projects`.
  Categories organize projects without owning their lifecycle; deleting a category moves its
  projects to Uncategorized. Tree moves update parent/category placement together and carry the
  full descendant subtree into the target category.

`src/project_planner/modules/planning/`
: One cohesive planning capability containing Agile backlog/sprints, Custom sections, and
  Waterfall phases/tasks. These are strategies within one feature rather than peer modules.

`src/project_planner/modules/artifacts/`
: Artifact entity and persistence contract, typed persisted Diagram/Workspace documents,
  version-aware codecs, service, and repository.

`src/project_planner/shared/database/`
: SQLAlchemy session boundary, shared ORM schema models, ordered Alembic migrations, and isolated
  seeds. Feature services never import this directory.

`src/project_planner/shared/settings/`
: Typed cfg/environment settings and persistence of user UI preferences.

`src/project_planner/shared/utils/`
: Small dependency-free helpers that are genuinely shared; feature-specific helpers stay in their
  module.

## Frontend

`frontend/src/project_planner_frontend/`
: Independently discoverable Kivy client package. `api/` owns transport and the connection facade.
  Desktop mode starts an ephemeral localhost API; remote mode uses the configured API URL. The
  backend never imports this package.

`projects/`, `planning/`, `collaboration/`, `artifacts/`, `system/`
: Frontend feature boundaries mirroring the five FastAPI controllers. Each owns its `clients/`
  and `views/`; planning views retain Agile, Custom, and Waterfall subdirectories.

`artifacts/views/diagram/`, `artifacts/views/workspace/`
: Node/edge and free-form editors for persisted artifact documents.
  Managed images use portable document references and are materialized through the HTTP client
  into a client-local cache before Kivy rendering.

`shared/`
: Kivy-only theme tokens, dialog helpers, layouts, and reusable controls. White is intentionally
  replaced by pearl grey. Gold means primary/selected; red means destructive/blocked.

## Dependency rules

- Backend code never imports `project_planner_frontend` or Kivy.
- Module entities import neither protocols, services, repositories, mappers, nor API code.
- API DTOs may reference entities but never services, repositories, or mappers.
- Protocols may reference entities/documents but never services, repositories, or API composition.
- Services depend on entities, documents, models, and protocols; they never import API or
  SQLAlchemy/database code.
- Repositories implement protocols and may use `shared/database` plus explicit mappers.
- Mappers translate between feature entities and SQLAlchemy schema models where that translation
  is substantial enough to deserve a separate unit.
- Only `api/controller_builder.py` composes repositories, services, and feature controllers.
- Each FastAPI feature controller owns its `/api/v1` routes and coordinates its services directly.
- Controller `_register_routes()` methods delegate to small resource-specific registration helpers
  so the route table remains readable without recreating a separate router layer.
- Frontend panels depend on typed feature HTTP clients, never backend services or composition
  types; frontend feature names mirror their API controllers.
- Frontend code never imports SQLAlchemy, `shared/database`, or module repositories.
- Kivy clients decode API DTOs; canvases render typed persisted documents and do not parse JSON.
- Each source file contains at most one class, and class modules use the exact PascalCase class
  name as their filename.
