from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectChoice:
    project_id: str | None
    label: str
