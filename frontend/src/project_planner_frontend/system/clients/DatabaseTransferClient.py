import json
import os
import tempfile
from pathlib import Path

from project_planner.modules.transfer.models.ImportReport import ImportReport
from project_planner_frontend.api.ApiTransport import ApiTransport


class DatabaseTransferClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def export_to(self, destination: str | Path) -> Path:
        path = Path(destination).expanduser().resolve()
        if not str(path).lower().endswith(".tar.gz"):
            path = Path(f"{path}.tar.gz")
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        os.close(handle)
        try:
            self._transport.download("/backup/export", Path(temporary_name))
            os.replace(temporary_name, path)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return path

    def export_json_to(self, destination: str | Path) -> Path:
        payload = self._transport.request("GET", "/database/export")
        if not isinstance(payload, dict):
            raise ValueError("Database export response must be a JSON object")
        path = Path(destination).expanduser().resolve()
        if path.suffix.casefold() != ".json":
            path = Path(f"{path}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as export_file:
                json.dump(payload, export_file, indent=2, sort_keys=True)
                export_file.write("\n")
            os.replace(temporary_name, path)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return path

    def import_from(self, source: str | Path) -> ImportReport:
        return self._transport.upload("/backup/import", Path(source).expanduser(), ImportReport)

    def dry_run_import(self, source: str | Path) -> ImportReport:
        return self._transport.upload(
            "/backup/import/dry-run", Path(source).expanduser(), ImportReport
        )

    def import_json_from(self, source: str | Path) -> ImportReport:
        return self._transport.model(
            ImportReport,
            "POST",
            "/database/import",
            payload=self._read_document(source),
        )

    def dry_run_json_import(self, source: str | Path) -> ImportReport:
        return self._transport.model(
            ImportReport,
            "POST",
            "/database/import/dry-run",
            payload=self._read_document(source),
        )

    @staticmethod
    def _read_document(source: str | Path) -> object:
        return json.loads(Path(source).expanduser().read_text(encoding="utf-8"))
