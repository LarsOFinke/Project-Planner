# Database architecture

Project Planner uses SQLAlchemy 2.x for ORM/session handling and Alembic for ordered schema
migrations. SQLite remains the zero-configuration default, while `[database] url` or
`PROJECT_PLANNER_DB_URL` can select another SQLAlchemy-compatible database later.

## Migration and seed boundaries

- `shared/database/migrations/versions/` contains ordered, immutable structure
  changes. Startup upgrades the configured database to the current revision.
- An existing prototype database without Alembic metadata is safely baselined at revision `0001`;
  subsequent migrations add phase metadata, contextual To-Dos, seed history, resource links, and
  the minimal planning relations without deleting rows.
- Revision `0008` repairs early prototype databases whose sprint-status constraint predates the
  `planned` state; existing sprint rows are preserved during the SQLite table rebuild.
- Revision `0009` adds the local `application_issues` diagnostics log used by the Admin screen.
- Revision `0010` adds normalized project categories and a nullable category reference on projects.
- Revision `0011` repairs the phase-to-project cascade rule in existing SQLite databases so
  deleting a project removes its phases, phase tasks, and phase To-Dos atomically.
- `shared/database/seeds/` contains the idempotent seed contract and runner. Each seed
  has its own class/file and is recorded in `seed_history` only after it succeeds.
- Prototype 0.1 has no demo-data seed. Opening the application must never add sample projects to a
  user's local database.

Migrations own structure; seeds own optional/reference records. Keeping them separate prevents a
schema rollback or upgrade from silently behaving like application data setup.

## 3NF review

The relational metadata schema conforms to third normal form:

| Relation | Candidate key | Non-key dependencies |
| --- | --- | --- |
| `project_categories` | `id`; `name` | display order and timestamps depend only on the category |
| `projects` | `id` | setup, ownership text, notes, status, method, category, parent and timestamps depend only on `id` |
| `planning_sections` | `id` | project, model, order, optional dates and status depend only on the section |
| `sprints` | `id` | project/context, dates, goal and lifecycle state depend only on the sprint |
| `backlog_items` | `id` | project/context, optional sprint, work fields and order depend only on the item |
| `section_items` | `id` | free-section work fields and order depend only on the item |
| `phases` | `id`; `(project_id, position)` | phase metadata and optional section depend on the selected candidate key, with no project facts copied |
| `waterfall_tasks` | `id` | phase, work fields, dates, status and order depend only on the task |
| `project_links` | `(source_id, target_id, relation)` | `note` depends on the whole relationship key |
| `todos` | `id` | title, description, module, optional phase and timestamps depend only on `id`; project/phase data is referenced, not copied |
| `artifacts` | `id`; `(project_id, kind)` | title, content and timestamps depend on the artifact key |
| `resource_links` | `id` | title, target, kind and timestamps depend only on `id`; project data is referenced, not copied |
| `application_issues` | `id` | source, exception details and occurrence time depend only on the issue |
| `seed_history` | `key` | `applied_at` depends only on the seed key |

All columns are atomic for their application domain, repeating groups are separate rows, and
foreign keys replace duplicated project facts. Status, planning-method, module, kind, and relation
values have no independent descriptive attributes, so keeping their stable codes on the owning row
does not introduce a transitive dependency. If these codes later gain user-editable labels or other
metadata, they should become reference tables in a new migration.

Phase To-Dos use a nullable `phase_id` foreign key rather than copying a phase name. Reordering or
editing phases updates rows in place so attached To-Dos remain intact; deleting a phase cascades
only its own To-Dos. Project relationships remain in `project_links`, while web URLs and local
filesystem targets are separate `resource_links`, avoiding overloaded link semantics.

Custom planning uses one `planning_sections` relation with a stable type code. Agile records and
Waterfall phases optionally reference a section, so mixed models reuse the same normalized tables
instead of creating one table per combination. Free items are separate rows rather than repeating
columns on a section. Project owner and assignee are intentionally atomic display names in 0.1;
they have no independent editable attributes yet, so a person directory would add identity and
workflow complexity without removing a current transitive dependency.

`artifacts.content` is an intentional document boundary: diagram/workspace JSON is treated as one
opaque, versioned value by the relational layer and interpreted by dedicated codecs. Its internal
nodes, strokes, and canvas objects are not relational facts and are never queried or joined by SQL.
This preserves a simple aggregate boundary without denormalizing project metadata.

## Transfer behavior

`project-planner-db export` writes a versioned JSON document atomically. Import validates the
format, merges categories and projects before dependent rows, and performs the whole operation in
one transaction.
Dry-run is the default and always rolls that transaction back after constraints have been checked.
`--apply` is required to commit. Import never removes records that are absent from the export.

The export covers database rows only. Workspace image binaries live in the configured data
directory and require a separate filesystem backup. Local application diagnostics are deliberately
excluded from project exports because they describe the running installation rather than project
content.
