import platform
from importlib.metadata import PackageNotFoundError, version

from project_planner.core.application.health.IssueLogService import IssueLogService
from project_planner.core.domain.health.SystemHealth import SystemHealth
from project_planner.core.ports.SystemHealthProbe import SystemHealthProbe


class SystemHealthService:
    def __init__(self, probe: SystemHealthProbe, issues: IssueLogService) -> None:
        self._probe = probe
        self._issues = issues

    def snapshot(self) -> SystemHealth:
        healthy = self._probe.is_healthy()
        return SystemHealth(
            app_version=self._app_version(),
            python_version=platform.python_version(),
            database_backend=self._probe.database_backend,
            database_location=self._probe.database_location,
            database_healthy=healthy,
            issue_count=self._issues.count() if healthy else 0,
        )

    @staticmethod
    def _app_version() -> str:
        try:
            return version("project-planner")
        except PackageNotFoundError:
            return "0.1.0"
