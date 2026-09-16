from dataclasses import dataclass

from project_planner.core.domain.projects.Project import Project


@dataclass(frozen=True, slots=True)
class ProjectTreeItem:
    project: Project
    depth: int
