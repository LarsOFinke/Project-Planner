from collections.abc import Sequence

from project_planner.core.application.links.models.ResolvedProjectLink import (
    ResolvedProjectLink,
)
from project_planner.core.application.projects.models.ProjectChoice import ProjectChoice
from project_planner.core.application.projects.project_choice_builder import (
    build_project_choices,
)
from project_planner.core.domain.links.ProjectLink import ProjectLink
from project_planner.core.ports.ProjectLinkRepository import ProjectLinkRepository
from project_planner.core.ports.ProjectRepository import ProjectRepository


class ProjectLinkService:
    def __init__(
        self, links: ProjectLinkRepository, projects: ProjectRepository
    ) -> None:
        self._links = links
        self._projects = projects

    def add(
        self,
        source_id: str,
        target_id: str,
        relation: str = "related",
        note: str = "",
    ) -> ProjectLink:
        if self._projects.get(source_id) is None or self._projects.get(target_id) is None:
            raise LookupError("Both linked projects must exist")
        link = ProjectLink(source_id, target_id, relation.strip(), note.strip())
        self._links.save(link)
        return link

    def list_for_project(self, project_id: str) -> Sequence[ProjectLink]:
        return self._links.list_for_project(project_id)

    def available_targets(self, project_id: str) -> tuple[ProjectChoice, ...]:
        projects = tuple(
            project
            for project in self._projects.list_all()
            if project.id != project_id
        )
        return build_project_choices(projects)

    def list_resolved(self, project_id: str) -> tuple[ResolvedProjectLink, ...]:
        projects = {project.id: project for project in self._projects.list_all()}
        resolved: list[ResolvedProjectLink] = []
        for link in self._links.list_for_project(project_id):
            outgoing = link.source_id == project_id
            other_id = link.target_id if outgoing else link.source_id
            resolved.append(ResolvedProjectLink(link, projects.get(other_id), outgoing))
        return tuple(resolved)

    def remove(self, link: ProjectLink) -> None:
        self._links.delete(link.source_id, link.target_id, link.relation)
