from pathlib import Path

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.core.bootstrap.container_builder import build_container
from project_planner.core.configuration.Settings import Settings
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod


def build_planner() -> ApplicationContainer:
    return build_container(Settings(Path(":memory:"), 1280, 800, 20))


def test_project_workflow_owns_project_and_phase_creation() -> None:
    planner = build_planner()

    project = planner.project_workflows.create_project(
        "Release", planning_method=PlanningMethod.WATERFALL
    )

    assert [phase.name for phase in planner.phases.list_for_project(project.id)] == [
        "Requirements",
        "Design",
        "Implementation",
        "Verification",
        "Deployment",
    ]


def test_project_workflow_handles_planning_method_changes_and_reset() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project("Iteration")

    updated = planner.project_workflows.update_project(
        project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        planning_method=PlanningMethod.AGILE,
        parent_id=None,
    )
    planner.phases.add(updated.id, "Temporary")
    planner.project_workflows.reset_phase_plan(updated.id)

    assert [phase.name for phase in planner.phases.list_for_project(updated.id)] == [
        "Product discovery",
        "Backlog",
        "Iteration",
        "Review",
        "Retrospective",
    ]


def test_project_queries_flatten_tree_and_disambiguate_duplicate_titles() -> None:
    planner = build_planner()
    first = planner.project_workflows.create_project("Shared")
    second = planner.project_workflows.create_project("Shared")
    child = planner.project_workflows.create_project("Child", parent_id=first.id)

    tree = planner.project_queries.list_tree()
    choices = planner.project_queries.list_choices()
    overview = planner.project_queries.get_overview(first.id)

    assert next(item.depth for item in tree if item.project.id == child.id) == 1
    assert len({choice.label for choice in choices}) == len(choices)
    assert all(choice.project_id != child.id for choice in overview.parent_choices)
    assert second.id in {
        choice.project_id for choice in overview.parent_choices
    }


def test_link_service_resolves_direction_and_duplicate_target_labels() -> None:
    planner = build_planner()
    source = planner.project_workflows.create_project("Source")
    first = planner.project_workflows.create_project("Target")
    second = planner.project_workflows.create_project("Target")
    link = planner.links.add(source.id, first.id, "depends-on")

    targets = planner.links.available_targets(source.id)
    resolved = planner.links.list_resolved(first.id)

    assert len({choice.label for choice in targets}) == len(targets)
    assert resolved[0].link == link
    assert resolved[0].other_project == source
    assert resolved[0].outgoing is False
    assert second.id in {choice.project_id for choice in targets}
