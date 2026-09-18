from typing import Annotated

from fastapi import APIRouter, Body, Query

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner.modules.health.entities.SystemHealth import SystemHealth
from project_planner.modules.health.services.IssueLogService import IssueLogService
from project_planner.modules.health.services.SystemHealthService import SystemHealthService


class SystemController:
    def __init__(self, issues: IssueLogService, health: SystemHealthService) -> None:
        self._issues = issues
        self._health = health
        self.router = APIRouter(tags=["system"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_health_routes()
        self._register_issue_routes()

    def _register_health_routes(self) -> None:
        self.router.add_api_route(
            "/health", self.health, methods=["GET"], response_model=SystemHealth
        )

    def _register_issue_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/issues", self.recent_issues, methods=["GET"], response_model=list[ApplicationIssue]
        )
        routes.add_api_route("/issues/count", self.issue_count_response, methods=["GET"])
        routes.add_api_route(
            "/issues",
            self.record_issue,
            methods=["POST"],
            status_code=201,
            response_model=ApplicationIssue,
        )

    def health(self):
        return self._health.snapshot()

    def recent_issues(self, limit: Annotated[int, Query(ge=1, le=500)] = 50):
        return self._issues.list_recent(limit)

    def issue_count(self) -> int:
        return self._issues.count()

    def issue_count_response(self) -> dict[str, int]:
        return {"count": self.issue_count()}

    def record_issue(
        self,
        message: Annotated[str, Body()],
        source: Annotated[str | None, Body()] = None,
    ):
        return self.record_exception(RuntimeError(message), source)

    def record_exception(self, error: Exception, source: str | None = None):
        return self._issues.record_exception(error, source)
