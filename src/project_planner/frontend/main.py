from project_planner.core.configuration.settings_loader import load_settings
from project_planner.frontend.bootstrap.clipboard_bootstrap import configure_clipboard

configure_clipboard()


def main() -> None:
    from project_planner.frontend.application.ProjectPlannerApp import ProjectPlannerApp

    ProjectPlannerApp(load_settings()).run()


if __name__ == "__main__":
    main()
