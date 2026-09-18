from kivy.uix.boxlayout import BoxLayout

from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.waterfall.PhasePlanningPanel import PhasePlanningPanel
from project_planner_frontend.planning.views.waterfall.WaterfallTimelinePanel import (
    WaterfallTimelinePanel,
)
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel


class WaterfallPlanningPanel(BoxLayout):
    def __init__(
        self,
        phases: PhaseClient,
        workflows: ProjectWorkflowClient,
        tasks: WaterfallTaskClient,
        todos: TodoClient,
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
