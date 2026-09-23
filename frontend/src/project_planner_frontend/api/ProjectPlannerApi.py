from dataclasses import dataclass

from project_planner.modules.artifacts.services.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.modules.artifacts.services.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner_frontend.api.ApiTransport import ApiTransport
from project_planner_frontend.artifacts.clients.ArtifactClient import ArtifactClient
from project_planner_frontend.artifacts.clients.ImageAssetClient import ImageAssetClient
from project_planner_frontend.bootstrap.http_logging_bootstrap import configure_http_logging
from project_planner_frontend.collaboration.clients.ProjectLinkClient import ProjectLinkClient
from project_planner_frontend.collaboration.clients.ResourceLinkClient import ResourceLinkClient
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.planning.clients.AgileClient import AgileClient
from project_planner_frontend.planning.clients.PhaseClient import PhaseClient
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.planning.clients.WaterfallTaskClient import WaterfallTaskClient
from project_planner_frontend.projects.clients.ProjectCategoryClient import ProjectCategoryClient
from project_planner_frontend.projects.clients.ProjectQueryClient import ProjectQueryClient
from project_planner_frontend.projects.clients.ProjectServiceClient import ProjectServiceClient
from project_planner_frontend.projects.clients.ProjectWorkflowClient import ProjectWorkflowClient
from project_planner_frontend.system.clients.DatabaseTransferClient import DatabaseTransferClient
from project_planner_frontend.system.clients.HealthClient import HealthClient
from project_planner_frontend.system.clients.IssueClient import IssueClient


@dataclass(frozen=True, slots=True)
class ProjectPlannerApi:
    transport: ApiTransport
    agile: AgileClient
    projects: ProjectServiceClient
    project_categories: ProjectCategoryClient
    project_queries: ProjectQueryClient
    project_workflows: ProjectWorkflowClient
    phases: PhaseClient
    sections: SectionClient
    waterfall_tasks: WaterfallTaskClient
    links: ProjectLinkClient
    resources: ResourceLinkClient
    todos: TodoClient
    artifacts: ArtifactClient
    diagram_documents: DiagramDocumentCodec
    workspace_documents: WorkspaceDocumentCodec
    images: ImageAssetClient
    database_transfer: DatabaseTransferClient
    issues: IssueClient
    health: HealthClient

    @classmethod
    def connect(
        cls,
        base_url: str,
        api_token: str | None = None,
        timeout: float = 15.0,
        backup_timeout: float = 120.0,
    ) -> "ProjectPlannerApi":
        configure_http_logging()
        transport = ApiTransport(
            base_url, api_token=api_token, timeout=timeout, backup_timeout=backup_timeout
        )
        return cls(
            transport=transport,
            agile=AgileClient(transport),
            projects=ProjectServiceClient(transport),
            project_categories=ProjectCategoryClient(transport),
            project_queries=ProjectQueryClient(transport),
            project_workflows=ProjectWorkflowClient(transport),
            phases=PhaseClient(transport),
            sections=SectionClient(transport),
            waterfall_tasks=WaterfallTaskClient(transport),
            links=ProjectLinkClient(transport),
            resources=ResourceLinkClient(transport),
            todos=TodoClient(transport),
            artifacts=ArtifactClient(transport),
            diagram_documents=DiagramDocumentCodec(),
            workspace_documents=WorkspaceDocumentCodec(),
            images=ImageAssetClient(transport),
            database_transfer=DatabaseTransferClient(transport),
            issues=IssueClient(transport),
            health=HealthClient(transport),
        )

    def close(self) -> None:
        self.transport.close()
