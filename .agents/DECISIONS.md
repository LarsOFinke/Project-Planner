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

## AD-011 — Resolution-aware UI scale

The default `auto` scale preserves the proven 200% experience for the 1280×800 laptop profile
and uses 100% for 1920×1080 or larger windows. Explicit cfg/environment values remain available
for unusual DPI and accessibility needs.
