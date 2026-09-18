from collections.abc import Sequence

from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory
from project_planner_frontend.api.ApiTransport import ApiTransport


class ProjectCategoryClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def create(self, name: str) -> ProjectCategory:
        return self._transport.model(
            ProjectCategory, "POST", "/project-categories", payload={"name": name}
        )

    def require(self, category_id: str) -> ProjectCategory:
        return self._transport.model(ProjectCategory, "GET", f"/project-categories/{category_id}")

    def list_all(self) -> Sequence[ProjectCategory]:
        return self._transport.model(list[ProjectCategory], "GET", "/project-categories")

    def rename(self, category_id: str, name: str) -> ProjectCategory:
        return self._transport.model(
            ProjectCategory,
            "PUT",
            f"/project-categories/{category_id}",
            payload={"name": name},
        )

    def delete(self, category_id: str) -> None:
        self._transport.request("DELETE", f"/project-categories/{category_id}")
