from types import SimpleNamespace

from project_planner_frontend.projects.views import OverviewPanel as overview_module
from project_planner_frontend.projects.views.OverviewPanel import OverviewPanel
from project_planner_frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot

from project_planner.api.projects.dtos.ProjectChoice import ProjectChoice
from project_planner.api.projects.dtos.ProjectOverview import ProjectOverview
from project_planner.modules.projects.entities.Project import Project


def build_panel(monkeypatch):
    queued, calls, saved, errors = [], [], [], []
    project = Project("Initial")

    def update(project_id, **changes):
        calls.append((project_id, changes))
        return project.revise(**changes)

    monkeypatch.setattr(
        overview_module, "run_background", lambda *callbacks: queued.append(callbacks)
    )
    monkeypatch.setattr(overview_module, "show_confirmation", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(overview_module, "show_error", errors.append)
    panel = OverviewPanel(
        SimpleNamespace(update_project=update), None, None, None, lambda *_: None, saved.append
    )
    panel._display_overview(ProjectOverview(project, (ProjectChoice(None, "No parent"),)))
    return panel, project, queued, calls, saved, errors


def test_overview_save_uses_snapshot_and_waits_without_blocking(monkeypatch) -> None:
    panel, project, queued, calls, saved, errors = build_panel(monkeypatch)
    panel.title_input.text = "Updated"
    panel._save()
    panel._save()
    assert not calls and len(queued) == 1
    assert panel.disabled and panel._save_button.disabled
    finished = []
    panel.wait_for_save(lambda: finished.append(True), lambda: finished.append(False))
    assert not finished
    panel.title_input.text = "Later mutation"
    operation, completed, _failed = queued.pop()
    completed(operation())
    assert calls[0][1]["title"] == "Updated"
    assert panel._project.title == "Updated"
    assert saved == [project.id] and finished == [True] and not errors
    assert not panel.disabled and not panel._save_button.disabled


def test_overview_failed_save_preserves_form_and_allows_retry(monkeypatch) -> None:
    panel, _project, queued, _calls, saved, errors = build_panel(monkeypatch)
    panel.title_input.text = "Retain these changes"
    panel._save()
    finished = []
    panel.wait_for_save(lambda: finished.append(True), lambda: finished.append(False))
    queued.pop()[2](TimeoutError("offline"))
    assert finished == [False] and not saved and errors
    assert panel.title_input.text == "Retain these changes"
    assert not panel.disabled
    panel._save()
    operation, completed, _failed = queued.pop()
    completed(operation())
    assert panel._project.title == "Retain these changes"


def test_overview_save_completion_does_not_replace_new_selection(monkeypatch) -> None:
    panel, project, queued, _calls, saved, _errors = build_panel(monkeypatch)
    panel._save()
    other = Project("Other")
    panel.clear_project()
    panel._display_overview(ProjectOverview(other, (ProjectChoice(None, "No parent"),)))
    operation, completed, _failed = queued.pop()
    completed(operation())
    assert panel._project == other and panel.title_input.text == "Other"
    assert not panel.disabled and saved == [project.id]
    refreshed = []
    root = SimpleNamespace(
        browser=SimpleNamespace(refresh_async=lambda: refreshed.append(True)),
        _selected_project_id=other.id,
        _loaded_project_by_tab={"Overview": other.id},
    )
    ProjectPlannerRoot._project_saved(root, project.id)
    assert root._selected_project_id == other.id
    assert root._loaded_project_by_tab == {"Overview": other.id}
    assert refreshed == [True]


def test_overview_invalid_date_does_not_start_request(monkeypatch) -> None:
    panel, _project, queued, calls, _saved, _errors = build_panel(monkeypatch)
    panel.start_date.text = "invalid"
    panel._save()
    assert not queued and not calls and not panel.disabled
