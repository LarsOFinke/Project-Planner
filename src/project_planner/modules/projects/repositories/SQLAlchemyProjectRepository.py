from collections.abc import Sequence

from sqlalchemy import delete, func, select

from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.mappers.ProjectMapper import ProjectMapper
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.ProjectModel import ProjectModel


class SQLAlchemyProjectRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, project: Project) -> None:
        with self._database.session() as session:
            session.merge(ProjectMapper.to_model(project))

    def save_all(self, projects: Sequence[Project]) -> None:
        with self._database.session() as session:
            for project in projects:
                session.merge(ProjectMapper.to_model(project))

    def get(self, project_id: str) -> Project | None:
        with self._database.session() as session:
            model = session.get(ProjectModel, project_id)
            return ProjectMapper.to_entity(model) if model else None

    def list_all(self) -> Sequence[Project]:
        statement = select(ProjectModel).order_by(
            func.lower(ProjectModel.title), ProjectModel.created_at
        )
        with self._database.session() as session:
            return [ProjectMapper.to_entity(model) for model in session.scalars(statement)]

    def delete(self, project_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(ProjectModel).where(ProjectModel.id == project_id))
