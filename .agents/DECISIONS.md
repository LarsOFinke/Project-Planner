# Durable decisions

## AD-001 — Local-first SQLite

Project metadata and editor artifacts are stored locally. No account or network is required.

## AD-002 — Core/frontend boundary

The Kivy frontend depends inward on framework-independent services. This keeps domain and
persistence tests runnable without a display server.

## AD-003 — One class per file

Every class has a dedicated source file and related files share feature subpackages. An AST
test prevents regression.

## AD-004 — Versioned editor JSON

Editor-specific content remains JSON inside the artifacts table. Relational metadata stays
normalized. Readers tolerate missing fields so older documents remain usable.

## AD-005 — Managed image copies

Workspace image imports are copied to the configured data directory. Canvas deletion removes
only the object reference, not the managed file, to reduce accidental data loss.

## AD-006 — High-readability UI

The default UI scale is 200%. Navigation widths use physical available space, and dense action
sets use named toolboxes rather than a clipped toolbar.

## AD-007 — Class-module naming

Every Python module that defines a source class uses the exact PascalCase class name as its
filename. Modules without a class retain conventional descriptive snake_case names.

## AD-008 — Application workflows and read projections

Cross-module operations live in application workflow services, while UI-oriented joins and
hierarchy shaping use framework-independent read models. This earlier direct service injection was
superseded by AD-022: feature panels now receive HTTP clients and FastAPI controllers coordinate
the backend services.

## AD-009 — Typed artifact boundaries

Diagram and workspace JSON is decoded into typed, versioned documents before reaching Kivy
canvases. Codecs own validation and compatibility; widgets own rendering and interaction.

## AD-010 — Categorized editor toolboxes

Editors with several commands use the shared categorized-toolbox control so actions remain
discoverable and unclipped at 200% scaling. Small two-action areas remain direct controls.

## AD-011 — User-controlled persistent UI scale

A top-right dropdown exposes 5%–500% in 5% steps. A change rebuilds the Kivy view at the new
density, preserves project selection, cancels replaced autosave callbacks, and persists to the
user cfg. Numeric environment configuration remains authoritative.

## AD-012 — First-class phase metadata

Phases persist their own description, lifecycle status, creation time, and update time. SQLite
startup performs additive migration for existing phase tables so older project plans remain
available without a manual conversion step.

## AD-013 — Persisted workspace colors

Workspace document version 4 stores colors with strokes and shapes. The codec assigns the former
pearl-grey default when reading version 1–3 documents, preserving their appearance while allowing
new and selected objects to use the workspace palette.

## AD-014 — Explicit workspace interaction modes

The workspace defaults to Select mode so clicking the canvas does not create accidental strokes.
Draw mode routes pointer gestures to freehand strokes instead of draggable objects. Object color
and selection indication are separate: palette colors render faithfully while a gold bounding
frame communicates selection.

## AD-015 — Planning templates are scoped structures

Agile and Waterfall are complete-project templates when selected on a project. Custom stores an
ordered list of sections whose model is independently Free, Agile, or Waterfall. Agile records and
Waterfall phases can therefore reference a section without duplicating their domain or persistence
logic. Changing a section model never deletes old content; it only adds the newly selected minimal
structure.

## AD-016 — One shared calendar boundary

Month construction, navigation, and ISO date parsing live in the framework-independent calendar
service. Kivy modules reuse one Date input and popup implementation, keeping date fields
keyboard-editable while preventing project, sprint, phase, task, and Custom-section pickers from
developing separate behavior.

## AD-017 — Top-anchored editor forms

Editor popups place variable-height fields in a shared top-anchored scroll container and keep the
primary/cancel action row outside it. Short forms no longer drift downward into unused space, while
long forms remain reachable at high UI scales. Empty variable-content areas show an explicit state
instead of an unexplained blank region.

## AD-018 — Recoverable UI exception boundary

Unexpected exceptions raised by Kivy event callbacks are recorded through the application issue
service and surfaced as a recoverable error dialog. Fatal startup, memory, and process-control
exceptions still propagate. The Admin screen reads the same service for health and recent issue
details; diagnostics remain local and are excluded from project database exports.

## AD-019 — Plan as a stable roadmap

The main planning view preserves structural order instead of moving completed work into a separate
queue. Custom sections remain in one roadmap regardless of status. Agile keeps planned and
completed sprints in one directory; selecting a sprint opens its work grouped into To Do, In
Progress, and Done tabs.

## AD-020 — Shared visual system and structural indentation

Application screens use one low-glare navy/slate surface system with restrained gold emphasis,
soft semantic red, bordered surfaces, rounded controls, consistent field focus, section labels,
and empty states. Hierarchy is expressed by layout geometry: project controls are offset as whole
rows and connected with branch guides instead of inserting whitespace into label text. Roadmap
groups use the same whole-row indentation principle so visual nesting remains stable at every
configured UI scale.

