from collections import Counter
from collections.abc import Sequence

from project_planner.core.application.projects.models.ProjectChoice import ProjectChoice
from project_planner.core.domain.projects.Project import Project


def build_project_choices(
    projects: Sequence[Project], *, include_empty: bool = False
) -> tuple[ProjectChoice, ...]:
    counts = Counter(project.title for project in projects)
    choices = [ProjectChoice(None, "No parent")] if include_empty else []
    for project in sorted(projects, key=lambda item: (item.title.casefold(), item.id)):
        label = project.title
        if counts[project.title] > 1:
            label = f"{label} · {project.id[:8]}"
        choices.append(ProjectChoice(project.id, label))
    return tuple(choices)
