# Known issues and platform notes

- Kivy 2.3.1 has no usable Python 3.14 wheel in this environment.
- `xclip` and `xsel` are absent. Normal application startup suppresses only their known optional
  Cutbuffer probe; direct Kivy scripts that bypass the frontend bootstrap may still show it.
- Freehand strokes from early artifact versions use absolute canvas coordinates; shape and image
  objects use canvas-relative coordinates.
- Workspace transform controls use fixed increments: rotation ±15°, scaling ×0.85/×1.15.
- Managed image garbage collection is intentionally not implemented in prototype 0.1.
- Backup import rolls back on ordinary errors, but a process or machine crash between publishing
  new managed files and committing database rows can leave those files behind. Retain the archive
  until the imported project has been verified; cross-resource crash recovery is future work.
- The unpacked-backup limit runs after FastAPI has received the multipart upload. Remote servers
  should also enforce a compressed/request-body size limit at their HTTP ingress.
