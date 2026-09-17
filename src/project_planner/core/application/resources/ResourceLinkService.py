from collections.abc import Sequence
from pathlib import Path

from project_planner.core.domain.resources.ResourceLink import ResourceLink
from project_planner.core.domain.resources.ResourceLinkKind import ResourceLinkKind
from project_planner.core.ports.ResourceLinkRepository import ResourceLinkRepository


class ResourceLinkService:
    def __init__(self, links: ResourceLinkRepository) -> None:
        self._links = links

    def add(self, project_id: str, title: str, target: str, kind: ResourceLinkKind) -> ResourceLink:
        normalized_target = self._target(target, kind)
        link = ResourceLink(project_id, title.strip(), normalized_target, kind)
        self._links.save(link)
        return link

    def list_for_project(
        self, project_id: str, kind: ResourceLinkKind | None = None
    ) -> Sequence[ResourceLink]:
        links = self._links.list_for_project(project_id)
        if kind is None:
            return links
        return [link for link in links if link.kind is kind]

    def remove(self, link_id: str) -> None:
        self._links.delete(link_id)

    @staticmethod
    def _target(target: str, kind: ResourceLinkKind) -> str:
        stripped = target.strip()
        if kind is ResourceLinkKind.FILE:
            return str(Path(stripped).expanduser().resolve(strict=False))
        return stripped