## AD-021 — Feature-first backend and replaceable frontend

Backend business code is organized as vertical modules. Each module owns only the entities,
protocols, services, repositories, and mappers it needs. API features own transport DTOs.
Database, settings, and narrow utilities remain shared.
The Kivy client lives in a separate root source package; backend modules never import it. Project
categories are a normalized directory concern inside the Projects module and do not own or delete
projects.

## AD-022 — Versioned HTTP boundary between backend and clients

FastAPI `/api/v1` resources are the public application boundary. Each feature controller owns
its routes and coordinates only that feature's backend services. Kivy
panels receive narrowly typed HTTP clients. Desktop mode hosts the API on an ephemeral loopback
port; a configured remote URL and explicit CORS origins support a later browser frontend. OpenAPI
is the cross-language contract; no aggregate service container is used.

## AD-023 — One planning feature and mirrored frontend boundaries

Agile, Custom sections, phases, and Waterfall tasks are strategies and structures within one
backend Planning capability, so their entities, protocols, services, and repositories live in
`modules/planning`. The Kivy client mirrors the API's Project, Planning, Collaboration, Artifact,
and System feature controllers. Each frontend feature colocates its typed HTTP clients and views;
only transport and connection setup remain in the frontend `api` package.

## AD-024 — API-owned transport DTOs

Each API feature is a module whose controller lives at its root and whose transport/read DTOs live
under `dtos/`. Business modules do not import the API. Persisted Diagram/Workspace structures are
named documents, and database transfer results are internal models, because neither is an HTTP
transport contract. API-specific query projection services may depend inward on business services
and repository protocols.

## AD-025 — Lazy project-view loading

The project directory projection is cached by the browser and reused while selection changes.
Selecting a project loads only the currently visible feature tab; other tabs load on first use and
are cached for that project. Overview remains the explicit default. This keeps HTTP traffic and
database reads proportional to what the user is viewing instead of eagerly hydrating every module.

## AD-026 — Conventional desktop pointer input

The desktop bootstrap disables Kivy's mouse-based multitouch emulation. Right and middle clicks
therefore remain ordinary pointer actions and do not create persistent red touch markers. Text
dialogs request focus after their modal-open event so the first field reliably accepts keyboard
input. Custom input surfaces are inserted before Kivy's native cursor/foreground instructions so
the theme cannot cover or recolor editable text.

## AD-027 — Explicit project lifecycle actions

Archive is a reversible data-preserving state change represented by the project's `archived`
status. Delete is separately confirmed and permanently removes the selected project's owned data;
children remain and become root projects through the existing foreign-key rule. The UI clears open
editor state before choosing a remaining project so deleted artifacts cannot be autosaved again.

## AD-028 — Database-enforced project cleanup

Project deletion relies on database cascades for owned planning records and `SET NULL` for child
projects. Migration 0011 repairs the legacy SQLite phase foreign key while temporarily preserving
phase To-Dos and tasks during the required table rebuild. This keeps deletion atomic and avoids
embedding cross-module cleanup knowledge in the Projects repository.

## AD-029 — Portable managed-image references

Workspace documents store `managed://images/<filename>` references instead of API-host filesystem
paths. The artifact API remains the source of the binary, while each frontend materializes the
asset into a local cache for rendering. Version-5 workspace documents retain support for existing
version-1 through version-4 local paths.

## AD-030 — Authenticated remote API boundary

Loopback desktop hosting remains zero-configuration. A configured bearer token protects all
`/api/v1` resources, and the standalone API refuses non-loopback binding without one. Image
uploads are project-bound, size-limited, and content-checked. TLS remains an external deployment
concern rather than application-managed certificate infrastructure.

## AD-031 — Reproducible validation environment

Direct dependencies are exactly pinned and the transitive Python 3.13 Linux graph is recorded with
artifact hashes in `pylock.toml`. Bootstrap and CI install that lock. Canonical validation includes
real Kivy event-loop smoke runs at both supported density profiles.

## AD-032 — GUI-owned database transfer

Database backup and restore are Admin-panel workflows rather than a separate CLI product surface.
The authenticated System API transfers versioned archives and never assumes that a path on the
desktop exists on a remote API host. The desktop client writes exports atomically and reads the
user-selected import locally. Archives contain a versioned relational JSON snapshot and managed
project images. Dry run validates database rows and image conflicts without persisting either.
Direct import requires confirmation, then restores missing files and applies the transactional
merge. Dry-run and applied reports compare actual database values and managed-file bytes, so
identical records are counted separately and skipped rather than being reported as updates.
The earlier JSON-only API remains available for compatibility.
Archive reads and writes enforce a configurable unpacked-data cap. New managed files are staged
and published atomically; on a normal database-merge failure, only files created by that import
are removed. Database and filesystem cannot share one transaction, so crash-consistent recovery
would require a separate durable journal rather than claiming full atomicity.

