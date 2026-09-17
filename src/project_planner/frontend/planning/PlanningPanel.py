from kivy.uix.boxlayout import BoxLayout

from project_planner.core.application.agile.AgilePlanningService import AgilePlanningService
from project_planner.core.application.custom.SectionService import SectionService
from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectService import ProjectService
from project_planner.core.application.projects.ProjectWorkflowService import ProjectWorkflowService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.application.waterfall.WaterfallTaskService import WaterfallTaskService
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.frontend.planning.agile.AgilePlanningPanel import AgilePlanningPanel
from project_planner.frontend.planning.custom.CustomPlanningPanel import CustomPlanningPanel
from project_planner.frontend.planning.waterfall.WaterfallPlanningPanel import (
    WaterfallPlanningPanel,
)
from project_planner.frontend.shared.theme import NAVY_900, empty_state_label, paint_background


class PlanningPanel(BoxLayout):
    def __init__(
        self,
        projects: ProjectService,
        agile: AgilePlanningService,
        phases: PhaseService,
        workflows: ProjectWorkflowService,
        sections: SectionService,
        tasks: WaterfallTaskService,
        todos: TodoService,
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._projects = projects
        self._agile = agile
        self._phases = phases
        self._workflows = workflows
        self._sections = sections
        self._tasks = tasks
        self._todos = todos
        self._project_id: str | None = None
        paint_background(self, NAVY_900)
        self._show_empty("Select a project to open its roadmap.")

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        project = self._projects.require(project_id)
        self.clear_widgets()
        if project.planning_method is PlanningMethod.AGILE:
            panel = AgilePlanningPanel(self._agile)
            panel.show_context(project_id)
        elif project.planning_method is PlanningMethod.WATERFALL:
            panel = WaterfallPlanningPanel(self._phases, self._workflows, self._tasks, self._todos)
            panel.show_context(project_id)
        else:
            panel = CustomPlanningPanel(
                self._sections,
                self._agile,
                self._phases,
                self._workflows,
                self._tasks,
                self._todos,
            )
            panel.show_project(project_id)
        self.add_widget(panel)

    def refresh(self) -> None:
        if self._project_id:
            self.show_project(self._project_id)

    def _show_empty(self, message: str) -> None:
        self.clear_widgets()
        self.add_widget(empty_state_label(message, 96))
