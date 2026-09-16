from dataclasses import dataclass

from project_planner.core.domain.links.ProjectLink import ProjectLink
from project_planner.core.domain.projects.Project import Project


@dataclass(frozen=True, slots=True)
class ResolvedProjectLink:
    link: ProjectLink
    other_project: Project | None
    outgoing: bool
