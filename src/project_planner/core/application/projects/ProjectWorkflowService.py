from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectService import ProjectService
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.Project import Project
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus


class ProjectWorkflowService:
    def __init__(self, projects: ProjectService, phases: PhaseService) -> None:
        self._projects = projects
        self._phases = phases

    def create_project(
        self,
        title: str,
        *,
        description: str = "",
        status: ProjectStatus = ProjectStatus.IDEA,
        planning_method: PlanningMethod = PlanningMethod.CUSTOM,
        parent_id: str | None = None,
    ) -> Project:
        project = self._projects.create(
            title,
            description=description,
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
        )
        self._phases.initialize(project.id, project.planning_method)
        return project

    def update_project(
        self,
        project_id: str,
        *,
        title: str,
        description: str,
        status: ProjectStatus,
        planning_method: PlanningMethod,
        parent_id: str | None,
    ) -> Project:
        previous = self._projects.require(project_id)
        project = self._projects.update(
            project_id,
            title=title,
            description=description,
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
        )
        if (
            previous.planning_method != project.planning_method
            and not self._phases.list_for_project(project.id)
        ):
            self._phases.initialize(project.id, project.planning_method)
        return project

    def reset_phase_plan(self, project_id: str) -> None:
        project = self._projects.require(project_id)
        self._phases.initialize(project.id, project.planning_method)
