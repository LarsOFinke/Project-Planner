from collections.abc import Sequence

from project_planner.core.domain.links.project_link import ProjectLink
from project_planner.core.infrastructure.database.sqlite_database import SQLiteDatabase


class SQLiteProjectLinkRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save(self, link: ProjectLink) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """INSERT INTO project_links (source_id, target_id, relation, note)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(source_id, target_id, relation)
                   DO UPDATE SET note=excluded.note""",
                (link.source_id, link.target_id, link.relation, link.note),
            )

    def list_for_project(self, project_id: str) -> Sequence[ProjectLink]:
        with self._database.connection() as connection:
            rows = connection.execute(
                """SELECT * FROM project_links
                   WHERE source_id = ? OR target_id = ?
                   ORDER BY relation, source_id, target_id""",
                (project_id, project_id),
            ).fetchall()
        return [
            ProjectLink(row["source_id"], row["target_id"], row["relation"], row["note"])
            for row in rows
        ]

    def delete(self, source_id: str, target_id: str, relation: str) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """DELETE FROM project_links
                   WHERE source_id = ? AND target_id = ? AND relation = ?""",
                (source_id, target_id, relation),
            )
