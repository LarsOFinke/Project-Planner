from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import Metrics

from project_planner.core.bootstrap.container_builder import build_container
from project_planner.core.configuration.settings import Settings
from project_planner.frontend.shared.theme import NAVY_950
from project_planner.frontend.shell.project_planner_root import ProjectPlannerRoot

_BASE_DENSITY = Metrics.density


class ProjectPlannerApp(App):
    title = "Project Planner 0.1"

    def __init__(self, settings: Settings, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._settings = settings

    def build(self) -> ProjectPlannerRoot:
        Metrics.density = _BASE_DENSITY * self._settings.ui_scale
        Window.size = (self._settings.window_width, self._settings.window_height)
        Window.clearcolor = NAVY_950
        return ProjectPlannerRoot(build_container(self._settings))
