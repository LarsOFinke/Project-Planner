from collections.abc import Sequence

from project_planner.modules.resources.entities.ResourceLink import ResourceLink
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner_frontend.api.ApiTransport import ApiTransport


class ResourceLinkClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def add(self, project_id: str, title: str, target: str, kind: ResourceLinkKind) -> ResourceLink:
        return self._transport.model(
            ResourceLink,
            "POST",
            f"/projects/{project_id}/resources",
            payload={"title": title, "target": target, "kind": kind},
        )

    def list_for_project(
        self, project_id: str, kind: ResourceLinkKind | None = None
    ) -> Sequence[ResourceLink]:
        return self._transport.model(
            list[ResourceLink],
            "GET",
            f"/projects/{project_id}/resources",
            params={"kind": None if kind is None else kind.value},
        )

    def remove(self, link_id: str) -> None:
        self._transport.request("DELETE", f"/resources/{link_id}")
