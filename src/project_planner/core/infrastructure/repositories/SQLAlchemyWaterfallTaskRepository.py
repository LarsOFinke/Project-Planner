from collections.abc import Sequence

from sqlalchemy import delete, select

from project_planner.core.domain.waterfall.WaterfallTask import WaterfallTask
from project_planner.core.domain.waterfall.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.WaterfallTaskModel import (
    WaterfallTaskModel,
)


class SQLAlchemyWaterfallTaskRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, task: WaterfallTask) -> None:
        with self._database.session() as session:
            session.merge(
                WaterfallTaskModel(
                    id=task.id,
                    phase_id=task.phase_id,
                    title=task.title,
                    description=task.description,
                    assignee=task.assignee,
                    start_date=task.start_date,
                    due_date=task.due_date,
                    status=task.status.value,
                    position=task.position,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )
            )

    def get(self, task_id: str) -> WaterfallTask | None:
        with self._database.session() as session:
            model = session.get(WaterfallTaskModel, task_id)
            return self._domain(model) if model else None

    def list_for_phase(self, phase_id: str) -> Sequence[WaterfallTask]:
        statement = (
            select(WaterfallTaskModel)
            .where(WaterfallTaskModel.phase_id == phase_id)
            .order_by(WaterfallTaskModel.position)
        )
        with self._database.session() as session:
            return [self._domain(model) for model in session.scalars(statement)]

    def delete(self, task_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(WaterfallTaskModel).where(WaterfallTaskModel.id == task_id))

    @staticmethod
    def _domain(model: WaterfallTaskModel) -> WaterfallTask:
        return WaterfallTask(
            id=model.id,
            phase_id=model.phase_id,
            title=model.title,
            description=model.description,
            assignee=model.assignee,
            start_date=model.start_date,
            due_date=model.due_date,
            status=WaterfallTaskStatus(model.status),
            position=model.position,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
