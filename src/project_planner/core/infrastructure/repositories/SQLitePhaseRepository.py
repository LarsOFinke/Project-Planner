from collections.abc import Sequence

from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.infrastructure.database.SQLiteDatabase import SQLiteDatabase


class SQLitePhaseRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save_all(self, project_id: str, phases: Sequence[Phase]) -> None:
        with self._database.connection() as connection:
            connection.execute("DELETE FROM phases WHERE project_id = ?", (project_id,))
            connection.executemany(
                """INSERT INTO phases (id, project_id, name, description, position)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (phase.id, phase.project_id, phase.name, phase.description, phase.position)
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
                position=row["position"],
            )
            for row in rows
        ]
