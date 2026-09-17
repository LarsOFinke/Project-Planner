from sqlalchemy import select

from project_planner.core.domain.artifacts.Artifact import Artifact
from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.ArtifactModel import ArtifactModel


class SQLAlchemyArtifactRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, artifact: Artifact) -> None:
        with self._database.session() as session:
            session.merge(
                ArtifactModel(
                    id=artifact.id,
                    project_id=artifact.project_id,
                    title=artifact.title,
                    kind=artifact.kind.value,
                    content=artifact.content,
                    created_at=artifact.created_at,
                    updated_at=artifact.updated_at,
                )
            )

    def get_for_project(self, project_id: str, kind: ArtifactKind) -> Artifact | None:
        statement = select(ArtifactModel).where(
            ArtifactModel.project_id == project_id, ArtifactModel.kind == kind.value
        )
        with self._database.session() as session:
            model = session.scalar(statement)
            if model is None:
                return None
            return Artifact(
                id=model.id,
                project_id=model.project_id,
                title=model.title,
                kind=ArtifactKind(model.kind),
                content=model.content,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
