from collections.abc import Sequence
from datetime import datetime

from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.infrastructure.database.SQLiteDatabase import SQLiteDatabase


class SQLitePhaseRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save_all(self, project_id: str, phases: Sequence[Phase]) -> None:
        with self._database.connection() as connection:
            connection.execute("DELETE FROM phases WHERE project_id = ?", (project_id,))
            connection.executemany(
                """INSERT INTO phases
                   (id, project_id, name, description, status, position,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        phase.id,
                        phase.project_id,
                        phase.name,
                        phase.description,
                        phase.status.value,
                        phase.position,
                        phase.created_at.isoformat(),
                        phase.updated_at.isoformat(),
                    )
                    for phase in phases
                ],
            )

    def list_for_project(self, project_id: str) -> Sequence[Phase]:
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM phases WHERE project_id = ? ORDER BY position", (project_id,)
            ).fetchall()
        return [
            Phase(
                id=row["id"],
                project_id=row["project_id"],
                name=row["name"],
                description=row["description"],
                status=PhaseStatus(row["status"]),
                position=row["position"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]
