# Known issues and platform notes

- Kivy 2.3.1 has no usable Python 3.14 wheel in this environment.
- `xclip` and `xsel` are absent, producing a non-fatal Linux Cutbuffer warning.
- Freehand strokes from early artifact versions use absolute canvas coordinates; shape and image
  objects use canvas-relative coordinates.
- Workspace transform controls use fixed increments: rotation ±15°, scaling ×0.85/×1.15.
- Managed image garbage collection is intentionally not implemented in prototype 0.1.
