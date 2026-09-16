from collections.abc import Sequence

from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.Project import Project
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus
from project_planner.core.ports.ProjectRepository import ProjectRepository


class ProjectService:
    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    def create(
        self,
        title: str,
        *,
        description: str = "",
        status: ProjectStatus = ProjectStatus.IDEA,
        planning_method: PlanningMethod = PlanningMethod.CUSTOM,
        parent_id: str | None = None,
    ) -> Project:
        if parent_id is not None:
            self.require(parent_id)
        project = Project(
            title=title.strip(),
            description=description.strip(),
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
        )
        self._projects.save(project)
        return project

    def update(
        self,
        project_id: str,
        *,
        title: str,
        description: str,
        status: ProjectStatus,
        planning_method: PlanningMethod,
        parent_id: str | None,
    ) -> Project:
        current = self.require(project_id)
        self._validate_parent(project_id, parent_id)
        updated = current.revise(
            title=title.strip(),
            description=description.strip(),
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
        )
        self._projects.save(updated)
        return updated

    def require(self, project_id: str) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise LookupError(f"Project {project_id!r} does not exist")
        return project

    def list_all(self) -> Sequence[Project]:
        return self._projects.list_all()

    def delete(self, project_id: str) -> None:
        self.require(project_id)
        self._projects.delete(project_id)

    def _validate_parent(self, project_id: str, parent_id: str | None) -> None:
        visited = {project_id}
        current_id = parent_id
        while current_id is not None:
            if current_id in visited:
                raise ValueError("Project hierarchy must not contain a cycle")
            visited.add(current_id)
            current_id = self.require(current_id).parent_id
