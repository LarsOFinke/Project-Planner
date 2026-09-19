from datetime import date
from pathlib import Path
from types import SimpleNamespace

from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.shared.settings.Settings import Settings
from tests.support import build_test_services


def build_planner() -> SimpleNamespace:
    return build_test_services(Settings(Path(":memory:"), 1280, 800, 20))


def test_agile_backlog_sprint_completion_and_history() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project(
        "Iterative", planning_method=PlanningMethod.AGILE
    )
    first = planner.agile.add_item(
        project.id, "First", priority=BacklogPriority.HIGH, assignee="Ada"
    )
    second = planner.agile.add_item(project.id, "Second")
    third = planner.agile.add_item(project.id, "Third")
    planner.agile.move_item(project.id, second.id, -1)
    sprint = planner.agile.add_sprint(
        project.id,
        "Sprint 1",
        date(2026, 9, 1),
        date(2026, 9, 14),
        "Ship the first slice",
        [first.id, second.id],
    )
    next_sprint = planner.agile.add_sprint(
        project.id,
        "Sprint 2",
        date(2026, 9, 15),
        date(2026, 9, 28),
        "Ship the next slice",
        [third.id],
    )
    planner.agile.update_item(
        planner.agile.list_items(project.id)[1],
        title=first.title,
        description=first.description,
        priority=first.priority,
        status=BacklogStatus.DONE,
        assignee=first.assignee,
    )

    planner.agile.complete_sprint(project.id, sprint.id)
    items = {item.id: item for item in planner.agile.list_items(project.id)}

    assert items[first.id].status is BacklogStatus.DONE
    assert items[second.id].status is BacklogStatus.BACKLOG
    assert items[second.id].sprint_id is None
    assert items[third.id].sprint_id == next_sprint.id
    assert planner.agile.sprint_history(project.id)[0].id == sprint.id
    assert planner.agile.planned_sprints(project.id) == [next_sprint]
    assert [item.id for item in planner.agile.list_sprint_items(project.id, sprint.id)] == [
        first.id
    ]


def test_waterfall_phases_tasks_and_timeline_data_are_persisted() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project(
        "Sequential", planning_method=PlanningMethod.WATERFALL
    )
    phase = planner.phases.list_for_context(project.id)[0]
    updated_phase = planner.phases.update(
        phase.id,
        project.id,
        phase.name,
        "Define the plan",
        PhaseStatus.IN_PROGRESS,
        date(2026, 9, 1),
        date(2026, 9, 5),
        parallel_group="Discovery lane",
    )
    task = planner.waterfall_tasks.add(
        phase.id,
        "Write brief",
        assignee="Grace",
        start_date=date(2026, 9, 1),
        due_date=date(2026, 9, 2),
        status=WaterfallTaskStatus.IN_PROGRESS,
    )

    assert updated_phase.start_date == date(2026, 9, 1)
    assert updated_phase.parallel_group == "Discovery lane"
    assert planner.waterfall_tasks.list_for_phase(phase.id) == [task]


def test_custom_sections_mix_models_reorder_and_preserve_content() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project(
        "Mixed", planning_method=PlanningMethod.CUSTOM
    )
    free = planner.sections.add(project.id, "Approval", SectionType.FREE)
    agile = planner.sections.add(project.id, "Research", SectionType.AGILE)
    waterfall = planner.sections.add(project.id, "Delivery", SectionType.WATERFALL)
    free_item = planner.sections.add_item(
        free.id, "Confirm wording", status=SectionStatus.IN_PROGRESS
    )
    planner.agile.add_item(project.id, "Interview users", section_id=agile.id)
    planner.sections.move(project.id, waterfall.id, -2)

    phases = planner.phases.list_for_context(project.id, waterfall.id)
    assert [phase.name for phase in phases] == [
        "Planning",
        "Design",
        "Execution",
        "Completion",
    ]
    assert planner.sections.list_for_project(project.id)[0].id == waterfall.id

    planner.sections.update(
        free.id,
        name=free.name,
        description=free.description,
        section_type=SectionType.WATERFALL,
        start_date=None,
        end_date=None,
        status=free.status,
    )

    assert planner.sections.list_items(free.id) == [free_item]
    assert len(planner.phases.list_for_context(project.id, free.id)) == 4

    planner.sections.remove(agile.id)
    replacement = planner.sections.add(project.id, "Launch", SectionType.FREE)
    assert [section.position for section in planner.sections.list_for_project(project.id)] == [
        0,
        1,
        2,
    ]
    planner.sections.remove_item(free_item.id)
    replacement_item = planner.sections.add_item(replacement.id, "Publish")
    assert replacement_item.position == 0


def test_custom_agile_section_persists_a_planned_sprint() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project(
        "Mixed sprint", planning_method=PlanningMethod.CUSTOM
    )
    agile = planner.sections.add(project.id, "Research", SectionType.AGILE)
    backlog_item = planner.agile.add_item(
        project.id,
        "Interview users",
        section_id=agile.id,
    )

    sprint = planner.agile.add_sprint(
        project.id,
        "Discovery sprint",
        date(2026, 9, 9),
        date(2026, 9, 26),
        "Validate the problem",
        [backlog_item.id],
        agile.id,
    )

    assert planner.agile.planned_sprints(project.id, agile.id) == [sprint]
    assert planner.agile.list_items(project.id, agile.id)[0].sprint_id == sprint.id


def test_shared_project_setup_metadata_round_trips() -> None:
    planner = build_planner()
    project = planner.project_workflows.create_project(
        "Metadata",
        description="Small and focused",
        start_date=date(2026, 9, 1),
        target_date=date(2026, 10, 1),
        owner="Owner",
        assignee="Assignee",
        notes="One notes area",
    )

    restored = planner.projects.require(project.id)
    assert restored.start_date == date(2026, 9, 1)
    assert restored.target_date == date(2026, 10, 1)
    assert (restored.owner, restored.assignee, restored.notes) == (
        "Owner",
        "Assignee",
        "One notes area",
    )
