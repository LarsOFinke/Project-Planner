from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import date

from project_planner.modules.planning.services.PhaseService import PhaseService
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.modules.projects.services.ProjectService import ProjectService


class ProjectWorkflowService:
    def __init__(
        self,
        projects: ProjectService,
        phases: PhaseService,
        transaction: Callable[[], AbstractContextManager[None]],
    ) -> None:
        self._projects = projects
        self._phases = phases
        self._transaction = transaction

    def create_project(
        self,
        title: str,
        *,
        description: str = "",
        status: ProjectStatus = ProjectStatus.IDEA,
        planning_method: PlanningMethod = PlanningMethod.CUSTOM,
        parent_id: str | None = None,
        category_id: str | None = None,
        start_date: date | None = None,
        target_date: date | None = None,
        owner: str = "",
        assignee: str = "",
        notes: str = "",
    ) -> Project:
        with self._transaction():
            project = self._projects.create(
                title,
                description=description,
                status=status,
                planning_method=planning_method,
                parent_id=parent_id,
                category_id=category_id,
                start_date=start_date,
                target_date=target_date,
                owner=owner,
                assignee=assignee,
                notes=notes,
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
        start_date: date | None = None,
        target_date: date | None = None,
        owner: str = "",
        assignee: str = "",
        notes: str = "",
    ) -> Project:
        with self._transaction():
            previous = self._projects.require(project_id)
            project = self._projects.update(
                project_id,
                title=title,
                description=description,
                status=status,
                planning_method=planning_method,
                parent_id=parent_id,
                start_date=start_date,
                target_date=target_date,
                owner=owner,
                assignee=assignee,
                notes=notes,
            )
            if (
                previous.planning_method != project.planning_method
                and not self._phases.list_for_context(project.id)
                and project.planning_method is PlanningMethod.WATERFALL
            ):
                self._phases.initialize_waterfall(project.id)
        return project

    def reset_phase_plan(self, project_id: str) -> None:
        with self._transaction():
            project = self._projects.require(project_id)
            if project.planning_method is PlanningMethod.WATERFALL:
                self._phases.reset_waterfall(project.id)
