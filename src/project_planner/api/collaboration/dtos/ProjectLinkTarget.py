from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectLinkTarget:
    project_id: str
    label: str
