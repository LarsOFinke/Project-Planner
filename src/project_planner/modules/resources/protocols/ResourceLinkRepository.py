from collections.abc import Sequence
from typing import Protocol

from project_planner.modules.resources.entities.ResourceLink import ResourceLink


class ResourceLinkRepository(Protocol):
    def save(self, link: ResourceLink) -> None: ...
    def list_for_project(self, project_id: str) -> Sequence[ResourceLink]: ...
    def delete(self, link_id: str) -> None: ...
