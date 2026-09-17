from collections.abc import Callable

from kivy.uix.boxlayout import BoxLayout

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot


class ProjectPlannerHost(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
        ui_scale: float,
        fullscreen: bool,
        on_scale_change: Callable[[float], None],
        on_fullscreen_change: Callable[[bool], None],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._container = container
        self._on_scale_change = on_scale_change
        self._fullscreen = fullscreen
        self._on_fullscreen_change = on_fullscreen_change
        self._planner_root: ProjectPlannerRoot | None = None
        self.rebuild(ui_scale)

    def rebuild(self, ui_scale: float) -> None:
        selected_id = None
        if self._planner_root is not None:
            selected_id = self._planner_root.browser.selected_id
            self._planner_root.dispose()
        self.clear_widgets()
        self._planner_root = ProjectPlannerRoot(
            self._container,
            ui_scale,
            self._fullscreen,
            self._on_scale_change,
            self._change_fullscreen,
        )
        self.add_widget(self._planner_root)
        if selected_id is not None:
            self._planner_root.browser.select(selected_id)

    def dispose(self) -> None:
        if self._planner_root is not None:
            self._planner_root.dispose()

    def _change_fullscreen(self, fullscreen: bool) -> None:
        self._fullscreen = fullscreen
        self._on_fullscreen_change(fullscreen)
