from collections.abc import Sequence

from sqlalchemy import delete, func, select

from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.Project import Project
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.ProjectModel import ProjectModel


class SQLAlchemyProjectRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, project: Project) -> None:
        with self._database.session() as session:
            session.merge(self._to_model(project))

    def get(self, project_id: str) -> Project | None:
        with self._database.session() as session:
            model = session.get(ProjectModel, project_id)
            return self._to_domain(model) if model else None

    def list_all(self) -> Sequence[Project]:
        statement = select(ProjectModel).order_by(
            func.lower(ProjectModel.title), ProjectModel.created_at
        )
        with self._database.session() as session:
            return [self._to_domain(model) for model in session.scalars(statement)]

    def delete(self, project_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(ProjectModel).where(ProjectModel.id == project_id))

    @staticmethod
    def _to_model(project: Project) -> ProjectModel:
        return ProjectModel(
            id=project.id,
            title=project.title,
            description=project.description,
            status=project.status.value,
            planning_method=project.planning_method.value,
            parent_id=project.parent_id,
            start_date=project.start_date,
            target_date=project.target_date,
            owner=project.owner,
            assignee=project.assignee,
            notes=project.notes,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    def _to_domain(model: ProjectModel) -> Project:
        return Project(
            id=model.id,
            title=model.title,
            description=model.description,
            status=ProjectStatus(model.status),
            planning_method=PlanningMethod(model.planning_method),
            parent_id=model.parent_id,
            start_date=model.start_date,
            target_date=model.target_date,
            owner=model.owner,
            assignee=model.assignee,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
