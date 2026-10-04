from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner.shared.database.Database import Database
from project_planner.shared.settings.Settings import Settings
from tests.support import build_test_services


@pytest.mark.parametrize("operation", ["create", "update", "reset"])
def test_project_workflow_rolls_back_phase_failure(tmp_path, monkeypatch, operation) -> None:
    settings = Settings(tmp_path / "planner.sqlite3", 1280, 800, 20)
    planner = build_test_services(settings)
    method = PlanningMethod.WATERFALL if operation == "reset" else PlanningMethod.CUSTOM
    project = planner.project_workflows.create_project("Existing", planning_method=method)
    phases_before = list(planner.phases.list_for_project(project.id))
    if phases_before:
        planner.todos.add(
            project.id, "Keep me", module=TodoModule.PHASES, phase_id=phases_before[0].id
        )
    todos_before = list(planner.todos.list_for_project(project.id))
    repository = planner.phases._phases
    original = repository.save_all

    def fail_after_write(*args):
        original(*args)
        raise RuntimeError("phase write failed")

    with monkeypatch.context() as patch:
        patch.setattr(repository, "save_all", fail_after_write)
        with pytest.raises(RuntimeError, match="phase write failed"):
            if operation == "create":
                planner.project_workflows.create_project(
                    "Incomplete", planning_method=PlanningMethod.WATERFALL
                )
            elif operation == "update":
                planner.project_workflows.update_project(
                    project.id,
                    title="Changed",
                    description="Changed",
                    status=project.status,
                    planning_method=PlanningMethod.WATERFALL,
                    parent_id=None,
                )
            else:
                planner.project_workflows.reset_phase_plan(project.id)

    reopened = build_test_services(settings)
    assert reopened.projects.list_all() == [project]
    assert list(reopened.phases.list_for_project(project.id)) == phases_before
    assert list(reopened.todos.list_for_project(project.id)) == todos_before
    # A failed workflow must not leave a failed session attached to this context.
    created = planner.project_workflows.create_project(
        "Complete", planning_method=PlanningMethod.WATERFALL
    )
    assert len(reopened.phases.list_for_project(created.id)) == 4


def test_workflow_sessions_are_isolated_between_threads(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    barrier = Barrier(2)

    def read_session():
        with database.transaction(), database.session() as session:
            barrier.wait(timeout=5)
            with database.session() as nested:
                assert nested is session
            return session

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(read_session)
        second = executor.submit(read_session)
        assert first.result(timeout=10) is not second.result(timeout=10)
    with database.session() as fresh:
        assert fresh is not first.result()
