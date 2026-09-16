from collections.abc import Sequence

from project_planner.core.domain.links.project_link import ProjectLink
from project_planner.core.ports.project_link_repository import ProjectLinkRepository
from project_planner.core.ports.project_repository import ProjectRepository


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

    def remove(self, link: ProjectLink) -> None:
        self._links.delete(link.source_id, link.target_id, link.relation)
