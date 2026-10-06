from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.entities.ArtifactRevision import ArtifactRevision
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.ArtifactModel import ArtifactModel
from project_planner.shared.database.models.ArtifactRevisionModel import ArtifactRevisionModel
from project_planner.shared.utils.clock import utc_now


class SQLAlchemyArtifactRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, artifact: Artifact) -> None:
        with self._database.session() as session:
            existing = session.get(ArtifactModel, artifact.id)
            if (
                existing is not None
                and existing.content != artifact.content
                and existing.content != "{}"
            ):
                session.add(
                    ArtifactRevisionModel(
                        id=str(uuid4()),
                        artifact_id=artifact.id,
                        content=existing.content,
                        created_at=utc_now(),
                    )
                )
            session.merge(self._model(artifact))
            session.flush()
            revisions = session.scalars(
                select(ArtifactRevisionModel)
                .where(ArtifactRevisionModel.artifact_id == artifact.id)
                .order_by(ArtifactRevisionModel.created_at.desc(), ArtifactRevisionModel.id.desc())
            ).all()
            for old_revision in revisions[20:]:
                session.delete(old_revision)

    def create_if_absent(self, artifact: Artifact) -> Artifact:
        with self._database.session() as session:
            try:
                with session.begin_nested():
                    session.add(self._model(artifact))
                    session.flush()
            except IntegrityError:
                existing = session.scalar(
                    select(ArtifactModel).where(
                        ArtifactModel.project_id == artifact.project_id,
                        ArtifactModel.kind == artifact.kind.value,
                    )
                )
                if existing is None:
                    raise
                return self._artifact(existing)
        return artifact

    def list_revisions(self, artifact_id: str) -> tuple[ArtifactRevision, ...]:
        with self._database.session() as session:
            models = session.scalars(
                select(ArtifactRevisionModel)
                .where(ArtifactRevisionModel.artifact_id == artifact_id)
                .order_by(ArtifactRevisionModel.created_at.desc(), ArtifactRevisionModel.id.desc())
            ).all()
            return tuple(self._revision(model) for model in models)

    def get_revision(self, artifact_id: str, revision_id: str) -> ArtifactRevision | None:
        with self._database.session() as session:
            model = session.get(ArtifactRevisionModel, revision_id)
            if model is None or model.artifact_id != artifact_id:
                return None
            return self._revision(model)

    @staticmethod
    def _revision(model: ArtifactRevisionModel) -> ArtifactRevision:
        return ArtifactRevision(model.id, model.artifact_id, model.content, model.created_at)

    def get_for_project(self, project_id: str, kind: ArtifactKind) -> Artifact | None:
        statement = select(ArtifactModel).where(
            ArtifactModel.project_id == project_id, ArtifactModel.kind == kind.value
        )
        with self._database.session() as session:
            model = session.scalar(statement)
            if model is None:
                return None
            return self._artifact(model)

    @staticmethod
    def _artifact(model: ArtifactModel) -> Artifact:
        return Artifact(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            kind=ArtifactKind(model.kind),
            content=model.content,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _model(artifact: Artifact) -> ArtifactModel:
        return ArtifactModel(
            id=artifact.id,
            project_id=artifact.project_id,
            title=artifact.title,
            kind=artifact.kind.value,
            content=artifact.content,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
