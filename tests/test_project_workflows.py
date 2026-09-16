import sqlite3
from pathlib import Path

import pytest

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.core.bootstrap.container_builder import build_container
from project_planner.core.configuration.Settings import Settings
from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus
from project_planner.core.infrastructure.database.SQLiteDatabase import SQLiteDatabase
from project_planner.core.infrastructure.repositories.SQLitePhaseRepository import (
    SQLitePhaseRepository,
)


@pytest.fixture
def planner() -> ApplicationContainer:
    return build_container(Settings(Path(":memory:"), 1280, 800, 20))


def test_creates_hierarchical_projects_and_phase_template(
    planner: ApplicationContainer,
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
        "Requirements",
        "Design",
        "Implementation",
        "Verification",
        "Deployment",
    ]


def test_updates_metadata_and_rejects_hierarchy_cycles(
    planner: ApplicationContainer,
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


def test_edits_and_reorders_custom_phases(planner: ApplicationContainer) -> None:
    project = planner.projects.create("Custom")
    discovery = planner.phases.add(project.id, "Discovery")
    delivery = planner.phases.add(project.id, "Delivery")
    planner.phases.move(project.id, delivery.id, -1)
    planner.phases.update(discovery.id, project.id, "Research", "")

    phases = planner.phases.list_for_project(project.id)
    assert [phase.name for phase in phases] == ["Delivery", "Research"]
    assert [phase.position for phase in phases] == [0, 1]


def test_phase_metadata_and_timestamps_are_persisted(
    planner: ApplicationContainer,
) -> None:
    project = planner.projects.create("Structured phases")
    phase = planner.phases.add(
        project.id,
        "Discovery",
        "Validate the problem and measurable outcome.",
        PhaseStatus.ACTIVE,
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
            CREATE TABLE phases (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL,
                UNIQUE(project_id, position)
            );
            INSERT INTO phases VALUES ('phase-1', 'project-1', 'Legacy', '', 0);
            """
        )

    repository = SQLitePhaseRepository(SQLiteDatabase(database_path))
    restored = repository.list_for_project("project-1")[0]

    assert restored.name == "Legacy"
    assert restored.status is PhaseStatus.PLANNED
    assert restored.created_at == restored.updated_at


def test_links_projects_and_removes_link(planner: ApplicationContainer) -> None:
    first = planner.projects.create("Core")
    second = planner.projects.create("Companion")
    link = planner.links.add(first.id, second.id, "depends-on")

    assert planner.links.list_for_project(second.id) == [link]
    planner.links.remove(link)
    assert planner.links.list_for_project(first.id) == []


def test_persists_versioned_diagram_and_workspace_json(
    planner: ApplicationContainer,
) -> None:
    project = planner.projects.create("Visual")
    diagram = planner.artifacts.get_or_create(project.id, ArtifactKind.DIAGRAM)
    updated = planner.artifacts.save_json(
        diagram, {"version": 1, "nodes": [{"id": "one"}], "edges": []}
    )

    loaded = planner.artifacts.get_or_create(project.id, ArtifactKind.DIAGRAM)
    assert loaded.id == updated.id
    assert planner.artifacts.read_json(loaded)["nodes"] == [{"id": "one"}]
