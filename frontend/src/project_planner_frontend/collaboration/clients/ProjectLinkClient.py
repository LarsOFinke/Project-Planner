from collections.abc import Sequence

from project_planner.api.collaboration.dtos.ProjectLinkTarget import ProjectLinkTarget
from project_planner.api.collaboration.dtos.ResolvedProjectLink import ResolvedProjectLink
from project_planner.modules.links.entities.ProjectLink import ProjectLink
from project_planner_frontend.api.ApiTransport import ApiTransport


class ProjectLinkClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def add(
        self, source_id: str, target_id: str, relation: str = "related", note: str = ""
    ) -> ProjectLink:
        return self._transport.model(
            ProjectLink,
            "POST",
            f"/projects/{source_id}/project-links",
            payload={"target_id": target_id, "relation": relation, "note": note},
        )

    def list_for_project(self, project_id: str) -> Sequence[ProjectLink]:
        return self._transport.model(
            list[ProjectLink], "GET", f"/projects/{project_id}/project-links"
        )

    def available_targets(self, project_id: str) -> tuple[ProjectLinkTarget, ...]:
        return self._transport.model(
            tuple[ProjectLinkTarget, ...],
            "GET",
            f"/projects/{project_id}/project-link-targets",
        )

    def list_resolved(self, project_id: str) -> tuple[ResolvedProjectLink, ...]:
        return self._transport.model(
            tuple[ResolvedProjectLink, ...],
            "GET",
            f"/projects/{project_id}/project-links",
            params={"resolved": True},
        )

    def remove(self, link: ProjectLink) -> None:
        self._transport.request(
            "DELETE",
            "/project-links",
            params={
                "source_id": link.source_id,
                "target_id": link.target_id,
                "relation": link.relation,
            },
        )
