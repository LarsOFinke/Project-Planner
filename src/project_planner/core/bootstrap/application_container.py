from dataclasses import dataclass

from project_planner.core.application.artifacts.artifact_service import ArtifactService
from project_planner.core.application.assets.image_asset_service import ImageAssetService
from project_planner.core.application.links.project_link_service import ProjectLinkService
from project_planner.core.application.phases.phase_service import PhaseService
from project_planner.core.application.projects.project_service import ProjectService
from project_planner.core.configuration.settings import Settings


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    projects: ProjectService
    phases: PhaseService
    links: ProjectLinkService
    artifacts: ArtifactService
    images: ImageAssetService
