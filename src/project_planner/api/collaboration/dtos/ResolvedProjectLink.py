from dataclasses import dataclass

from project_planner.modules.links.entities.ProjectLink import ProjectLink
from project_planner.modules.projects.entities.Project import Project


@dataclass(frozen=True, slots=True)
class ResolvedProjectLink:
    link: ProjectLink
    other_project: Project | None
    outgoing: bool
