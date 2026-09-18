import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.modules.planning.repositories.SQLAlchemyPhaseRepository import (
    SQLAlchemyPhaseRepository,
)
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.shared.database.Database import Database
from project_planner.shared.settings.Settings import Settings
from tests.support import build_test_services


@pytest.fixture
def planner() -> SimpleNamespace:
    return build_test_services(Settings(Path(":memory:"), 1280, 800, 20))


def test_creates_hierarchical_projects_and_phase_template(
    planner: SimpleNamespace,
) -> None:
    parent = planner.projects.create("Product")
    child = planner.projects.create(
        "Launch",
        parent_id=parent.id,
        planning_method=PlanningMethod.WATERFALL,
    )
    planner.phases.initialize(child.id, child.planning_method)

    assert planner.projects.require(child.id).parent_id == parent.id
    assert [phase.name for phase in planner.phases.list_for_project(child.id)] == [
        "Planning",
        "Design",
        "Execution",
        "Completion",
    ]


def test_updates_metadata_and_rejects_hierarchy_cycles(
    planner: SimpleNamespace,
) -> None:
    parent = planner.projects.create("Parent")
    child = planner.projects.create("Child", parent_id=parent.id)
    updated = planner.projects.update(
        child.id,
        title="Desktop child",
        description="Local first",
        status=ProjectStatus.ACTIVE,
        planning_method=PlanningMethod.AGILE,
        parent_id=parent.id,
    )

    assert updated.status is ProjectStatus.ACTIVE
    with pytest.raises(ValueError, match="cycle"):
        planner.projects.update(
            parent.id,
            title=parent.title,
            description=parent.description,
            status=parent.status,
            planning_method=parent.planning_method,
            parent_id=child.id,
        )


def test_categories_group_projects_without_owning_their_lifecycle(
    planner: SimpleNamespace,
) -> None:
    category = planner.project_categories.create("Client work")
    project = planner.projects.create("Website", category_id=category.id)

    directory = planner.project_queries.list_directory()
    assert directory[0].category == category
    assert directory[0].projects[0].project == project

    planner.project_categories.delete(category.id)
    restored = planner.projects.require(project.id)
    assert restored.category_id is None
    assert planner.project_queries.list_directory()[0].category is None


def test_renames_category_without_changing_its_identity(planner: SimpleNamespace) -> None:
    category = planner.project_categories.create("Client work")

    renamed = planner.project_categories.rename(category.id, "Customer projects")

    assert renamed.id == category.id
    assert renamed.name == "Customer projects"
    assert renamed.created_at == category.created_at
    assert renamed.updated_at >= category.updated_at
    assert planner.project_categories.require(category.id) == renamed


def test_rejects_duplicate_category_name_when_renaming(planner: SimpleNamespace) -> None:
    planner.project_categories.create("Internal")
    category = planner.project_categories.create("External")

    with pytest.raises(ValueError, match="already exists"):
        planner.project_categories.rename(category.id, " internal ")


def test_archives_project_without_deleting_its_data(planner: SimpleNamespace) -> None:
    project = planner.projects.create("Keep the plan", description="Retained")

    archived = planner.projects.archive(project.id)

    assert archived.status is ProjectStatus.ARCHIVED
    assert archived.description == "Retained"
    assert planner.projects.require(project.id) == archived


def test_deleting_parent_keeps_child_as_root_project(planner: SimpleNamespace) -> None:
    parent = planner.projects.create("Parent")
    child = planner.projects.create("Child", parent_id=parent.id)

    planner.projects.delete(parent.id)

    assert planner.projects.require(child.id).parent_id is None
    with pytest.raises(LookupError, match="does not exist"):
        planner.projects.require(parent.id)


def test_edits_and_reorders_custom_phases(planner: SimpleNamespace) -> None:
    project = planner.projects.create("Custom")
    discovery = planner.phases.add(project.id, "Discovery")
    delivery = planner.phases.add(project.id, "Delivery")
    planner.phases.move(project.id, delivery.id, -1)
    planner.phases.update(discovery.id, project.id, "Research", "")

    phases = planner.phases.list_for_project(project.id)
    assert [phase.name for phase in phases] == ["Delivery", "Research"]
    assert [phase.position for phase in phases] == [0, 1]


def test_phase_metadata_and_timestamps_are_persisted(
    planner: SimpleNamespace,
) -> None:
    project = planner.projects.create("Structured phases")
    phase = planner.phases.add(
        project.id,
        "Discovery",
        "Validate the problem and measurable outcome.",
        PhaseStatus.IN_PROGRESS,
    )
    updated = planner.phases.update(
        phase.id,
        project.id,
        "Discovery and validation",
        "Interview users and document acceptance criteria.",
        PhaseStatus.COMPLETED,
    )
    restored = planner.phases.list_for_project(project.id)[0]

    assert restored == updated
    assert restored.status is PhaseStatus.COMPLETED
    assert restored.created_at == phase.created_at
    assert restored.updated_at >= restored.created_at


def test_existing_phase_table_is_migrated_without_data_loss(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
                status TEXT NOT NULL, planning_method TEXT NOT NULL,
                parent_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            INSERT INTO projects VALUES (
                'project-1', 'Legacy project', '', 'idea', 'custom', NULL,
                '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00'
            );
            CREATE TABLE phases (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL,
                UNIQUE(project_id, position)
            );
            INSERT INTO phases VALUES ('phase-1', 'project-1', 'Legacy', '', 0);
            CREATE TABLE project_links (
                source_id TEXT NOT NULL, target_id TEXT NOT NULL,
                relation TEXT NOT NULL, note TEXT NOT NULL,
                PRIMARY KEY(source_id, target_id, relation)
            );
            CREATE TABLE artifacts (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL,
                kind TEXT NOT NULL, content TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            """
        )

    repository = SQLAlchemyPhaseRepository(Database(database_path))
    restored = repository.list_for_project("project-1")[0]

    assert restored.name == "Legacy"
    assert restored.status is PhaseStatus.NOT_STARTED
    assert restored.created_at == restored.updated_at


def test_links_projects_and_removes_link(planner: SimpleNamespace) -> None:
    first = planner.projects.create("Core")
    second = planner.projects.create("Companion")
    link = planner.links.add(first.id, second.id, "depends-on")

    assert planner.links.list_for_project(second.id) == [link]
    planner.links.remove(link)
    assert planner.links.list_for_project(first.id) == []


def test_persists_versioned_diagram_and_workspace_json(
    planner: SimpleNamespace,
) -> None:
    project = planner.projects.create("Visual")
    diagram = planner.artifacts.get_or_create(project.id, ArtifactKind.DIAGRAM)
    updated = planner.artifacts.save_json(
        diagram, {"version": 1, "nodes": [{"id": "one"}], "edges": []}
    )

    loaded = planner.artifacts.get_or_create(project.id, ArtifactKind.DIAGRAM)
    assert loaded.id == updated.id
    assert planner.artifacts.read_json(loaded)["nodes"] == [{"id": "one"}]
