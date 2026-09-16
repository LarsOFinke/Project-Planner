import sqlite3
from collections.abc import Sequence
from datetime import datetime

from project_planner.core.domain.projects.planning_method import PlanningMethod
from project_planner.core.domain.projects.project import Project
from project_planner.core.domain.projects.project_status import ProjectStatus
from project_planner.core.infrastructure.database.sqlite_database import SQLiteDatabase


class SQLiteProjectRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self._database = database

    def save(self, project: Project) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """INSERT INTO projects
                   (id, title, description, status, planning_method, parent_id,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     title=excluded.title, description=excluded.description,
                     status=excluded.status, planning_method=excluded.planning_method,
                     parent_id=excluded.parent_id, updated_at=excluded.updated_at""",
                (
                    project.id,
                    project.title,
                    project.description,
                    project.status.value,
                    project.planning_method.value,
                    project.parent_id,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )

    def get(self, project_id: str) -> Project | None:
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        return self._from_row(row) if row else None

    def list_all(self) -> Sequence[Project]:
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM projects ORDER BY lower(title), created_at"
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def delete(self, project_id: str) -> None:
        with self._database.connection() as connection:
            connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=ProjectStatus(row["status"]),
            planning_method=PlanningMethod(row["planning_method"]),
            parent_id=row["parent_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
