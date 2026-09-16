from project_planner.core.application.artifacts.artifact_service import ArtifactService
from project_planner.core.application.assets.image_asset_service import ImageAssetService
from project_planner.core.application.links.project_link_service import ProjectLinkService
from project_planner.core.application.phases.phase_service import PhaseService
from project_planner.core.application.projects.project_service import ProjectService
from project_planner.core.bootstrap.application_container import ApplicationContainer
from project_planner.core.configuration.settings import Settings
from project_planner.core.configuration.settings_loader import load_settings
from project_planner.core.infrastructure.database.sqlite_database import SQLiteDatabase
from project_planner.core.infrastructure.repositories.sqlite_artifact_repository import (
    SQLiteArtifactRepository,
)
from project_planner.core.infrastructure.repositories.sqlite_phase_repository import (
    SQLitePhaseRepository,
)
from project_planner.core.infrastructure.repositories.sqlite_project_link_repository import (
    SQLiteProjectLinkRepository,
)
from project_planner.core.infrastructure.repositories.sqlite_project_repository import (
    SQLiteProjectRepository,
)


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved = settings or load_settings()
    database = SQLiteDatabase(resolved.database_path)
    projects = SQLiteProjectRepository(database)
    phases = SQLitePhaseRepository(database)
    links = SQLiteProjectLinkRepository(database)
    artifacts = SQLiteArtifactRepository(database)
    return ApplicationContainer(
        settings=resolved,
        projects=ProjectService(projects),
        phases=PhaseService(phases),
        links=ProjectLinkService(links, projects),
        artifacts=ArtifactService(artifacts),
        images=ImageAssetService(resolved.data_directory),
    )
