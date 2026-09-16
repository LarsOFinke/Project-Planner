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
