# Project Planner agent instructions

Start with `.agents/ONBOARDING.md`, then read `.agents/PROJECT_CACHE.md`.

Keep the cache current when architecture, commands, persistence formats, configuration, or
known issues change. Run `bash .agents/scripts/check-all.sh` before handing off code changes.
Use `.agents/debugging/README.md` when diagnosing startup, UI, database, or environment issues.

Project invariants:

- every source class has its own PascalCase file matching the class name exactly;
- `frontend` may depend on `core`, never the reverse;
- use Python 3.11–3.13 because Kivy 2.3.1 is incompatible with this machine's Python 3.14;
- preserve local user data and existing SQLite compatibility;
- keep the 200% UI scale usable and verify Kivy changes with a real event-loop smoke test.
