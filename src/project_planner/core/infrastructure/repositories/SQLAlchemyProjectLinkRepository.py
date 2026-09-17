from collections.abc import Sequence

from sqlalchemy import delete, or_, select

from project_planner.core.domain.links.ProjectLink import ProjectLink
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.ProjectLinkModel import ProjectLinkModel


class SQLAlchemyProjectLinkRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, link: ProjectLink) -> None:
        with self._database.session() as session:
            session.merge(
                ProjectLinkModel(
                    source_id=link.source_id,
                    target_id=link.target_id,
                    relation=link.relation,
                    note=link.note,
                )
            )

    def list_for_project(self, project_id: str) -> Sequence[ProjectLink]:
        statement = (
            select(ProjectLinkModel)
            .where(
                or_(
                    ProjectLinkModel.source_id == project_id,
                    ProjectLinkModel.target_id == project_id,
                )
            )
            .order_by(
                ProjectLinkModel.relation,
                ProjectLinkModel.source_id,
                ProjectLinkModel.target_id,
            )
        )
        with self._database.session() as session:
            return [
                ProjectLink(model.source_id, model.target_id, model.relation, model.note)
                for model in session.scalars(statement)
            ]

    def delete(self, source_id: str, target_id: str, relation: str) -> None:
        statement = delete(ProjectLinkModel).where(
            ProjectLinkModel.source_id == source_id,
            ProjectLinkModel.target_id == target_id,
            ProjectLinkModel.relation == relation,
        )
        with self._database.session() as session:
            session.execute(statement)
