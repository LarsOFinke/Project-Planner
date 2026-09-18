from dataclasses import dataclass

from project_planner.modules.projects.entities.Project import Project


@dataclass(frozen=True, slots=True)
class ProjectTreeItem:
    project: Project
    depth: int
