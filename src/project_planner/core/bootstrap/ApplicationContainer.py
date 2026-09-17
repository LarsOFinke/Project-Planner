from dataclasses import dataclass

from project_planner.core.application.artifacts.ArtifactService import ArtifactService
from project_planner.core.application.artifacts.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.core.application.artifacts.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner.core.application.assets.ImageAssetService import ImageAssetService
from project_planner.core.application.links.ProjectLinkService import ProjectLinkService
from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectQueryService import ProjectQueryService
from project_planner.core.application.projects.ProjectService import ProjectService
from project_planner.core.application.projects.ProjectWorkflowService import (
    ProjectWorkflowService,
)
from project_planner.core.application.resources.ResourceLinkService import ResourceLinkService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.configuration.Settings import Settings


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    projects: ProjectService
    project_queries: ProjectQueryService
    project_workflows: ProjectWorkflowService
    phases: PhaseService
    links: ProjectLinkService
    resources: ResourceLinkService
    todos: TodoService
    artifacts: ArtifactService
    diagram_documents: DiagramDocumentCodec
    workspace_documents: WorkspaceDocumentCodec
    images: ImageAssetService
