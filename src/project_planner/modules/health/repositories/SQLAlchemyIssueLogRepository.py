from collections.abc import Sequence

from sqlalchemy import func, select

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.ApplicationIssueModel import (
    ApplicationIssueModel,
)


class SQLAlchemyIssueLogRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, issue: ApplicationIssue) -> None:
        with self._database.session() as session:
            session.add(
                ApplicationIssueModel(
                    id=issue.id,
                    source=issue.source,
                    exception_type=issue.exception_type,
                    message=issue.message,
                    traceback=issue.traceback,
                    occurred_at=issue.occurred_at,
                )
            )

    def list_recent(self, limit: int) -> Sequence[ApplicationIssue]:
        statement = (
            select(ApplicationIssueModel)
            .order_by(ApplicationIssueModel.occurred_at.desc())
            .limit(limit)
        )
        with self._database.session() as session:
            return [self._domain(model) for model in session.scalars(statement)]

    def count(self) -> int:
        with self._database.session() as session:
            return int(session.scalar(select(func.count(ApplicationIssueModel.id))) or 0)

    @staticmethod
    def _domain(model: ApplicationIssueModel) -> ApplicationIssue:
        return ApplicationIssue(
            id=model.id,
            source=model.source,
            exception_type=model.exception_type,
            message=model.message,
            traceback=model.traceback,
            occurred_at=model.occurred_at,
        )
