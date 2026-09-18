from project_planner.api.artifacts.ArtifactController import ArtifactController
from project_planner.api.collaboration.CollaborationController import CollaborationController
from project_planner.api.collaboration.queries.CollaborationQueryService import (
    CollaborationQueryService,
)
from project_planner.api.planning.PlanningController import PlanningController
from project_planner.api.projects.ProjectController import ProjectController
from project_planner.api.projects.queries.ProjectQueryService import ProjectQueryService
from project_planner.api.system.SystemController import SystemController
from project_planner.modules.artifacts.repositories.SQLAlchemyArtifactRepository import (
    SQLAlchemyArtifactRepository,
)
from project_planner.modules.artifacts.services.ArtifactService import ArtifactService
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
from project_planner.shared.settings.settings_loader import load_settings


def build_controllers(
    settings: Settings | None = None,
) -> tuple[
    ProjectController,
    PlanningController,
    CollaborationController,
    ArtifactController,
    SystemController,
]:
    resolved = settings or load_settings()
    database = Database(resolved.database_path, resolved.database_url)
    SeedRunner(database).run()

    project_repository = SQLAlchemyProjectRepository(database)
    category_repository = SQLAlchemyProjectCategoryRepository(database)
    category_service = ProjectCategoryService(category_repository)
    project_service = ProjectService(project_repository, category_repository)
    phase_service = PhaseService(SQLAlchemyPhaseRepository(database))
    issue_service = IssueLogService(SQLAlchemyIssueLogRepository(database))
    project_link_repository = SQLAlchemyProjectLinkRepository(database)

    return (
        ProjectController(
            project_service,
            category_service,
            ProjectQueryService(project_service, category_service),
            ProjectWorkflowService(project_service, phase_service),
        ),
        PlanningController(
            AgilePlanningService(SQLAlchemyAgileRepository(database)),
            phase_service,
            SectionService(SQLAlchemySectionRepository(database), phase_service),
            WaterfallTaskService(SQLAlchemyWaterfallTaskRepository(database)),
        ),
        CollaborationController(
            ProjectLinkService(project_link_repository, project_repository),
            CollaborationQueryService(project_link_repository, project_repository),
            ResourceLinkService(SQLAlchemyResourceLinkRepository(database)),
            TodoService(SQLAlchemyTodoRepository(database)),
        ),
        ArtifactController(
            ArtifactService(SQLAlchemyArtifactRepository(database)),
            ImageAssetService(resolved.data_directory),
        ),
        SystemController(
            issue_service,
            SystemHealthService(database, issue_service),
        ),
    )
