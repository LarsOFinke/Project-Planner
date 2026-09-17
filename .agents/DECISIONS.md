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

Feature panels receive narrow service dependencies. Cross-module operations live in application
workflow services, while UI-oriented joins and hierarchy shaping use framework-independent read
models. The complete application container is visible only to the frontend composition root.

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

Month construction, navigation, and ISO date parsing live in the framework-independent core
calendar service. Kivy modules reuse one Date input and popup implementation, keeping date fields
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
