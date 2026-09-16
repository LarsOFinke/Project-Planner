from collections.abc import Callable

from kivy.uix.boxlayout import BoxLayout

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot


class ProjectPlannerHost(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
        ui_scale: float,
        on_scale_change: Callable[[float], None],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._container = container
        self._on_scale_change = on_scale_change
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
            self._on_scale_change,
        )
        self.add_widget(self._planner_root)
        if selected_id is not None:
            self._planner_root.browser.select(selected_id)
