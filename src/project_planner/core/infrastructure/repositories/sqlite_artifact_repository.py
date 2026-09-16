from datetime import datetime

from project_planner.core.domain.artifacts.artifact import Artifact
from project_planner.core.domain.artifacts.artifact_kind import ArtifactKind
from project_planner.core.infrastructure.database.sqlite_database import SQLiteDatabase


class SQLiteArtifactRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save(self, artifact: Artifact) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """INSERT INTO artifacts
                   (id, project_id, title, kind, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     title=excluded.title, content=excluded.content,
                     updated_at=excluded.updated_at""",
                (
                    artifact.id,
                    artifact.project_id,
                    artifact.title,
                    artifact.kind.value,
                    artifact.content,
                    artifact.created_at.isoformat(),
                    artifact.updated_at.isoformat(),
                ),
            )

    def get_for_project(
        self, project_id: str, kind: ArtifactKind
    ) -> Artifact | None:
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM artifacts WHERE project_id = ? AND kind = ?",
                (project_id, kind.value),
            ).fetchone()
        if row is None:
            return None
        return Artifact(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            kind=ArtifactKind(row["kind"]),
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
