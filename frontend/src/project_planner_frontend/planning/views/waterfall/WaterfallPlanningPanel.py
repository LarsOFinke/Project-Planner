from kivy.uix.boxlayout import BoxLayout

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.waterfall.PhasePlanningPanel import PhasePlanningPanel
from project_planner_frontend.planning.views.waterfall.WaterfallTimelinePanel import (
    WaterfallTimelinePanel,
)
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.shared.background import run_background
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
        self._phases = phases
        self._tasks = tasks
        self._load_generation = 0
        self.add_widget(
            SimpleTabbedPanel({"Phases & Tasks": self._phase_panel, "Timeline": self._timeline})
        )

    def show_context(self, project_id: str, section_id: str | None = None) -> None:
        self._phase_panel.show_context(project_id, section_id)
        self._timeline.show_context(project_id, section_id)

    def show_context_async(self, project_id: str, section_id: str | None = None) -> None:
        self._load_generation += 1
        generation = self._load_generation

        def fetch() -> tuple[list[Phase], dict[str, list[WaterfallTask]]]:
            phases = list(self._phases.list_for_context(project_id, section_id))
            tasks = {phase.id: list(self._tasks.list_for_phase(phase.id)) for phase in phases}
            return phases, tasks

        def display(result: tuple[list[Phase], dict[str, list[WaterfallTask]]]) -> None:
            if generation != self._load_generation:
                return
            phases, tasks = result
            self._phase_panel.show_fetched(project_id, section_id, phases, tasks)
            self._timeline.show_fetched(project_id, section_id, phases, tasks)

        run_background(fetch, display)

    def refresh(self) -> None:
        self._phase_panel.refresh()
        self._timeline.refresh()
