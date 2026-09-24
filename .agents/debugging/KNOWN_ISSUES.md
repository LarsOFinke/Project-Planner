# Known issues and platform notes

- Kivy 2.3.1 has no usable Python 3.14 wheel in this environment.
- `xclip` and `xsel` are absent. Normal application startup suppresses only their known optional
  Cutbuffer probe; direct Kivy scripts that bypass the frontend bootstrap may still show it.
- Early workspace documents use absolute screen coordinates for strokes and canvas-relative pixels
  for shapes/images; diagram v1 uses absolute node coordinates. The current editors convert these
  on load to logical units, using the current canvas origin for the historical absolute values.
  Since old documents did not record their original viewport, legacy placement is best-effort;
  verify old visual artifacts before further editing/saving.
- Workspace transform controls use fixed increments: rotation ±15°, scaling ×0.85/×1.15.
- Editor undo/redo is in-memory (50 steps) and resets on project change. Direct-manipulation
  resize handles, rotation-aware hit testing, a visible grid, SVG/PNG export, and crash-durable
  unsaved revision recovery remain future work. Image assets uploaded but never referenced by a
  saved workspace can still remain in managed storage.
- Managed image garbage collection is intentionally not implemented in prototype 0.1.
- Backup import rolls back on ordinary errors, but a process or machine crash between publishing
  new managed files and committing database rows can leave those files behind. Retain the archive
  until the imported project has been verified; cross-resource crash recovery is future work.
- The unpacked-backup limit runs after FastAPI has received the multipart upload. Remote servers
  should also enforce a compressed/request-body size limit at their HTTP ingress.
