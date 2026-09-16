from collections.abc import Sequence
from typing import Protocol

from project_planner.core.domain.links.project_link import ProjectLink


class ProjectLinkRepository(Protocol):
    def save(self, link: ProjectLink) -> None: ...
    def list_for_project(self, project_id: str) -> Sequence[ProjectLink]: ...
    def delete(self, source_id: str, target_id: str, relation: str) -> None: ...
