from kivy.base import ExceptionHandler, ExceptionManager
from kivy.clock import Clock
from kivy.logger import Logger

from project_planner_frontend.api.ApiError import ApiError
from project_planner_frontend.shared.dialogs import show_error
from project_planner_frontend.system.clients.IssueClient import IssueClient


class ApplicationExceptionHandler(ExceptionHandler):
    def __init__(self, issues: IssueClient) -> None:
        self._issues = issues
        self._notification_pending = False

    def handle_exception(self, error: BaseException) -> int:
        if not isinstance(error, Exception) or isinstance(error, MemoryError):
            return ExceptionManager.RAISE
        if isinstance(error, ApiError) and error.status_code == 408:
            Clock.schedule_once(lambda _elapsed: show_error(str(error)), 0)
            return ExceptionManager.PASS
        Logger.error(
            "ProjectPlanner: Recovered from %s: %s",
            type(error).__name__,
            error,
        )
        issue_id: str | None = None
        try:
            issue_id = self._issues.record_exception(error).id
        except Exception as logging_error:
            Logger.error(
                "ProjectPlanner: Could not persist the application issue: %s",
                logging_error,
            )
        if not self._notification_pending:
            self._notification_pending = True
            Clock.schedule_once(
                lambda _elapsed: self._notify(error, issue_id),
                0,
            )
        return ExceptionManager.PASS

    def _notify(self, error: Exception, issue_id: str | None) -> None:
        self._notification_pending = False
        reference = f"\n\nIssue reference: {issue_id}" if issue_id else ""
        show_error(
            "The action could not be completed, but the application can continue.\n\n"
            f"{type(error).__name__}: {error}{reference}\n\n"
            "Open Admin to inspect recent issues and technical details."
        )
