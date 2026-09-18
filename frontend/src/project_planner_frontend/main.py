from project_planner.shared.settings.settings_loader import load_settings
from project_planner_frontend.bootstrap.clipboard_bootstrap import configure_clipboard
from project_planner_frontend.bootstrap.input_bootstrap import configure_mouse_input

configure_clipboard()
configure_mouse_input()


def main() -> None:
    from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp

    ProjectPlannerApp(load_settings()).run()


if __name__ == "__main__":
    main()
