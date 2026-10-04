from types import SimpleNamespace

from project_planner.api.collaboration.queries.CollaborationQueryService import (
    CollaborationQueryService,
)
from project_planner.api.projects.queries.ProjectQueryService import ProjectQueryService
from project_planner.modules.artifacts.repositories.SQLAlchemyArtifactRepository import (
    SQLAlchemyArtifactRepository,
)
from project_planner.modules.artifacts.services.ArtifactService import ArtifactService
from project_planner.modules.artifacts.services.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.modules.artifacts.services.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner.modules.assets.services.ImageAssetService import ImageAssetService
from project_planner.modules.health.repositories.SQLAlchemyIssueLogRepository import (
    SQLAlchemyIssueLogRepository,
)
from project_planner.modules.health.services.IssueLogService import IssueLogService
from project_planner.modules.health.services.SystemHealthService import SystemHealthService
from project_planner.modules.links.repositories.SQLAlchemyProjectLinkRepository import (
    SQLAlchemyProjectLinkRepository,
)
from project_planner.modules.links.services.ProjectLinkService import ProjectLinkService
from project_planner.modules.planning.repositories.SQLAlchemyAgileRepository import (
    SQLAlchemyAgileRepository,
)
from project_planner.modules.planning.repositories.SQLAlchemyPhaseRepository import (
    SQLAlchemyPhaseRepository,
)
from project_planner.modules.planning.repositories.SQLAlchemySectionRepository import (
    SQLAlchemySectionRepository,
)
from project_planner.modules.planning.repositories.SQLAlchemyWaterfallTaskRepository import (
    SQLAlchemyWaterfallTaskRepository,
)
from project_planner.modules.planning.services.AgilePlanningService import AgilePlanningService
from project_planner.modules.planning.services.PhaseService import PhaseService
from project_planner.modules.planning.services.SectionService import SectionService
from project_planner.modules.planning.services.WaterfallTaskService import WaterfallTaskService
from project_planner.modules.projects.repositories.SQLAlchemyProjectCategoryRepository import (
    SQLAlchemyProjectCategoryRepository,
)
from project_planner.modules.projects.repositories.SQLAlchemyProjectRepository import (
    SQLAlchemyProjectRepository,
)
from project_planner.modules.projects.services.ProjectCategoryService import ProjectCategoryService
from project_planner.modules.projects.services.ProjectService import ProjectService
from project_planner.modules.projects.services.ProjectWorkflowService import ProjectWorkflowService
from project_planner.modules.resources.repositories.SQLAlchemyResourceLinkRepository import (
    SQLAlchemyResourceLinkRepository,
)
from project_planner.modules.resources.services.ResourceLinkService import ResourceLinkService
from project_planner.modules.todos.repositories.SQLAlchemyTodoRepository import (
    SQLAlchemyTodoRepository,
)
from project_planner.modules.todos.services.TodoService import TodoService
from project_planner.shared.database.Database import Database
from project_planner.shared.database.seeds.SeedRunner import SeedRunner
from project_planner.shared.settings.Settings import Settings


def build_test_services(settings: Settings) -> SimpleNamespace:
    database = Database(settings.database_path, settings.database_url)
    SeedRunner(database).run()
    projects = SQLAlchemyProjectRepository(database)
    categories = SQLAlchemyProjectCategoryRepository(database)
    phases = SQLAlchemyPhaseRepository(database)
    project_service = ProjectService(projects, categories)
    category_service = ProjectCategoryService(categories)
    phase_service = PhaseService(phases)
    issues = IssueLogService(SQLAlchemyIssueLogRepository(database))
    project_links = SQLAlchemyProjectLinkRepository(database)
    return SimpleNamespace(
        settings=settings,
        agile=AgilePlanningService(SQLAlchemyAgileRepository(database)),
        projects=project_service,
        project_categories=category_service,
        project_queries=ProjectQueryService(project_service, category_service),
        project_workflows=ProjectWorkflowService(
            project_service, phase_service, database.transaction
        ),
        phases=phase_service,
        sections=SectionService(SQLAlchemySectionRepository(database), phase_service),
        waterfall_tasks=WaterfallTaskService(SQLAlchemyWaterfallTaskRepository(database)),
        links=ProjectLinkService(project_links, projects),
        collaboration_queries=CollaborationQueryService(project_links, projects),
        resources=ResourceLinkService(SQLAlchemyResourceLinkRepository(database)),
        todos=TodoService(SQLAlchemyTodoRepository(database)),
        artifacts=ArtifactService(SQLAlchemyArtifactRepository(database)),
        diagram_documents=DiagramDocumentCodec(),
        workspace_documents=WorkspaceDocumentCodec(),
        images=ImageAssetService(settings.data_directory),
        issues=issues,
        health=SystemHealthService(database, issues),
    )
