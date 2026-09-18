# Product roadmap

## Product principles

1. Local-first: a project remains useful without an account or network.
2. Progressive detail: overview first, phase plan second, visual workspaces on demand.
3. One mental model: every plan, diagram, and canvas is an artifact belonging to a project.
4. KISS: ship small vertical slices and use JSON only for editor-specific payloads.
5. SOLID boundaries: UI, use cases, domain rules, and persistence depend inward through
   narrow contracts.

## Milestones

### M1 — Project library (prototype 0.1)

Create, categorize, browse, nest, and update projects. Show status, planning method, description,
and timestamps. Persist everything in SQLite.

### M2 — Minimal planning (prototype 0.1)

Agile backlog/sprint flow, Waterfall phases/tasks/timeline, and mixed Custom sections are
implemented. Milestones and task dependencies remain follow-up work.

### M3 — Structured diagrams (basic editor in prototype 0.1)

A persistent draggable node/edge editor is implemented. Pan, zoom, richer UML shapes,
undo/redo, import/export, and SVG/PNG export remain follow-up work.

### M4 — Free workspace (basic editor in prototype 0.1)

Persistent freehand strokes, shapes, managed images, transforms, color selection, and autosave are
implemented. Text objects, grouping, infinite pan/zoom, and undo remain follow-up work.

### M5 — Connections and polish

Linked projects, backlinks, transactional database export/import, recoverable UI errors, and local
health diagnostics are implemented. Search/filtering, recent projects, archive, complete managed
asset backups, keyboard navigation, accessibility, and recovery from autosaved revisions remain.

## Explicit non-goals for the first release

- real-time collaboration or accounts
- cloud sync
- a full Draw.io file-format implementation
- plugin APIs before core workflows stabilize
