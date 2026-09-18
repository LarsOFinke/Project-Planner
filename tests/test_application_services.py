from pathlib import Path
from types import SimpleNamespace

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.shared.settings.Settings import Settings
from tests.support import build_test_services


def build_planner() -> SimpleNamespace:
    return build_test_services(Settings(Path(":memory:"), 1280, 800, 20))


def test_project_workflow_owns_project_and_phase_creation() -> None:
    planner = build_planner()

    project = planner.project_workflows.create_project(
        "Release", planning_method=PlanningMethod.WATERFALL
    )

    assert [phase.name for phase in planner.phases.list_for_project(project.id)] == [
        "Planning",
        "Design",
        "Execution",
        "Completion",
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
    assert planner.phases.list_for_project(updated.id) == []
    backlog_item = planner.agile.add_item(updated.id, "Validate idea")
    assert planner.agile.list_items(updated.id) == [backlog_item]


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
    assert second.id in {choice.project_id for choice in overview.parent_choices}


def test_link_service_resolves_direction_and_duplicate_target_labels() -> None:
    planner = build_planner()
    source = planner.project_workflows.create_project("Source")
    first = planner.project_workflows.create_project("Target")
    second = planner.project_workflows.create_project("Target")
    link = planner.links.add(source.id, first.id, "depends-on")

    targets = planner.collaboration_queries.available_targets(source.id)
    resolved = planner.collaboration_queries.list_resolved(first.id)

    assert len({choice.label for choice in targets}) == len(targets)
    assert resolved[0].link == link
    assert resolved[0].other_project == source
    assert resolved[0].outgoing is False
    assert second.id in {choice.project_id for choice in targets}


def test_resource_links_can_be_queried_by_url_or_file_kind() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project("Resources")
    website = planner.resources.add(
        project.id,
        "Documentation",
        "https://example.com/docs",
        ResourceLinkKind.WEB,
    )
    specification = planner.resources.add(
        project.id,
        "Specification",
        "/tmp/specification.pdf",
        ResourceLinkKind.FILE,
    )

    assert planner.resources.list_for_project(project.id, ResourceLinkKind.WEB) == [website]
    assert planner.resources.list_for_project(project.id, ResourceLinkKind.FILE) == [specification]


def test_application_issues_are_persisted_and_reflected_in_health() -> None:
    planner = build_planner()
    try:
        raise RuntimeError("Simulated UI failure")
    except RuntimeError as error:
        issue = planner.issues.record_exception(error, "Regression test")

    assert planner.issues.list_recent() == [issue]
    health = planner.health.snapshot()
    assert health.database_healthy is True
    assert health.database_backend == "sqlite"
    assert health.issue_count == 1
