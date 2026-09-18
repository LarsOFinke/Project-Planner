import traceback
from collections.abc import Sequence
from pathlib import Path

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner.modules.health.protocols.IssueLogRepository import IssueLogRepository


class IssueLogService:
    def __init__(self, issues: IssueLogRepository) -> None:
        self._issues = issues

    def record_exception(self, error: Exception, source: str | None = None) -> ApplicationIssue:
        issue = ApplicationIssue(
            source=source or self._source(error),
            exception_type=type(error).__name__,
            message=str(error) or type(error).__name__,
            traceback="".join(traceback.format_exception(type(error), error, error.__traceback__)),
        )
        self._issues.save(issue)
        return issue

    def list_recent(self, limit: int = 50) -> Sequence[ApplicationIssue]:
        return self._issues.list_recent(max(1, min(limit, 200)))

    def count(self) -> int:
        return self._issues.count()

    @staticmethod
    def _source(error: Exception) -> str:
        frames = traceback.extract_tb(error.__traceback__)
        frame = next(
            (entry for entry in reversed(frames) if "project_planner" in entry.filename),
            frames[-1] if frames else None,
        )
        if frame is None:
            return "Application"
        return f"{Path(frame.filename).name}:{frame.lineno} · {frame.name}"
