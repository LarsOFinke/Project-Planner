from project_planner.core.application.agile.AgilePlanningService import AgilePlanningService
from project_planner.core.application.artifacts.ArtifactService import ArtifactService
from project_planner.core.application.artifacts.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.core.application.artifacts.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner.core.application.assets.ImageAssetService import ImageAssetService
from project_planner.core.application.custom.SectionService import SectionService
from project_planner.core.application.links.ProjectLinkService import ProjectLinkService
from project_planner.core.application.phases.PhaseService import PhaseService
from project_planner.core.application.projects.ProjectQueryService import ProjectQueryService
from project_planner.core.application.projects.ProjectService import ProjectService
from project_planner.core.application.projects.ProjectWorkflowService import (
    ProjectWorkflowService,
)
from project_planner.core.application.resources.ResourceLinkService import ResourceLinkService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.application.waterfall.WaterfallTaskService import WaterfallTaskService
from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.core.configuration.Settings import Settings
from project_planner.core.configuration.settings_loader import load_settings
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.seeds.SeedRunner import SeedRunner
from project_planner.core.infrastructure.repositories.SQLAlchemyAgileRepository import (
    SQLAlchemyAgileRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyArtifactRepository import (
    SQLAlchemyArtifactRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyPhaseRepository import (
    SQLAlchemyPhaseRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyProjectLinkRepository import (
    SQLAlchemyProjectLinkRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyProjectRepository import (
    SQLAlchemyProjectRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyResourceLinkRepository import (
    SQLAlchemyResourceLinkRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemySectionRepository import (
    SQLAlchemySectionRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyTodoRepository import (
    SQLAlchemyTodoRepository,
)
from project_planner.core.infrastructure.repositories.SQLAlchemyWaterfallTaskRepository import (
    SQLAlchemyWaterfallTaskRepository,
)


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved = settings or load_settings()
    database = Database(resolved.database_path, resolved.database_url)
    SeedRunner(database).run()
    projects = SQLAlchemyProjectRepository(database)
    phases = SQLAlchemyPhaseRepository(database)
    links = SQLAlchemyProjectLinkRepository(database)
    artifacts = SQLAlchemyArtifactRepository(database)
    todos = SQLAlchemyTodoRepository(database)
    resources = SQLAlchemyResourceLinkRepository(database)
    agile = SQLAlchemyAgileRepository(database)
    sections = SQLAlchemySectionRepository(database)
    waterfall_tasks = SQLAlchemyWaterfallTaskRepository(database)
    project_service = ProjectService(projects)
    phase_service = PhaseService(phases)
    return ApplicationContainer(
        settings=resolved,
        agile=AgilePlanningService(agile),
        projects=project_service,
        project_queries=ProjectQueryService(project_service),
        project_workflows=ProjectWorkflowService(project_service, phase_service),
        phases=phase_service,
        sections=SectionService(sections, phase_service),
        waterfall_tasks=WaterfallTaskService(waterfall_tasks),
        links=ProjectLinkService(links, projects),
        resources=ResourceLinkService(resources),
        todos=TodoService(todos),
        artifacts=ArtifactService(artifacts),
        diagram_documents=DiagramDocumentCodec(),
        workspace_documents=WorkspaceDocumentCodec(),
        images=ImageAssetService(resolved.data_directory),
    )
