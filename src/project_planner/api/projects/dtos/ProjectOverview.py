from dataclasses import dataclass

from project_planner.api.projects.dtos.ProjectChoice import ProjectChoice
from project_planner.modules.projects.entities.Project import Project


@dataclass(frozen=True, slots=True)
class ProjectOverview:
    project: Project
    parent_choices: tuple[ProjectChoice, ...]
