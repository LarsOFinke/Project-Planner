from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.repositories.SQLAlchemyArtifactRepository import (
    SQLAlchemyArtifactRepository,
)
from project_planner.modules.artifacts.services.ArtifactService import ArtifactService
from project_planner.modules.projects.repositories.SQLAlchemyProjectCategoryRepository import (
    SQLAlchemyProjectCategoryRepository,
)
from project_planner.modules.projects.repositories.SQLAlchemyProjectRepository import (
    SQLAlchemyProjectRepository,
)
from project_planner.modules.projects.services.ProjectService import ProjectService
from project_planner.shared.database.Database import Database


def test_concurrent_first_artifact_requests_share_one_record(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    project = ProjectService(
        SQLAlchemyProjectRepository(database), SQLAlchemyProjectCategoryRepository(database)
    ).create("Concurrent diagram")
    repository = SQLAlchemyArtifactRepository(database)
    service = ArtifactService(repository)
    original_get = repository.get_for_project
    both_read_missing = Barrier(2)

    def get_before_create(project_id: str, kind: ArtifactKind):
        artifact = original_get(project_id, kind)
        if artifact is None:
            both_read_missing.wait(timeout=10)
        return artifact

    repository.get_for_project = get_before_create  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _: service.get_or_create(project.id, ArtifactKind.DIAGRAM), range(2)
            )
        )

    assert results[0].id == results[1].id
    stored = original_get(project.id, ArtifactKind.DIAGRAM)
    assert stored is not None
    assert stored.id == results[0].id
