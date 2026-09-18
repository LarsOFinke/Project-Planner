import json
import sqlite3
from pathlib import Path

from sqlalchemy import inspect, text

from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.modules.todos.entities.TodoModule import TodoModule
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
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0011"
    assert "category_id" in {column["name"] for column in inspector.get_columns("projects")}

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
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0011"
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

    planner.phases.remove(project.id, discovery.id)
    assert planner.todos.list_for_context(project.id, TodoModule.PHASES, discovery.id) == []


def test_database_export_import_dry_run_and_apply(tmp_path: Path) -> None:
    source_path = tmp_path / "source.sqlite3"
    source = build_test_services(Settings(source_path, 1280, 800, 20))
    category = source.project_categories.create("Products")
    parent = source.projects.create("Platform", category_id=category.id)
    project = source.projects.create("Desktop", parent_id=parent.id, category_id=category.id)
    source.phases.add(project.id, "Discovery")
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
    source.sections.add_item(section.id, "Confirm release copy", assignee="Ada")

    export_path = tmp_path / "planner-export.json"
    DatabaseTransferGateway(Database(source_path)).export_to(export_path)
    document = json.loads(export_path.read_text(encoding="utf-8"))
    assert document["format"] == "project-planner-database-export"
    assert document["version"] == 5

    target_path = tmp_path / "target.sqlite3"
    target_database = Database(target_path)
    transfer = DatabaseTransferGateway(target_database)
    dry_run = transfer.import_from(export_path)
    target = build_test_services(Settings(target_path, 1280, 800, 20))

    assert dry_run.dry_run is True
    assert dry_run.created == 10
    assert target.projects.list_all() == []

    applied = transfer.import_from(export_path, dry_run=False)
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
    assert restored.sections.list_items(restored_section.id)[0].assignee == "Ada"


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
        DatabaseTransferGateway(database).import_from(path, dry_run=False)
    except ValueError as error:
        assert "Unsupported" in str(error)
    else:
        raise AssertionError("Future export version was accepted")
