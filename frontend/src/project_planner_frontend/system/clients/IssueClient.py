from collections.abc import Sequence

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner_frontend.api.ApiTransport import ApiTransport


class IssueClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def record_exception(self, error: Exception, source: str | None = None) -> ApplicationIssue:
        return self._transport.model(
            ApplicationIssue, "POST", "/issues", payload={"message": str(error), "source": source}
        )

    def list_recent(self, limit: int = 50) -> Sequence[ApplicationIssue]:
        return self._transport.model(
            list[ApplicationIssue], "GET", "/issues", params={"limit": limit}
        )

    def count(self) -> int:
        payload = self._transport.request("GET", "/issues/count")
        return int(payload["count"])  # type: ignore[index]
