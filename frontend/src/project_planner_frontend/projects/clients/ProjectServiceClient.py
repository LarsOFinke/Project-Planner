from collections.abc import Sequence

from project_planner.modules.projects.entities.Project import Project
from project_planner_frontend.api.ApiTransport import ApiTransport


class ProjectServiceClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def require(self, project_id: str) -> Project:
        return self._transport.model(Project, "GET", f"/projects/{project_id}")

    def list_all(self) -> Sequence[Project]:
        return self._transport.model(list[Project], "GET", "/projects")

    def delete(self, project_id: str) -> None:
        self._transport.request("DELETE", f"/projects/{project_id}")

    def assign_category(self, project_id: str, category_id: str | None) -> Project:
        return self._transport.model(
            Project,
            "PUT",
            f"/projects/{project_id}/category",
            payload={"category_id": category_id},
        )
