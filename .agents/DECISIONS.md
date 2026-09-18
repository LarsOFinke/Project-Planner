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
