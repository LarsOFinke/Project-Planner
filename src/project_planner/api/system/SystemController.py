import tempfile
from typing import Annotated, Any

from fastapi import APIRouter, Body, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from project_planner.modules.health.entities.ApplicationIssue import ApplicationIssue
from project_planner.modules.health.entities.SystemHealth import SystemHealth
from project_planner.modules.health.services.IssueLogService import IssueLogService
from project_planner.modules.health.services.SystemHealthService import SystemHealthService
from project_planner.modules.transfer.gateways.BackupArchiveGateway import BackupArchiveGateway
from project_planner.modules.transfer.gateways.DatabaseTransferGateway import (
    DatabaseTransferGateway,
)
from project_planner.modules.transfer.models.ImportReport import ImportReport


class SystemController:
    def __init__(
        self,
        issues: IssueLogService,
        health: SystemHealthService,
        database_transfer: DatabaseTransferGateway,
        backup_archive: BackupArchiveGateway,
    ) -> None:
        self._issues = issues
        self._health = health
        self._database_transfer = database_transfer
        self._backup_archive = backup_archive
        self.router = APIRouter(tags=["system"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_health_routes()
        self._register_issue_routes()
        self._register_database_routes()

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

    def _register_database_routes(self) -> None:
        self.router.add_api_route("/backup/export", self.export_backup, methods=["GET"])
        self.router.add_api_route("/backup/import", self.import_backup, methods=["POST"])
        self.router.add_api_route("/backup/import/dry-run", self.dry_run_backup, methods=["POST"])
        self.router.add_api_route(
            "/database/export",
            self.export_database,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/database/import",
            self.import_database,
            methods=["POST"],
            response_model=ImportReport,
        )
        self.router.add_api_route(
            "/database/import/dry-run",
            self.dry_run_database_import,
            methods=["POST"],
            response_model=ImportReport,
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

    def export_database(self) -> dict[str, Any]:
        return self._database_transfer.export_document()

    def import_database(
        self,
        document: Annotated[dict[str, Any], Body()],
    ) -> ImportReport:
        return self._database_transfer.import_document(document)

    def dry_run_database_import(
        self,
        document: Annotated[dict[str, Any], Body()],
    ) -> ImportReport:
        return self._database_transfer.validate_document(document)

    def export_backup(self) -> StreamingResponse:
        archive = tempfile.TemporaryFile()  # noqa: SIM115 - streaming owns the file lifetime
        try:
            self._backup_archive.export_to(archive)
            archive.seek(0)
        except Exception:
            archive.close()
            raise

        def chunks():
            try:
                while chunk := archive.read(1024 * 1024):
                    yield chunk
            finally:
                archive.close()

        return StreamingResponse(
            chunks(),
            media_type="application/gzip",
            headers={"Content-Disposition": 'attachment; filename="project-planner-backup.tar.gz"'},
        )

    def import_backup(self, archive: Annotated[UploadFile, File()]) -> ImportReport:
        return self._backup_archive.import_from(archive.file)

    def dry_run_backup(self, archive: Annotated[UploadFile, File()]) -> ImportReport:
        return self._backup_archive.import_from(archive.file, dry_run=True)
