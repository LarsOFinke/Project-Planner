import io
import json
import os
import sqlite3
import tarfile
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner.modules.transfer.gateways.BackupArchiveGateway import BackupArchiveGateway
from project_planner.modules.transfer.gateways.DatabaseTransferGateway import (
    DatabaseTransferGateway,
)
from project_planner.shared.database.Database import Database
from project_planner.shared.settings.Settings import Settings
from tests.support import build_test_services


def test_migrations_create_versioned_normalized_schema(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    inspector = inspect(database.engine)

    assert {
        "alembic_version",
        "projects",
        "phases",
        "project_links",
        "todos",
        "artifacts",
        "seed_history",
        "resource_links",
        "planning_sections",
        "sprints",
        "backlog_items",
        "section_items",
        "waterfall_tasks",
        "application_issues",
        "project_categories",
    } <= set(inspector.get_table_names())
    with database.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0013"
    assert "category_id" in {column["name"] for column in inspector.get_columns("projects")}
    assert "position" in {column["name"] for column in inspector.get_columns("projects")}
    assert "parallel_group" in {column["name"] for column in inspector.get_columns("phases")}

    todo_foreign_tables = {
        foreign_key["referred_table"] for foreign_key in inspector.get_foreign_keys("todos")
    }
    assert todo_foreign_tables == {"phases", "projects"}
    assert {column["name"] for column in inspector.get_columns("todos")} == {
        "id",
        "project_id",
        "phase_id",
        "title",
        "description",
        "module",
        "status",
        "created_at",
        "updated_at",
    }


def test_migration_repairs_legacy_sprint_status_constraint(tmp_path: Path) -> None:
    path = tmp_path / "legacy-sprint-status.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            INSERT INTO alembic_version (version_num) VALUES ('0007');
            CREATE TABLE projects (id VARCHAR PRIMARY KEY);
            CREATE TABLE planning_sections (id VARCHAR PRIMARY KEY);
            CREATE TABLE sprints (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                section_id VARCHAR REFERENCES planning_sections(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                goal TEXT NOT NULL DEFAULT '',
                status VARCHAR(24) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                CONSTRAINT ck_sprints_status
                    CHECK (status IN ('current', 'completed')),
                CONSTRAINT ck_sprints_dates CHECK (end_date >= start_date)
            );
            CREATE INDEX idx_sprints_context_status
                ON sprints (project_id, section_id, status);
            """
        )

    database = Database(path)
    with database.engine.begin() as connection:
        connection.execute(text("INSERT INTO projects (id) VALUES ('project')"))
        connection.execute(text("INSERT INTO planning_sections (id) VALUES ('section')"))
        connection.execute(
            text(
                "INSERT INTO sprints "
                "(id, project_id, section_id, name, start_date, end_date, goal, status, "
                "created_at, updated_at) VALUES "
                "('sprint', 'project', 'section', 'Sprint 1', '2026-09-01', "
                "'2026-09-14', '', 'planned', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0013"
        assert connection.scalar(text("SELECT status FROM sprints")) == "planned"


def test_migration_repairs_phase_project_cascade_without_losing_children(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy-phase-cascade.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            INSERT INTO alembic_version (version_num) VALUES ('0010');
            CREATE TABLE projects (id VARCHAR PRIMARY KEY);
            CREATE TABLE planning_sections (id VARCHAR PRIMARY KEY);
            CREATE TABLE phases (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL REFERENCES projects(id),
                section_id VARCHAR REFERENCES planning_sections(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL,
                status VARCHAR(32) NOT NULL,
                start_date DATE,
                end_date DATE,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            );
            CREATE TABLE todos (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                phase_id VARCHAR REFERENCES phases(id) ON DELETE CASCADE
            );
            CREATE TABLE waterfall_tasks (
                id VARCHAR PRIMARY KEY,
                phase_id VARCHAR NOT NULL REFERENCES phases(id) ON DELETE CASCADE
            );
            INSERT INTO projects (id) VALUES ('project');
            INSERT INTO phases (
                id, project_id, name, position, status, created_at, updated_at
            ) VALUES (
                'phase', 'project', 'Delivery', 0, 'not_started',
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            );
            INSERT INTO todos (id, project_id, phase_id)
                VALUES ('todo', 'project', 'phase');
            INSERT INTO waterfall_tasks (id, phase_id) VALUES ('task', 'phase');
            """
        )

    database = Database(path)
    with database.engine.begin() as connection:
        phase_foreign_keys = connection.execute(text("PRAGMA foreign_key_list(phases)")).all()
        project_key = next(key for key in phase_foreign_keys if key[3] == "project_id")
        assert project_key[6] == "CASCADE"
        assert connection.scalar(text("SELECT count(*) FROM todos")) == 1
        assert connection.scalar(text("SELECT count(*) FROM waterfall_tasks")) == 1
        connection.execute(text("DELETE FROM projects WHERE id = 'project'"))
        assert connection.scalar(text("SELECT count(*) FROM phases")) == 0
        assert connection.scalar(text("SELECT count(*) FROM todos")) == 0
        assert connection.scalar(text("SELECT count(*) FROM waterfall_tasks")) == 0


def test_todos_are_shared_by_module_and_cascade_with_project(tmp_path: Path) -> None:
    planner = build_test_services(Settings(tmp_path / "todos.sqlite3", 1280, 800, 20))
    project = planner.projects.create("Release")
    todo = planner.todos.add(
        project.id,
        "Review model",
        "Check the diagram before implementation.",
        TodoModule.DIAGRAM,
    )

    assert planner.todos.require(todo.id).module is TodoModule.DIAGRAM
    planner.projects.delete(project.id)
    assert planner.todos.list_for_project(project.id) == []


def test_phase_todos_survive_reordering_and_follow_phase_deletion(tmp_path: Path) -> None:
    planner = build_test_services(Settings(tmp_path / "phase-todos.sqlite3", 1280, 800, 20))
    project = planner.projects.create("Delivery")
    discovery = planner.phases.add(project.id, "Discovery")
    delivery = planner.phases.add(project.id, "Delivery")
    todo = planner.todos.add(
        project.id,
        "Interview users",
        module=TodoModule.PHASES,
        phase_id=discovery.id,
    )

    planner.phases.move(project.id, delivery.id, -1)
    assert planner.todos.require(todo.id).phase_id == discovery.id

    planner.phases.move_to(project.id, discovery.id, delivery.id)
    assert [phase.id for phase in planner.phases.list_for_project(project.id)] == [
        discovery.id,
        delivery.id,
    ]

    planner.phases.remove(project.id, discovery.id)
    assert planner.todos.list_for_context(project.id, TodoModule.PHASES, discovery.id) == []


def test_database_export_import_dry_run_and_apply(tmp_path: Path) -> None:
    source_path = tmp_path / "source.sqlite3"
    source = build_test_services(Settings(source_path, 1280, 800, 20))
    category = source.project_categories.create("Products")
    parent = source.projects.create("Platform", category_id=category.id)
    project = source.projects.create("Desktop", parent_id=parent.id, category_id=category.id)
    source.phases.add(project.id, "Discovery", parallel_group="Discovery lane")
    source.todos.add(project.id, "Confirm scope", module=TodoModule.OVERVIEW)
    source.links.add(parent.id, project.id, "contains")
    source.artifacts.get_or_create(project.id, ArtifactKind.DIAGRAM)
    source.resources.add(
        project.id,
        "Project website",
        "https://example.com/project",
        ResourceLinkKind.WEB,
    )
    section = source.sections.add(project.id, "Launch prep", SectionType.FREE)
    source.sections.add_item(section.id, "Confirm release copy", assignee="Example assignee")

    export_path = tmp_path / "planner-export.json"
    DatabaseTransferGateway(Database(source_path)).export_to(export_path)
    document = json.loads(export_path.read_text(encoding="utf-8"))
    assert document["format"] == "project-planner-database-export"
    assert document["version"] == 7

    target_path = tmp_path / "target.sqlite3"
    target_database = Database(target_path)
    transfer = DatabaseTransferGateway(target_database)
    dry_run = transfer.validate_import(export_path)
    target = build_test_services(Settings(target_path, 1280, 800, 20))

    assert dry_run.dry_run is True
    assert dry_run.created == 10
    assert target.projects.list_all() == []

    applied = transfer.import_from(export_path)
    restored = build_test_services(Settings(target_path, 1280, 800, 20))

    assert applied.dry_run is False
    assert applied.created == 10
    assert {item.title for item in restored.projects.list_all()} == {"Platform", "Desktop"}
    assert restored.project_categories.list_all()[0].name == "Products"
    assert restored.todos.list_for_project(project.id)[0].title == "Confirm scope"
    assert restored.links.list_for_project(project.id)[0].relation == "contains"
    assert restored.resources.list_for_project(project.id)[0].title == "Project website"
    restored_section = restored.sections.list_for_project(project.id)[0]
    assert restored_section.name == "Launch prep"
    assert restored.sections.list_items(restored_section.id)[0].assignee == "Example assignee"
    assert restored.phases.list_for_project(project.id)[0].parallel_group == "Discovery lane"

    unchanged = transfer.validate_import(export_path)
    assert (unchanged.created, unchanged.updated, unchanged.unchanged) == (0, 0, 10)
    unchanged_apply = transfer.import_from(export_path)
    assert (unchanged_apply.created, unchanged_apply.updated, unchanged_apply.unchanged) == (
        0,
        0,
        10,
    )

    project_row = next(row for row in document["tables"]["projects"] if row["id"] == project.id)
    project_row["title"] = "Desktop changed"
    changed = transfer.validate_document(document)
    assert (changed.created, changed.updated, changed.unchanged) == (0, 1, 9)
    assert next(item for item in restored.projects.list_all() if item.id == project.id).title == (
        "Desktop"
    )
    document["tables"]["projects"].append(dict(project_row))
    with pytest.raises(ValueError, match="Duplicate projects primary key"):
        transfer.import_document(document)
    assert next(item for item in restored.projects.list_all() if item.id == project.id).title == (
        "Desktop"
    )


def test_backup_rejects_unsafe_paths_and_conflicting_local_files(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    data = tmp_path / "data"
    gateway = BackupArchiveGateway(DatabaseTransferGateway(database), data)
    image = data / "projects" / "sample" / "images" / "example.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"original")
    backup = io.BytesIO()
    gateway.export_to(backup)
    backup.seek(0)
    same = gateway.import_from(backup, dry_run=True)
    assert (same.files_created, same.files_unchanged) == (0, 1)
    assert (same.created, same.updated, same.unchanged) == (0, 0, 0)
    backup.seek(0)
    same_applied = gateway.import_from(backup)
    assert (same_applied.files_created, same_applied.files_unchanged) == (0, 1)

    image.unlink()
    backup.seek(0)
    missing = gateway.import_from(backup, dry_run=True)
    assert (missing.files_created, missing.files_unchanged) == (1, 0)
    assert not image.exists()
    backup.seek(0)
    restored = gateway.import_from(backup)
    assert (restored.files_created, restored.files_unchanged) == (1, 0)
    assert image.read_bytes() == b"original"

    image.write_bytes(b"local edit")
    backup.seek(0)
    with pytest.raises(ValueError, match="conflicts with local data"):
        gateway.import_from(backup)
    assert image.read_bytes() == b"local edit"

    unsafe = io.BytesIO()
    with tarfile.open(fileobj=unsafe, mode="w:gz") as archive:
        document = json.dumps(DatabaseTransferGateway(database).export_document()).encode()
        info = tarfile.TarInfo("database.json")
        info.size = len(document)
        archive.addfile(info, io.BytesIO(document))
        info = tarfile.TarInfo("data/../outside")
        info.size = 1
        archive.addfile(info, io.BytesIO(b"x"))
    unsafe.seek(0)
    with pytest.raises(ValueError, match="unsafe path"):
        gateway.import_from(unsafe)
    assert not (tmp_path / "outside").exists()


def test_backup_import_rolls_back_new_files_if_database_merge_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_database = Database(tmp_path / "source.sqlite3")
    source_data = tmp_path / "source-data"
    source_image = source_data / "projects" / "sample" / "images" / "example.png"
    source_image.parent.mkdir(parents=True)
    source_image.write_bytes(b"image contents")
    archive = io.BytesIO()
    BackupArchiveGateway(DatabaseTransferGateway(source_database), source_data).export_to(archive)

    target_data = tmp_path / "target-data"
    target_image = target_data / "projects" / "sample" / "images" / "example.png"
    transfer = DatabaseTransferGateway(Database(tmp_path / "target.sqlite3"))
    gateway = BackupArchiveGateway(transfer, target_data)

    def fail_merge(_document: object) -> None:
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(transfer, "import_document", fail_merge)
    archive.seek(0)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        gateway.import_from(archive)
    assert not target_image.exists()
    assert not [path for path in target_data.rglob("*") if path.is_file()]


def test_backup_rejects_archives_over_configured_unpacked_limit(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    archive = io.BytesIO()
    BackupArchiveGateway(DatabaseTransferGateway(database), tmp_path / "data").export_to(archive)
    limited = BackupArchiveGateway(DatabaseTransferGateway(database), tmp_path / "data", 1)

    archive.seek(0)
    with pytest.raises(ValueError, match="unpacked size limit"):
        limited.import_from(archive, dry_run=True)
    with pytest.raises(ValueError, match="unpacked size limit"):
        limited.export_to(io.BytesIO())


def test_backup_import_rolls_back_files_after_a_restore_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    data = tmp_path / "data"
    image_dir = data / "projects" / "sample" / "images"
    image_dir.mkdir(parents=True)
    for name in ("first.png", "second.png"):
        (image_dir / name).write_bytes(name.encode())
    archive = io.BytesIO()
    gateway = BackupArchiveGateway(DatabaseTransferGateway(database), data)
    gateway.export_to(archive)
    for path in image_dir.iterdir():
        path.unlink()

    link = os.link

    def fail_second(source: str | Path, target: str | Path) -> None:
        if Path(target).name == "second.png":
            raise OSError("simulated restore failure")
        link(source, target)

    monkeypatch.setattr(os, "link", fail_second)
    archive.seek(0)
    with pytest.raises(OSError, match="simulated restore failure"):
        gateway.import_from(archive)
    assert not list(image_dir.iterdir())


def test_import_rejects_unknown_export_version_without_changes(tmp_path: Path) -> None:
    path = tmp_path / "future.json"
    path.write_text(
        json.dumps(
            {
                "format": "project-planner-database-export",
                "version": 99,
                "tables": {},
            }
        ),
        encoding="utf-8",
    )
    database = Database(tmp_path / "target.sqlite3")

    try:
        DatabaseTransferGateway(database).import_from(path)
    except ValueError as error:
        assert "Unsupported" in str(error)
    else:
        raise AssertionError("Future export version was accepted")
