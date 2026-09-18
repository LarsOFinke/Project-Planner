from collections.abc import Sequence

from sqlalchemy import delete, func, select

from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory
from project_planner.modules.projects.mappers.ProjectCategoryMapper import ProjectCategoryMapper
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.ProjectCategoryModel import ProjectCategoryModel


class SQLAlchemyProjectCategoryRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, category: ProjectCategory) -> None:
        with self._database.session() as session:
            session.merge(ProjectCategoryMapper.to_model(category))

    def get(self, category_id: str) -> ProjectCategory | None:
        with self._database.session() as session:
            model = session.get(ProjectCategoryModel, category_id)
            return ProjectCategoryMapper.to_entity(model) if model else None

    def list_all(self) -> Sequence[ProjectCategory]:
        statement = select(ProjectCategoryModel).order_by(
            ProjectCategoryModel.position,
            func.lower(ProjectCategoryModel.name),
        )
        with self._database.session() as session:
            return [ProjectCategoryMapper.to_entity(model) for model in session.scalars(statement)]

    def delete(self, category_id: str) -> None:
        with self._database.session() as session:
            session.execute(
                delete(ProjectCategoryModel).where(ProjectCategoryModel.id == category_id)
            )
