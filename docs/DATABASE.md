# Database architecture

Project Planner uses SQLAlchemy 2.x for ORM/session handling and Alembic for ordered schema
migrations. SQLite remains the zero-configuration default, while `[database] url` or
`PROJECT_PLANNER_DB_URL` can select another SQLAlchemy-compatible database later.

## Migration and seed boundaries

- `core/infrastructure/database/migrations/versions/` contains ordered, immutable structure
  changes. Startup upgrades the configured database to the current revision.
- An existing prototype database without Alembic metadata is safely baselined at revision `0001`;
  subsequent migrations add phase metadata, contextual To-Dos, seed history, and resource links
  without deleting rows.
- `core/infrastructure/database/seeds/` contains the idempotent seed contract and runner. Each seed
  has its own class/file and is recorded in `seed_history` only after it succeeds.
- Prototype 0.1 has no demo-data seed. Opening the application must never add sample projects to a
  user's local database.

Migrations own structure; seeds own optional/reference records. Keeping them separate prevents a
schema rollback or upgrade from silently behaving like application data setup.

## 3NF review

The relational metadata schema conforms to third normal form:

| Relation | Candidate key | Non-key dependencies |
| --- | --- | --- |
| `projects` | `id` | title, description, status, method, parent and timestamps depend only on `id` |
| `phases` | `id`; `(project_id, position)` | phase metadata depends on the selected candidate key, with no derived project attributes stored |
| `project_links` | `(source_id, target_id, relation)` | `note` depends on the whole relationship key |
| `todos` | `id` | title, description, module, optional phase and timestamps depend only on `id`; project/phase data is referenced, not copied |
| `artifacts` | `id`; `(project_id, kind)` | title, content and timestamps depend on the artifact key |
| `resource_links` | `id` | title, target, kind and timestamps depend only on `id`; project data is referenced, not copied |
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

`artifacts.content` is an intentional document boundary: diagram/workspace JSON is treated as one
opaque, versioned value by the relational layer and interpreted by dedicated codecs. Its internal
nodes, strokes, and canvas objects are not relational facts and are never queried or joined by SQL.
This preserves a simple aggregate boundary without denormalizing project metadata.

## Transfer behavior

`project-planner-db export` writes a versioned JSON document atomically. Import validates the
format, merges projects before dependent rows, and performs the whole operation in one transaction.
Dry-run is the default and always rolls that transaction back after constraints have been checked.
`--apply` is required to commit. Import never removes records that are absent from the export.

The export covers database rows only. Workspace image binaries live in the configured data
directory and require a separate filesystem backup.
