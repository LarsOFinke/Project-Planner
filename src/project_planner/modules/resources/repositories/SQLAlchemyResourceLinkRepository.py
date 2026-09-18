from collections.abc import Sequence

from sqlalchemy import delete, select

from project_planner.modules.resources.entities.ResourceLink import ResourceLink
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.ResourceLinkModel import ResourceLinkModel


class SQLAlchemyResourceLinkRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, link: ResourceLink) -> None:
        with self._database.session() as session:
            session.merge(
                ResourceLinkModel(
                    id=link.id,
                    project_id=link.project_id,
                    title=link.title,
                    target=link.target,
                    kind=link.kind.value,
                    created_at=link.created_at,
                    updated_at=link.updated_at,
                )
            )

    def list_for_project(self, project_id: str) -> Sequence[ResourceLink]:
        statement = (
            select(ResourceLinkModel)
            .where(ResourceLinkModel.project_id == project_id)
            .order_by(ResourceLinkModel.kind, ResourceLinkModel.title)
        )
        with self._database.session() as session:
            return [
                ResourceLink(
                    id=model.id,
                    project_id=model.project_id,
                    title=model.title,
                    target=model.target,
                    kind=ResourceLinkKind(model.kind),
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                )
                for model in session.scalars(statement)
            ]

    def delete(self, link_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(ResourceLinkModel).where(ResourceLinkModel.id == link_id))
