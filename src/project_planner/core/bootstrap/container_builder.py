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
from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.core.configuration.Settings import Settings
from project_planner.core.configuration.settings_loader import load_settings
from project_planner.core.infrastructure.database.SQLiteDatabase import SQLiteDatabase
from project_planner.core.infrastructure.repositories.SQLiteArtifactRepository import (
    SQLiteArtifactRepository,
)
from project_planner.core.infrastructure.repositories.SQLitePhaseRepository import (
    SQLitePhaseRepository,
)
from project_planner.core.infrastructure.repositories.SQLiteProjectLinkRepository import (
    SQLiteProjectLinkRepository,
)
from project_planner.core.infrastructure.repositories.SQLiteProjectRepository import (
    SQLiteProjectRepository,
)


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved = settings or load_settings()
    database = SQLiteDatabase(resolved.database_path)
    projects = SQLiteProjectRepository(database)
    phases = SQLitePhaseRepository(database)
    links = SQLiteProjectLinkRepository(database)
    artifacts = SQLiteArtifactRepository(database)
    project_service = ProjectService(projects)
    phase_service = PhaseService(phases)
    return ApplicationContainer(
        settings=resolved,
        projects=project_service,
        project_queries=ProjectQueryService(project_service),
        project_workflows=ProjectWorkflowService(project_service, phase_service),
        phases=phase_service,
        links=ProjectLinkService(links, projects),
        artifacts=ArtifactService(artifacts),
        diagram_documents=DiagramDocumentCodec(),
        workspace_documents=WorkspaceDocumentCodec(),
        images=ImageAssetService(resolved.data_directory),
    )
