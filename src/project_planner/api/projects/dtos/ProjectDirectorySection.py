from dataclasses import dataclass

from project_planner.api.projects.dtos.ProjectTreeItem import ProjectTreeItem
from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory


@dataclass(frozen=True, slots=True)
class ProjectDirectorySection:
    category: ProjectCategory | None
    projects: tuple[ProjectTreeItem, ...]
