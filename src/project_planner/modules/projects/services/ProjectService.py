from collections.abc import Sequence
from datetime import date

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.modules.projects.protocols.ProjectCategoryRepository import (
    ProjectCategoryRepository,
)
from project_planner.modules.projects.protocols.ProjectRepository import ProjectRepository


class ProjectService:
    def __init__(
        self,
        projects: ProjectRepository,
        categories: ProjectCategoryRepository,
    ) -> None:
        self._projects = projects
        self._categories = categories

    def create(
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
        if parent_id is not None:
            category_id = self.require(parent_id).category_id
        self._validate_category(category_id)
        project = Project(
            title=title.strip(),
            description=description.strip(),
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
            category_id=category_id,
            start_date=start_date,
            target_date=target_date,
            owner=owner.strip(),
            assignee=assignee.strip(),
            notes=notes.strip(),
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
        start_date: date | None = None,
        target_date: date | None = None,
        owner: str = "",
        assignee: str = "",
        notes: str = "",
    ) -> Project:
        current = self.require(project_id)
        self._validate_parent(project_id, parent_id)
        category_id = current.category_id
        if parent_id is not None:
            category_id = self.require(parent_id).category_id
        updated = current.revise(
            title=title.strip(),
            description=description.strip(),
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
            category_id=category_id,
            start_date=start_date,
            target_date=target_date,
            owner=owner.strip(),
            assignee=assignee.strip(),
            notes=notes.strip(),
        )
        if category_id == current.category_id:
            self._projects.save(updated)
        else:
            projects = tuple(self._projects.list_all())
            self._projects.save_all(self._subtree_updates(updated, projects))
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

    def archive(self, project_id: str) -> Project:
        current = self.require(project_id)
        archived = current.revise(status=ProjectStatus.ARCHIVED)
        self._projects.save(archived)
        return archived

    def move(
        self,
        project_id: str,
        *,
        parent_id: str | None,
        category_id: str | None,
    ) -> Project:
        current = self.require(project_id)
        self._validate_parent(project_id, parent_id)
        if parent_id is not None:
            category_id = self.require(parent_id).category_id
        self._validate_category(category_id)
        projects = tuple(self._projects.list_all())
        moved = current.revise(parent_id=parent_id, category_id=category_id)
        self._projects.save_all(self._subtree_updates(moved, projects))
        return moved

    @classmethod
    def _subtree_updates(
        cls,
        root: Project,
        projects: Sequence[Project],
    ) -> list[Project]:
        descendant_ids = cls._descendant_ids(root.id, projects)
        updates = [root]
        updates.extend(
            project.revise(category_id=root.category_id)
            for project in projects
            if project.id in descendant_ids and project.category_id != root.category_id
        )
        return updates

    def _validate_category(self, category_id: str | None) -> None:
        if category_id is not None and self._categories.get(category_id) is None:
            raise LookupError(f"Project category {category_id!r} does not exist")

    def _validate_parent(self, project_id: str, parent_id: str | None) -> None:
        visited = {project_id}
        current_id = parent_id
        while current_id is not None:
            if current_id in visited:
                raise ValueError("Project hierarchy must not contain a cycle")
            visited.add(current_id)
            current_id = self.require(current_id).parent_id

    @staticmethod
    def _descendant_ids(project_id: str, projects: Sequence[Project]) -> set[str]:
        children_by_parent: dict[str, list[str]] = {}
        for project in projects:
            if project.parent_id is not None:
                children_by_parent.setdefault(project.parent_id, []).append(project.id)
        descendants: set[str] = set()
        pending = [project_id]
        while pending:
            parent_id = pending.pop()
            for child_id in children_by_parent.get(parent_id, []):
                if child_id not in descendants:
                    descendants.add(child_id)
                    pending.append(child_id)
        return descendants
