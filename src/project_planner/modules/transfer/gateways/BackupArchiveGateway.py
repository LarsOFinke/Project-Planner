import filecmp
import json
import shutil
import tarfile
import tempfile
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from project_planner.modules.transfer.gateways.DatabaseTransferGateway import (
    DatabaseTransferGateway,
)
from project_planner.modules.transfer.models.ImportReport import ImportReport


class BackupArchiveGateway:
    """Transfer the database and managed data files as one portable archive."""

    def __init__(self, database: DatabaseTransferGateway, data_directory: Path) -> None:
        self._database = database
        self._data_directory = data_directory

    def export_to(self, destination: BinaryIO) -> None:
        document = json.dumps(self._database.export_document(), sort_keys=True).encode("utf-8")
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
                        name = PurePosixPath("data", *path.relative_to(self._data_directory).parts)
                        archive.add(path, arcname=str(name), recursive=False)

    def import_from(self, source: BinaryIO, *, dry_run: bool = False) -> ImportReport:
        with tempfile.TemporaryDirectory(prefix="project-planner-backup-") as staging:
            staged = Path(staging)
            document = None
            asset_paths: list[tuple[Path, Path]] = []
            seen: set[str] = set()
            try:
                with tarfile.open(fileobj=source, mode="r:gz") as archive:
                    for member in archive:
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
            created: list[Path] = []
            try:
                for staged_file, target in asset_paths:
                    if target.exists():
                        continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with staged_file.open("rb") as source_file, target.open("xb") as output:
                        created.append(target)
                        shutil.copyfileobj(source_file, output)
                return replace(
                    self._database.import_document(document),
                    files_created=len(created),
                    files_unchanged=len(asset_paths) - len(created),
                )
            except Exception:
                for path in created:
                    path.unlink(missing_ok=True)
                raise
