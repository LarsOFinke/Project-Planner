from project_planner.core.configuration.settings_loader import load_settings
from project_planner.frontend.application.project_planner_app import ProjectPlannerApp


def main() -> None:
    ProjectPlannerApp(load_settings()).run()


if __name__ == "__main__":
    main()
