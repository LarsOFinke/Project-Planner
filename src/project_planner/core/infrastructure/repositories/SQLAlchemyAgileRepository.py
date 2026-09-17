from collections.abc import Sequence

from sqlalchemy import delete, select

from project_planner.core.domain.agile.BacklogItem import BacklogItem
from project_planner.core.domain.agile.BacklogPriority import BacklogPriority
from project_planner.core.domain.agile.BacklogStatus import BacklogStatus
from project_planner.core.domain.agile.Sprint import Sprint
from project_planner.core.domain.agile.SprintStatus import SprintStatus
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.BacklogItemModel import BacklogItemModel
from project_planner.core.infrastructure.database.models.SprintModel import SprintModel


class SQLAlchemyAgileRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save_item(self, item: BacklogItem) -> None:
        with self._database.session() as session:
            session.merge(BacklogItemModel(**self._item_values(item)))

    def list_items(self, project_id: str, section_id: str | None) -> Sequence[BacklogItem]:
        statement = (
            select(BacklogItemModel)
            .where(
                BacklogItemModel.project_id == project_id,
                BacklogItemModel.section_id == section_id,
            )
            .order_by(BacklogItemModel.position)
        )
        with self._database.session() as session:
            return [self._item_domain(model) for model in session.scalars(statement)]

    def delete_item(self, item_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(BacklogItemModel).where(BacklogItemModel.id == item_id))

    def save_sprint(self, sprint: Sprint) -> None:
        with self._database.session() as session:
            session.merge(
                SprintModel(
                    id=sprint.id,
                    project_id=sprint.project_id,
                    section_id=sprint.section_id,
                    name=sprint.name,
                    start_date=sprint.start_date,
                    end_date=sprint.end_date,
                    goal=sprint.goal,
                    status=sprint.status.value,
                    created_at=sprint.created_at,
                    updated_at=sprint.updated_at,
                )
            )

    def list_sprints(self, project_id: str, section_id: str | None) -> Sequence[Sprint]:
        statement = (
            select(SprintModel)
            .where(SprintModel.project_id == project_id, SprintModel.section_id == section_id)
            .order_by(SprintModel.start_date, SprintModel.created_at)
        )
        with self._database.session() as session:
            return [
                Sprint(
                    id=model.id,
                    project_id=model.project_id,
                    section_id=model.section_id,
                    name=model.name,
                    start_date=model.start_date,
                    end_date=model.end_date,
                    goal=model.goal,
                    status=SprintStatus(model.status),
                    created_at=model.created_at,
                    updated_at=model.updated_at,
                )
                for model in session.scalars(statement)
            ]

    @staticmethod
    def _item_values(item: BacklogItem) -> dict[str, object]:
        return {
            "id": item.id,
            "project_id": item.project_id,
            "section_id": item.section_id,
            "sprint_id": item.sprint_id,
            "title": item.title,
            "description": item.description,
            "priority": item.priority.value,
            "status": item.status.value,
            "assignee": item.assignee,
            "position": item.position,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }

    @staticmethod
    def _item_domain(model: BacklogItemModel) -> BacklogItem:
        return BacklogItem(
            id=model.id,
            project_id=model.project_id,
            section_id=model.section_id,
            sprint_id=model.sprint_id,
            title=model.title,
            description=model.description,
            priority=BacklogPriority(model.priority),
            status=BacklogStatus(model.status),
            assignee=model.assignee,
            position=model.position,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
