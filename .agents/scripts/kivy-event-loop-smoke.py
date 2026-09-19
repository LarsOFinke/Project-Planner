import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    args = parser.parse_args()
    with (
        TemporaryDirectory(prefix="project-planner-kivy-home-") as kivy_home,
        TemporaryDirectory(prefix="project-planner-kivy-smoke-") as temporary,
    ):
        os.environ["KIVY_NO_ARGS"] = "1"
        os.environ["KIVY_HOME"] = kivy_home
        from kivy.clock import Clock
        from project_planner_frontend.bootstrap.clipboard_bootstrap import configure_clipboard
        from project_planner_frontend.bootstrap.input_bootstrap import configure_mouse_input

        from project_planner.api.controller_builder import build_controllers
        from project_planner.shared.settings.Settings import Settings

        configure_clipboard()
        configure_mouse_input()

        from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp

        root = Path(temporary)
        settings = Settings(
            database_path=root / "planner.sqlite3",
            data_directory=root / "data",
            window_width=args.width,
            window_height=args.height,
            autosave_seconds=20,
            ui_scale=args.scale,
            fullscreen=False,
        )
        projects, _planning, _collaboration, _artifacts, _system = build_controllers(settings)
        category = projects.create_category("Smoke category")
        project = projects.create_project("Smoke project", category_id=category.id)
        child = projects.create_project(
            "Nested smoke project",
            parent_id=project.id,
            category_id=category.id,
        )
        projects.create_project(
            "Deep smoke project",
            parent_id=child.id,
            category_id=category.id,
        )
        application = ProjectPlannerApp(settings)
        Clock.schedule_once(lambda _elapsed: application.stop(), 1.0)
        application.run()


if __name__ == "__main__":
    main()
