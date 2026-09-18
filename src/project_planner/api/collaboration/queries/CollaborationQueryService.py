from collections import Counter

from project_planner.api.collaboration.dtos.ProjectLinkTarget import ProjectLinkTarget
from project_planner.api.collaboration.dtos.ResolvedProjectLink import ResolvedProjectLink
from project_planner.modules.links.protocols.ProjectLinkRepository import ProjectLinkRepository
from project_planner.modules.projects.protocols.ProjectRepository import ProjectRepository


class CollaborationQueryService:
    def __init__(self, links: ProjectLinkRepository, projects: ProjectRepository) -> None:
        self._links = links
        self._projects = projects

    def available_targets(self, project_id: str) -> tuple[ProjectLinkTarget, ...]:
        projects = tuple(
            project for project in self._projects.list_all() if project.id != project_id
        )
        counts = Counter(project.title for project in projects)
        return tuple(
            ProjectLinkTarget(
                project.id,
                (
                    project.title
                    if counts[project.title] == 1
                    else f"{project.title} · {project.id[:8]}"
                ),
            )
            for project in sorted(projects, key=lambda item: (item.title.casefold(), item.id))
        )

    def list_resolved(self, project_id: str) -> tuple[ResolvedProjectLink, ...]:
        projects = {project.id: project for project in self._projects.list_all()}
        resolved: list[ResolvedProjectLink] = []
        for link in self._links.list_for_project(project_id):
            outgoing = link.source_id == project_id
            other_id = link.target_id if outgoing else link.source_id
            resolved.append(ResolvedProjectLink(link, projects.get(other_id), outgoing))
        return tuple(resolved)
