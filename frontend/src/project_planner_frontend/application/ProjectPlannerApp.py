from dataclasses import replace

from kivy.app import App
from kivy.base import ExceptionManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.metrics import Metrics

from project_planner.api.http.ApiServer import ApiServer
from project_planner.shared.settings.Settings import Settings
from project_planner.shared.settings.settings_loader import save_fullscreen, save_ui_scale
from project_planner_frontend.api.ProjectPlannerApi import ProjectPlannerApi
from project_planner_frontend.application.ProjectPlannerHost import ProjectPlannerHost
from project_planner_frontend.errors.ApplicationExceptionHandler import (
    ApplicationExceptionHandler,
)
from project_planner_frontend.shared.theme import NAVY_950

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
        Window.fullscreen = "auto" if self._settings.fullscreen else False
        Window.clearcolor = NAVY_950
        self._api_server = None
        try:
            if self._settings.api_url is None:
                self._api_server = ApiServer(self._settings)
                self._api_server.start()
                api_url = self._api_server.base_url
            else:
                api_url = self._settings.api_url
            self._clients = ProjectPlannerApi.connect(api_url)
        except Exception:
            if self._api_server is not None:
                self._api_server.stop()
            raise
        self._exception_handler = ApplicationExceptionHandler(self._clients.issues)
        ExceptionManager.add_handler(self._exception_handler)
        self._host = ProjectPlannerHost(
            self._clients,
            self._settings.autosave_seconds,
            self._settings.ui_scale,
            self._settings.fullscreen,
            self._change_ui_scale,
            self._change_fullscreen,
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

    def _change_fullscreen(self, fullscreen: bool) -> None:
        if fullscreen == self._settings.fullscreen:
            return
        self._settings = replace(self._settings, fullscreen=fullscreen)
        try:
            save_fullscreen(fullscreen)
        except OSError as error:
            Logger.warning("ProjectPlanner: Could not save fullscreen setting: %s", error)
        Window.fullscreen = "auto" if fullscreen else False

    def _rebuild_ui(self, _elapsed: float) -> None:
        self._scale_rebuild_event = None
        self._host.rebuild(self._pending_ui_scale)

    def on_stop(self) -> None:
        try:
            if hasattr(self, "_host"):
                self._host.dispose()
        finally:
            if hasattr(self, "_exception_handler"):
                ExceptionManager.remove_handler(self._exception_handler)
            if hasattr(self, "_clients"):
                self._clients.close()
            if getattr(self, "_api_server", None) is not None:
                self._api_server.stop()
