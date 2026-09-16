from dataclasses import replace

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import Metrics

from project_planner.core.bootstrap.container_builder import build_container
from project_planner.core.configuration.Settings import Settings
from project_planner.core.configuration.settings_loader import save_ui_scale
from project_planner.frontend.application.ProjectPlannerHost import ProjectPlannerHost
from project_planner.frontend.shared.theme import NAVY_950

_BASE_DENSITY = Metrics.density


class ProjectPlannerApp(App):
    title = "Project Planner 0.1"

    def __init__(self, settings: Settings, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._settings = settings
        self._pending_ui_scale = settings.ui_scale
        self._scale_rebuild_event = None

    def build(self) -> ProjectPlannerHost:
        Metrics.density = _BASE_DENSITY * self._settings.ui_scale
        Window.size = (self._settings.window_width, self._settings.window_height)
        Window.clearcolor = NAVY_950
        self._host = ProjectPlannerHost(
            build_container(self._settings),
            self._settings.ui_scale,
            self._change_ui_scale,
        )
        return self._host

    def _change_ui_scale(self, ui_scale: float) -> None:
        if ui_scale == self._settings.ui_scale:
            return
        self._settings = replace(self._settings, ui_scale=ui_scale)
        try:
            save_ui_scale(ui_scale)
        except OSError as error:
            Logger.warning("ProjectPlanner: Could not save UI scale: %s", error)
        Metrics.density = _BASE_DENSITY * ui_scale
        self._pending_ui_scale = ui_scale
        if self._scale_rebuild_event is not None:
            self._scale_rebuild_event.cancel()
        self._scale_rebuild_event = Clock.schedule_once(self._rebuild_ui, 0)

    def _rebuild_ui(self, _elapsed: float) -> None:
        self._scale_rebuild_event = None
        self._host.rebuild(self._pending_ui_scale)
