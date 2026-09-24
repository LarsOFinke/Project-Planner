# Troubleshooting

Start with:

```bash
bash .agents/scripts/doctor.sh
bash .agents/scripts/check-all.sh
```

Create a shareable local report with:

```bash
bash .agents/scripts/collect-diagnostics.sh
```

Reports are written to `.agents/debugging/reports/` and ignored. In a managed environment where
`.agents` is runtime read-only, the collector falls back to
`${TMPDIR:-/tmp}/project-planner-diagnostics/`. Review reports before sharing; the scripts avoid
environment dumps and database contents, but paths and platform versions are included.

## Symptom routing

### `requires a different Python`

Cause: `.venv` was created by system Python 3.14 or its base interpreter was removed. Run
`make setup`; it downloads a project-local CPython 3.13 runtime when no compatible system Python
exists, then clears and rebuilds unusable environments. Do not use `python3 -m venv .venv` on
this machine.

### Kivy Cutbuffer warning for `xclip` or `xsel`

Non-fatal when the app continues into `Start application main loop`. SDL2 clipboard is active.
Install `xclip` at the OS level only if X primary-selection support is wanted.

### Window opens and then exits with a traceback

Ignore earlier provider warnings and read the final traceback. Kivy layout exceptions are often
deferred until the first clock tick, so reproduce with a real event loop.

### Controls clip at 200% scaling

Do not shrink fonts locally. Use responsive widths and scrollable tool docks. Validate
at both 1280×800 and 960×620 where practical.

### Workspace object appears outside the canvas

Check the logical-to-screen `CanvasTransform` and `_sync_view` in `FreehandCanvas.py`.
The canvas uses `StencilView` to clip children to its bounds.

### Imported image disappears after restart

Check `PROJECT_PLANNER_DATA_DIR`, file existence in the managed per-project image directory,
and the artifact's image `source` reference. Do not print or attach the image contents.

### Database behavior differs from tests

Confirm `PROJECT_PLANNER_DB`. Tests generally use `:memory:` while the app defaults to the user
data directory. Inspect schema, not private database rows, unless the user authorizes it.