## AD-033 — Directory-owned hierarchy organization

The project directory is the primary visual organizer for project hierarchy. Dragging a project
onto a category makes it a root there; dragging it onto another project makes it a child and adopts
the target category. The backend validates cycles and persists the moved project plus any descendant
category changes in one transaction, so a subtree cannot be split across directory sections.

## AD-034 — Named parallel phase groups are a small roadmap primitive

A Waterfall phase may carry an optional short `parallel_group` label. Phases with the same label
are presented as a concurrent lane in the timeline, while blank phases retain the normal ordered
flow. This intentionally does not model dependencies, capacity, or automatic scheduling yet;
the label is a reversible prototype that can inform a later planning model without making the
current workflow misleadingly complex.

## AD-035 — Project hierarchy has explicit sibling ordering

Projects retain a numeric position among their siblings instead of deriving directory order from
titles. A directory-row middle drop retains the existing “make child” behavior, while an upper or
lower edge drop places the project before or after that sibling. This makes hierarchy structure and
ordering available in one interaction without adding separate move controls.

## AD-036 — Background initial fetches

Project-directory, feature-tab, and Admin initial reads run in bounded background workers. Their
results are applied on Kivy's event loop, with generation checks to discard stale responses after
selection changes. Backup transfers use the same mechanism. HTTP timeouts become a clear retry
message, so a slow remote API does not freeze the primary navigation flow.

## AD-037 — Logical editor coordinates and serialized background saves

Diagram v2 and workspace v6 store positions and dimensions in logical canvas units, rather than
window pixels. Viewport pan/zoom and UI scale change only the screen transform; editing geometry
or strokes changes the document. Earlier artifacts are accepted and converted on load, with
best-effort placement for legacy absolute coordinates because their original viewport was never
stored. Workspace v6 adds editable text objects; diagram v2 adds node dimensions. Clear-all is
confirmed and undoable in a bounded in-memory history. Editor saves are serialized off the Kivy
event loop; a failed save leaves the revision dirty and blocks project replacement so it can be
retried. Image upload and materialization also run in a worker, with navigation deferred until
the import completes. This does not claim crash-durable unsaved revision recovery.

## AD-038 — Side-docked visual editor tools

Visual editor actions use one scrollable, task-sectioned dock beside the canvas instead of a
category switcher above it. The most frequent controls stay first: workspace mode, size, rectangle
and text creation; diagram node creation, connection and geometry. Selection-dependent actions are disabled
when inapplicable. The root feature tab already names the editor, so redundant editor headings
are removed to preserve canvas height at 200% UI scale.

## AD-039 — Bounded durable editor recovery

Each successful diagram or workspace save stores the previous nonempty document as an artifact
revision in the same database transaction. The 20 newest earlier versions remain available in
the editor and travel with database backups. Restoring a version saves the current document as a
new revision, so recovery is reversible. Unsaved changes still require a successful save before
the restore control proceeds.

## AD-040 — Journaled backup file publication

Before publishing managed files, backup import writes and syncs a journal of paths and checksums.
The database merge commits an import marker in its transaction. Startup recovery retains files
when that marker exists, or removes unchanged files when the marker is absent. Changed local
files stop recovery so they are not silently deleted.

## AD-041 — Project workflow transactions

Project creation, project updates that initialize phases, and phase-plan resets use one transaction.
Composition injects a context-manager factory into the workflow; business code remains unaware of
SQLAlchemy. Repositories share a context-local session and flush their changes, while the outer
workflow commits or rolls back. Concurrent synchronous requests use separate session contexts.

## AD-042 — Save completion precedes normal shutdown

Exit, application stop, and native window-close requests keep Kivy and the HTTP connection alive
until pending editor revisions, image imports, and active Overview saves complete. Duplicate close
requests are coalesced. Failure restores interaction and permits retry instead of closing with
unsaved changes. This does not provide recovery from process termination or power loss.

## AD-043 — Background Overview mutations

Overview captures and validates a form snapshot on the UI thread, then sends its update through
the existing worker pool. Pending saves prevent duplicate submission and participate in shutdown
and scale-rebuild waits. Completion refreshes the directory asynchronously; a stale completion
cannot replace the project selected since the save started. Failed saves retain the current form.

## AD-044 — Idempotent first artifact creation

Diagram and workspace requests can arrive concurrently for a project that has no artifact yet.
The artifact service keeps the existing lookup, then asks its repository to create the initial
row if absent. The repository uses a savepoint and the database's unique project/kind constraint;
the losing request reloads the winning row. Other integrity failures still propagate. This
keeps SQLAlchemy recovery inside the repository and avoids a first-open HTTP 500.
