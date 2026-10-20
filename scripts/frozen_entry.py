"""Start the packaged desktop application or check its bundled dependencies."""

import os
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    os.environ.setdefault("KIVY_NO_ARGS", "1")
    if sys.argv[1:] in (["--check-imports"], ["--smoke-ui"]):
        from project_planner_frontend.bootstrap.clipboard_bootstrap import configure_clipboard
        from project_planner_frontend.bootstrap.input_bootstrap import configure_mouse_input

        configure_clipboard()
        configure_mouse_input()
        from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp

        from project_planner.api.http.app_factory import create_app
        from project_planner.shared.settings.settings_loader import load_settings

        with TemporaryDirectory(prefix="project-planner-smoke-") as directory:
            settings = replace(
                load_settings(),
                database_path=Path(directory) / "planner.sqlite3",
                data_directory=Path(directory) / "data",
                database_url=None,
            )
            create_app(settings)
            if sys.argv[1:] == ["--smoke-ui"]:
                from kivy.clock import Clock

                app = ProjectPlannerApp(replace(settings, fullscreen=False, ui_scale=2.0))
                Clock.schedule_once(lambda _dt: app.stop(), 2.0)
                app.run()
                print("Project Planner frozen UI event loop OK")
            else:
                print("Project Planner imports and database migrations OK")
    else:
        from project_planner_frontend.main import main as run_app

        run_app()


if __name__ == "__main__":
    main()
