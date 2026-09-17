from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Date, inspect, select
from sqlalchemy.orm import Session

from project_planner.core.infrastructure.database.Database import Database
from project_planner.core.infrastructure.database.models.ArtifactModel import ArtifactModel
from project_planner.core.infrastructure.database.models.BacklogItemModel import BacklogItemModel
from project_planner.core.infrastructure.database.models.PhaseModel import PhaseModel
from project_planner.core.infrastructure.database.models.PlanningSectionModel import (
    PlanningSectionModel,
)
from project_planner.core.infrastructure.database.models.ProjectLinkModel import ProjectLinkModel
from project_planner.core.infrastructure.database.models.ProjectModel import ProjectModel
from project_planner.core.infrastructure.database.models.ResourceLinkModel import ResourceLinkModel
from project_planner.core.infrastructure.database.models.SectionItemModel import SectionItemModel
from project_planner.core.infrastructure.database.models.SprintModel import SprintModel
from project_planner.core.infrastructure.database.models.TodoModel import TodoModel
from project_planner.core.infrastructure.database.models.UTCDateTime import UTCDateTime
from project_planner.core.infrastructure.database.models.WaterfallTaskModel import (
    WaterfallTaskModel,
)
from project_planner.core.infrastructure.transfer.ImportReport import ImportReport

_FORMAT = "project-planner-database-export"
_VERSION = 4
_TABLES = (
    "projects",
    "phases",
    "project_links",
    "todos",
    "artifacts",
    "resource_links",
    "planning_sections",
    "sprints",
    "backlog_items",
    "section_items",
    "waterfall_tasks",
)


