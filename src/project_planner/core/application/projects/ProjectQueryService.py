from project_planner.core.application.projects.models.ProjectChoice import ProjectChoice
from project_planner.core.application.projects.models.ProjectOverview import ProjectOverview
from project_planner.core.application.projects.models.ProjectTreeItem import ProjectTreeItem
from project_planner.core.application.projects.project_choice_builder import (
    build_project_choices,
)
from project_planner.core.application.projects.ProjectService import ProjectService
from project_planner.core.domain.projects.Project import Project


class ProjectQueryService:
    def __init__(self, projects: ProjectService) -> None:
        self._projects = projects

    def get_overview(self, project_id: str) -> ProjectOverview:
        project = self._projects.require(project_id)
        projects = tuple(self._projects.list_all())
        excluded_ids = self._descendant_ids(project_id, projects) | {project_id}
        candidates = tuple(candidate for candidate in projects if candidate.id not in excluded_ids)
        return ProjectOverview(
            project=project,
            parent_choices=build_project_choices(candidates, include_empty=True),
        )

    def list_choices(self, *, exclude_id: str | None = None) -> tuple[ProjectChoice, ...]:
        projects = tuple(
            project for project in self._projects.list_all() if project.id != exclude_id
        )
        return build_project_choices(projects)

    def list_tree(self) -> tuple[ProjectTreeItem, ...]:
        projects = tuple(self._projects.list_all())
        by_parent: dict[str | None, list[Project]] = {}
        for project in projects:
            by_parent.setdefault(project.parent_id, []).append(project)
        for children in by_parent.values():
            children.sort(key=lambda item: (item.title.casefold(), item.id))

        items: list[ProjectTreeItem] = []
        visited: set[str] = set()

        def append_children(parent_id: str | None, depth: int) -> None:
            for project in by_parent.get(parent_id, []):
                if project.id in visited:
                    continue
                visited.add(project.id)
                items.append(ProjectTreeItem(project, depth))
                append_children(project.id, depth + 1)

        append_children(None, 0)
        for project in sorted(projects, key=lambda item: (item.title.casefold(), item.id)):
            if project.id not in visited:
                visited.add(project.id)
                items.append(ProjectTreeItem(project, 0))
                append_children(project.id, 1)
        return tuple(items)

    @staticmethod
    def _descendant_ids(project_id: str, projects: tuple[Project, ...]) -> set[str]:
        children: dict[str, list[str]] = {}
        for project in projects:
            if project.parent_id is not None:
                children.setdefault(project.parent_id, []).append(project.id)
        descendants: set[str] = set()
        pending = list(children.get(project_id, []))
        while pending:
            child_id = pending.pop()
            if child_id in descendants:
                continue
            descendants.add(child_id)
            pending.extend(children.get(child_id, []))
        return descendants
