# Agent onboarding

## Mission

Maintain a local-first Kivy desktop project planner with hierarchical projects, metadata,
phase planning, linked projects, diagrams, and a visual workspace. Optimize for KISS, SOLID,
readability across user-selected scale profiles, and preservation of local data.

## First five minutes

1. Read `PROJECT_CACHE.md`.
2. Run `git status --short` if the checkout is a Git worktree. Never overwrite unrelated work.
3. Locate the requested feature through the repository map in `ARCHITECTURE.md`.
4. Run the narrowest relevant tests before editing.
5. Use `apply_patch` for source and documentation changes.

Avoid broad discovery unless the cache is stale. Use `rg` and `rg --files`, not recursive
filesystem dumps. Do not install dependencies until `.venv/bin/python --version` confirms a
supported interpreter.

## Development contract

- One source class per file; its PascalCase filename must match the class name exactly.
  `tests/test_structure.py` enforces both rules.
- Domain and application code must not import Kivy.
- UI code consumes backend workflows only through the `clients/` directory of its mirrored
  frontend feature. FastAPI feature controllers own service coordination; only desktop bootstrap
  may start the embedded API host.
- Configuration belongs in `default.cfg`, the example cfg, and `Settings`/loader together.
- New persisted editor data must remain backward-compatible and include a version number.
- Imported files belong in the configured data directory, never inside the source tree.
- Destructive UI actions use red and should not silently delete managed source assets.
- Group dense actions into toolboxes or scrollable/stacked layouts. Validate both the 200% laptop
  profile and the 100% Full-HD profile, including a live dropdown scale change.

## Standard workflow

```bash
bash .agents/scripts/doctor.sh
bash .agents/scripts/check-all.sh
```

For frontend work, also run a real Kivy event loop for at least one second on the affected
screen. Compilation alone does not catch deferred layout and TabbedPanel errors.

## Handoff checklist

- State the user-visible outcome first.
- List validation actually run.
- Note any non-fatal platform warning separately from application failures.
- Update `PROJECT_CACHE.md` and `DECISIONS.md` if assumptions changed.
- Do not claim the UI was tested unless the event loop reached and exited its main loop.
