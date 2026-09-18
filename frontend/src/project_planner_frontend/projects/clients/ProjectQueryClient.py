from project_planner.api.projects.dtos.ProjectChoice import ProjectChoice
from project_planner.api.projects.dtos.ProjectDirectorySection import ProjectDirectorySection
from project_planner.api.projects.dtos.ProjectOverview import ProjectOverview
from project_planner.api.projects.dtos.ProjectTreeItem import ProjectTreeItem
from project_planner_frontend.api.ApiTransport import ApiTransport


class ProjectQueryClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def get_overview(self, project_id: str) -> ProjectOverview:
        return self._transport.model(ProjectOverview, "GET", f"/projects/{project_id}/overview")

    def list_choices(self, *, exclude_id: str | None = None) -> tuple[ProjectChoice, ...]:
        return self._transport.model(
            tuple[ProjectChoice, ...],
            "GET",
            "/project-choices",
            params={"exclude_id": exclude_id},
        )

    def list_tree(self) -> tuple[ProjectTreeItem, ...]:
        return self._transport.model(tuple[ProjectTreeItem, ...], "GET", "/project-tree")

    def list_directory(self) -> tuple[ProjectDirectorySection, ...]:
        return self._transport.model(
            tuple[ProjectDirectorySection, ...], "GET", "/project-directory"
        )
