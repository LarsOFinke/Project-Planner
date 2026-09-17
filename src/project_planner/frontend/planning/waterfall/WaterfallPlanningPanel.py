from kivy.uix.boxlayout import BoxLayout

from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectWorkflowService import ProjectWorkflowService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.application.waterfall.WaterfallTaskService import WaterfallTaskService
from project_planner.frontend.phases.PhasePlanningPanel import PhasePlanningPanel
from project_planner.frontend.planning.waterfall.WaterfallTimelinePanel import (
    WaterfallTimelinePanel,
)
from project_planner.frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel


class WaterfallPlanningPanel(BoxLayout):
    def __init__(
        self,
        phases: PhaseService,
        workflows: ProjectWorkflowService,
        tasks: WaterfallTaskService,
        todos: TodoService,
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._phase_panel = PhasePlanningPanel(phases, workflows, tasks, todos)
        self._timeline = WaterfallTimelinePanel(phases, tasks)
        self.add_widget(
            SimpleTabbedPanel({"Phases & Tasks": self._phase_panel, "Timeline": self._timeline})
        )

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._phase_panel.show_context(project_id, section_id)
        self._timeline.show_context(project_id, section_id)

    def refresh(self) -> None:
        self._phase_panel.refresh()
        self._timeline.refresh()
