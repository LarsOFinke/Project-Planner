from dataclasses import dataclass

from project_planner.core.application.projects.models.ProjectChoice import ProjectChoice
from project_planner.core.domain.projects.Project import Project


@dataclass(frozen=True, slots=True)
class ProjectOverview:
    project: Project
    parent_choices: tuple[ProjectChoice, ...]
