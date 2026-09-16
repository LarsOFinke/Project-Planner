from pathlib import Path

import pytest

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.core.bootstrap.container_builder import build_container
from project_planner.core.configuration.Settings import Settings
from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus


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
