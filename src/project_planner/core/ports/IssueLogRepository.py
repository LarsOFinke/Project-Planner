from collections.abc import Sequence
from typing import Protocol

from project_planner.core.domain.health.ApplicationIssue import ApplicationIssue


class IssueLogRepository(Protocol):
    def save(self, issue: ApplicationIssue) -> None: ...

    def list_recent(self, limit: int) -> Sequence[ApplicationIssue]: ...

    def count(self) -> int: ...