class DatabaseTransferService:
    def __init__(self, database: Database) -> None:
        self._database = database

    def export_to(self, destination: str | Path) -> Path:
        path = Path(destination).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._database.session() as session:
            payload = {
                "format": _FORMAT,
                "version": _VERSION,
                "exported_at": datetime.now(UTC).isoformat(),
                "tables": {
                    "projects": self._rows(session, ProjectModel),
                    "phases": self._rows(session, PhaseModel),
                    "project_links": self._rows(session, ProjectLinkModel),
                    "todos": self._rows(session, TodoModel),
                    "artifacts": self._rows(session, ArtifactModel),
                    "resource_links": self._rows(session, ResourceLinkModel),
                    "planning_sections": self._rows(session, PlanningSectionModel),
                    "sprints": self._rows(session, SprintModel),
                    "backlog_items": self._rows(session, BacklogItemModel),
                    "section_items": self._rows(session, SectionItemModel),
                    "waterfall_tasks": self._rows(session, WaterfallTaskModel),
                },
            }
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

    def import_from(self, source: str | Path, *, dry_run: bool = True) -> ImportReport:
        payload = json.loads(Path(source).expanduser().read_text(encoding="utf-8"))
        tables = self._validated_tables(payload)
        session = self._database.new_session()
        try:
            created, updated = self._merge(session, tables)
            session.flush()
            if dry_run:
                session.rollback()
            else:
                session.commit()
            return ImportReport(created=created, updated=updated, dry_run=dry_run)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    def _rows(session: Session, model_type: type[Any]) -> list[dict[str, Any]]:
        primary_keys = inspect(model_type).primary_key
        statement = select(model_type).order_by(*primary_keys)
        return [
            {
                column.key: DatabaseTransferService._json_value(getattr(model, column.key))
                for column in inspect(model_type).columns
            }
            for model in session.scalars(statement)
        ]

    @staticmethod
    def _json_value(value: Any) -> Any:
        return value.isoformat() if isinstance(value, date) else value

    @staticmethod
    def _validated_tables(payload: object) -> dict[str, list[dict[str, Any]]]:
        if not isinstance(payload, dict):
            raise ValueError("Import document must be a JSON object")
        version = payload.get("version")
        if payload.get("format") != _FORMAT or version not in {1, 2, 3, _VERSION}:
            raise ValueError("Unsupported database export format or version")
        raw_tables = payload.get("tables")
        if not isinstance(raw_tables, dict):
            raise ValueError("Import document has no tables object")
        unexpected = set(raw_tables) - set(_TABLES)
        if unexpected:
            raise ValueError(f"Import document contains unknown tables: {sorted(unexpected)}")
        missing_tables = set(_TABLES) - set(raw_tables)
        if version in {1, 2}:
            missing_tables.discard("resource_links")
        if version in {1, 2, 3}:
            missing_tables -= {
                "planning_sections",
                "sprints",
                "backlog_items",
                "section_items",
                "waterfall_tasks",
            }
        if missing_tables:
            raise ValueError(f"Import document is missing tables: {sorted(missing_tables)}")
        result: dict[str, list[dict[str, Any]]] = {}
        for table in _TABLES:
            rows = raw_tables.get(table, [])
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise ValueError(f"Table {table!r} must be a list of objects")
            result[table] = rows
        if version == 1:
            for todo in result["todos"]:
                todo.setdefault("phase_id", None)
        if version in {1, 2, 3}:
            status_map = {
                "completed": "completed",
                "skipped": "completed",
                "active": "in_progress",
                "blocked": "in_progress",
            }
            for phase in result["phases"]:
                phase["status"] = status_map.get(phase.get("status"), "not_started")
        return result

    def _merge(self, session: Session, tables: dict[str, list[dict[str, Any]]]) -> tuple[int, int]:
        created = updated = 0
        model_rows: tuple[tuple[type[Any], list[dict[str, Any]]], ...] = (
            (ProjectModel, self._ordered_projects(tables["projects"])),
            (PlanningSectionModel, tables["planning_sections"]),
            (SprintModel, tables["sprints"]),
            (PhaseModel, tables["phases"]),
            (BacklogItemModel, tables["backlog_items"]),
            (SectionItemModel, tables["section_items"]),
            (WaterfallTaskModel, tables["waterfall_tasks"]),
            (ProjectLinkModel, tables["project_links"]),
            (TodoModel, tables["todos"]),
            (ArtifactModel, tables["artifacts"]),
            (ResourceLinkModel, tables["resource_links"]),
        )
        for model_type, rows in model_rows:
            allowed = {column.key for column in inspect(model_type).columns}
            required = {
                column.key
                for column in inspect(model_type).columns
                if not column.nullable and column.default is None and column.server_default is None
            }
            for raw_row in rows:
                unknown = set(raw_row) - allowed
                missing = required - set(raw_row)
                if unknown or missing:
                    raise ValueError(
                        f"Invalid {model_type.__tablename__} row; "
                        f"unknown={sorted(unknown)}, missing={sorted(missing)}"
                    )
                values = {
                    key: self._model_value(model_type, key, value) for key, value in raw_row.items()
                }
                identity = tuple(values[column.key] for column in inspect(model_type).primary_key)
                existing = session.get(model_type, identity[0] if len(identity) == 1 else identity)
                if existing is None:
                    created += 1
                else:
                    updated += 1
                session.merge(model_type(**values))
            session.flush()
        return created, updated

    @staticmethod
    def _model_value(model_type: type[Any], key: str, value: Any) -> Any:
        column = inspect(model_type).columns[key]
        if value is None:
            return None
        if isinstance(column.type, UTCDateTime):
            if not isinstance(value, str):
                raise ValueError(f"{model_type.__tablename__}.{key} must be a timestamp")
            return datetime.fromisoformat(value)
        if isinstance(column.type, Date):
            if not isinstance(value, str):
                raise ValueError(f"{model_type.__tablename__}.{key} must be a date")
            return date.fromisoformat(value)
        return value

    @staticmethod
    def _ordered_projects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        remaining = list(rows)
        ordered: list[dict[str, Any]] = []
        imported_ids: set[object] = set()
        row_ids = {row.get("id") for row in rows}
        while remaining:
            ready = [
                row
                for row in remaining
                if row.get("parent_id") is None
                or row.get("parent_id") not in row_ids
                or row.get("parent_id") in imported_ids
            ]
            if not ready:
                raise ValueError("Imported project hierarchy contains a cycle")
            for row in ready:
                ordered.append(row)
                imported_ids.add(row.get("id"))
                remaining.remove(row)
        return ordered
