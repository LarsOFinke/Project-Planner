from kivy.uix.boxlayout import BoxLayout

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.planning.views.agile.AgilePlanningPanel import AgilePlanningPanel
from project_planner_frontend.planning.views.custom.CustomPlanningPanel import CustomPlanningPanel
from project_planner_frontend.planning.views.waterfall.WaterfallPlanningPanel import (
    WaterfallPlanningPanel,
)
from project_planner_frontend.projects.clients.ProjectServiceClient import ProjectServiceClient
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.theme import NAVY_900, empty_state_label, paint_background


class PlanningPanel(BoxLayout):
    def __init__(
        self,
        projects: ProjectServiceClient,
        agile: AgileClient,
        phases: PhaseClient,
        workflows: ProjectWorkflowClient,
        sections: SectionClient,
        tasks: WaterfallTaskClient,
        todos: TodoClient,
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
        self._load_generation = 0
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

    def show_project_async(self, project_id: str) -> None:
        self._project_id = project_id
        self._load_generation += 1
        generation = self._load_generation
        self._show_empty("Loading roadmap...")

        def display(project: object) -> None:
            if generation != self._load_generation:
                return
            self.clear_widgets()
            if project.planning_method is PlanningMethod.AGILE:
                panel = AgilePlanningPanel(self._agile)
                panel.show_context_async(project_id)
            elif project.planning_method is PlanningMethod.WATERFALL:
                panel = WaterfallPlanningPanel(
                    self._phases, self._workflows, self._tasks, self._todos
                )
                panel.show_context_async(project_id)
            else:
                panel = CustomPlanningPanel(
                    self._sections,
                    self._agile,
                    self._phases,
                    self._workflows,
                    self._tasks,
                    self._todos,
                )
                panel.show_project_async(project_id)
            self.add_widget(panel)

        run_background(lambda: self._projects.require(project_id), display)

    def refresh(self) -> None:
        if self._project_id:
            self.show_project(self._project_id)

    def clear_project(self) -> None:
        self._load_generation += 1
        self._project_id = None
        self._show_empty("Select a project to open its roadmap.")

    def _show_empty(self, message: str) -> None:
        self.clear_widgets()
        self.add_widget(empty_state_label(message, 96))
