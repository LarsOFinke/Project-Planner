import filecmp
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from project_planner.modules.transfer.gateways.DatabaseTransferGateway import (
    DatabaseTransferGateway,
)
from project_planner.modules.transfer.models.ImportReport import ImportReport


class BackupArchiveGateway:
    """Transfer the database and managed data files as one portable archive."""

    _MAX_MEMBERS = 100_000

    def __init__(
        self,
        database: DatabaseTransferGateway,
        data_directory: Path,
        max_uncompressed_bytes: int = 8 * 1024 * 1024 * 1024,
    ) -> None:
        self._database = database
        self._data_directory = data_directory
        if max_uncompressed_bytes <= 0:
            raise ValueError("Maximum backup size must be positive")
        self._max_uncompressed_bytes = max_uncompressed_bytes
        self.recover_incomplete_imports()

    @staticmethod
    def _digest(path: Path) -> str:
        result = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                result.update(chunk)
        return result.hexdigest()

    def _journal_path(self, import_id: str) -> Path:
        return self._data_directory / f".backup-import-{import_id}.json"

    def _write_journal(self, import_id: str, assets: list[tuple[Path, Path]]) -> Path:
        self._data_directory.mkdir(parents=True, exist_ok=True)
        journal = self._journal_path(import_id)
        entries = [
            {
                "path": target.relative_to(self._data_directory).as_posix(),
                "sha256": self._digest(staged),
            }
            for staged, target in assets
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self._data_directory, delete=False
        ) as output:
            temporary = Path(output.name)
            try:
                json.dump({"id": import_id, "files": entries}, output)
                output.flush()
                os.fsync(output.fileno())
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
        os.replace(temporary, journal)
        self._sync_directory(self._data_directory)
        return journal

    @staticmethod
    def _sync_directory(directory: Path) -> None:
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _remove_journal(self, journal: Path) -> None:
        journal.unlink(missing_ok=True)
        self._sync_directory(self._data_directory)

    def recover_incomplete_imports(self) -> None:
        if not self._data_directory.is_dir():
            return
        for journal in sorted(self._data_directory.glob(".backup-import-*.json")):
            document = json.loads(journal.read_text(encoding="utf-8"))
            import_id = document.get("id")
            if not isinstance(import_id, str) or journal != self._journal_path(import_id):
                raise ValueError("Backup import journal has an invalid identifier")
            committed = self._database.import_committed(import_id)
            if not committed:
                for entry in document.get("files", []):
                    relative = Path(entry["path"])
                    parts = relative.parts
                    if (
                        len(parts) != 4
                        or parts[0] != "projects"
                        or parts[2] != "images"
                        or any(part in {".", ".."} for part in parts)
                    ):
                        raise ValueError("Backup import journal contains an unsafe path")
                    target = self._data_directory / relative
                    if any(
                        parent.is_symlink() for parent in (target, *target.parents)
                    ) or not target.resolve().is_relative_to(self._data_directory.resolve()):
                        raise ValueError("Backup import journal conflicts with a symbolic link")
                    if target.exists():
                        if self._digest(target) != entry["sha256"]:
                            raise ValueError("Interrupted backup file changed after import")
                        target.unlink()
                        self._sync_directory(target.parent)
            self._remove_journal(journal)
            if committed:
                self._database.clear_import_marker(import_id)

    def _check_size(self, total: int, entries: int) -> None:
        if total > self._max_uncompressed_bytes:
            raise ValueError("Backup exceeds the configured unpacked size limit")
        if entries > self._MAX_MEMBERS:
            raise ValueError("Backup contains too many files")

    def export_to(self, destination: BinaryIO) -> None:
        document = json.dumps(self._database.export_document(), sort_keys=True).encode("utf-8")
        total = len(document)
        entries = 1
        self._check_size(total, entries)
        with tarfile.open(fileobj=destination, mode="w:gz") as archive:
            with tempfile.TemporaryFile() as payload:
                payload.write(document)
                payload.seek(0)
                info = tarfile.TarInfo("database.json")
                info.size = len(document)
                archive.addfile(info, payload)
            image_root = self._data_directory / "projects"
            if image_root.is_symlink():
                raise ValueError("Managed data contains a symbolic link")
            if image_root.is_dir():
                for path in sorted(image_root.glob("*/images/*")):
                    ancestors = (path, path.parent, path.parent.parent)
                    if any(parent.is_symlink() for parent in ancestors):
                        raise ValueError("Managed data contains a symbolic link")
                    if path.is_file():
                        total += path.stat().st_size
                        entries += 1
                        self._check_size(total, entries)
                        name = PurePosixPath("data", *path.relative_to(self._data_directory).parts)
                        archive.add(path, arcname=str(name), recursive=False)

    def import_from(self, source: BinaryIO, *, dry_run: bool = False) -> ImportReport:
        with tempfile.TemporaryDirectory(prefix="project-planner-backup-") as staging:
            staged = Path(staging)
            document = None
            asset_paths: list[tuple[Path, Path]] = []
            seen: set[str] = set()
            total = 0
            try:
                with tarfile.open(fileobj=source, mode="r:gz") as archive:
                    for member in archive:
                        if member.size < 0:
                            raise ValueError("Backup contains an invalid file size")
                        total += member.size
                        self._check_size(total, len(seen) + 1)
                        parts = PurePosixPath(member.name).parts
                        if member.name in seen or not member.isfile():
                            raise ValueError("Backup contains duplicate or non-file entries")
                        seen.add(member.name)
                        if member.name == "database.json":
                            stream = archive.extractfile(member)
                            if stream is None:
                                raise ValueError("Backup database document is unreadable")
                            document = json.load(stream)
                            continue
                        if (
                            member.name != str(PurePosixPath(member.name))
                            or len(parts) != 5
                            or parts[0:2] != ("data", "projects")
                            or parts[3] != "images"
                            or any(part in {".", ".."} for part in parts)
                        ):
                            raise ValueError("Backup contains an unsafe path")
                        relative = Path(*parts[1:])
                        target = self._data_directory / relative
                        if not target.resolve().is_relative_to(self._data_directory.resolve()):
                            raise ValueError("Backup path escapes the managed data directory")
                        staged_file = staged / relative
                        staged_file.parent.mkdir(parents=True, exist_ok=True)
                        stream = archive.extractfile(member)
                        if stream is None:
                            raise ValueError("Backup data file is unreadable")
                        with staged_file.open("wb") as output:
                            shutil.copyfileobj(stream, output)
                        asset_paths.append((staged_file, target))
            except (tarfile.TarError, json.JSONDecodeError) as error:
                raise ValueError("Invalid backup archive") from error
            if document is None:
                raise ValueError("Backup is missing database.json")
            report = self._database.validate_document(document)
            files_created = files_unchanged = 0
            for staged_file, target in asset_paths:
                ancestors = (
                    target,
                    target.parent,
                    target.parent.parent,
                    target.parent.parent.parent,
                )
                if any(parent.is_symlink() for parent in ancestors):
                    raise ValueError(f"Backup file conflicts with a symbolic link: {target}")
                if target.exists() and (
                    not target.is_file() or not filecmp.cmp(staged_file, target, shallow=False)
                ):
                    raise ValueError(f"Backup file conflicts with local data: {target}")
                if target.exists():
                    files_unchanged += 1
                else:
                    files_created += 1
            if dry_run:
                return replace(report, files_created=files_created, files_unchanged=files_unchanged)
            import_id = str(uuid4())
            new_assets = []
            for staged_file, target in asset_paths:
                if not target.exists():
                    new_assets.append((staged_file, target))
            journal = self._write_journal(import_id, new_assets)
            created: list[Path] = []
            try:
                for staged_file, target in asset_paths:
                    if target.exists():
                        if not target.is_file() or not filecmp.cmp(
                            staged_file, target, shallow=False
                        ):
                            raise ValueError(f"Backup file conflicts with local data: {target}")
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    directory = target.parent
                    while directory != self._data_directory:
                        self._sync_directory(directory)
                        directory = directory.parent
                    self._sync_directory(self._data_directory)
                    with tempfile.NamedTemporaryFile(
                        dir=target.parent, prefix=f".{target.name}.", delete=False
                    ) as output:
                        temporary = Path(output.name)
                        try:
                            with staged_file.open("rb") as source_file:
                                shutil.copyfileobj(source_file, output)
                            output.flush()
                            os.fsync(output.fileno())
                        except Exception:
                            output.close()
                            temporary.unlink(missing_ok=True)
                            raise
                    try:
                        os.link(temporary, target)
                        created.append(target)
                    finally:
                        temporary.unlink(missing_ok=True)
                    self._sync_directory(target.parent)
                imported = self._database.import_document(document, import_id=import_id)
                result = replace(
                    imported,
                    files_created=len(created),
                    files_unchanged=len(asset_paths) - len(created),
                )
                self._remove_journal(journal)
                self._database.clear_import_marker(import_id)
                return result
            except Exception:
                if not self._database.import_committed(import_id):
                    for path in created:
                        path.unlink(missing_ok=True)
                        self._sync_directory(path.parent)
                    self._remove_journal(journal)
                raise
