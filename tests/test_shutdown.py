from pathlib import Path
from types import MethodType, SimpleNamespace

import pytest
from kivy.app import App
from project_planner_frontend.application.ProjectPlannerApp import ProjectPlannerApp
from project_planner_frontend.application.ProjectPlannerHost import ProjectPlannerHost
from project_planner_frontend.artifacts.views import EditorSaveSession as save_module
from project_planner_frontend.artifacts.views.EditorSaveSession import EditorSaveSession
from project_planner_frontend.artifacts.views.workspace.WorkspacePanel import WorkspacePanel
from project_planner_frontend.shell.ProjectPlannerRoot import ProjectPlannerRoot

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.shared.settings.Settings import Settings


def build_shutdown_app(monkeypatch):
    queued, events = [], []
    monkeypatch.setattr(save_module, "run_background", lambda *callbacks: queued.append(callbacks))
    monkeypatch.setattr(save_module, "show_error", lambda message: events.append("error"))
    monkeypatch.setattr(ProjectPlannerHost, "rebuild", lambda *_: None)
    app = ProjectPlannerApp(Settings(Path(":memory:"), 1280, 800, 20))
    host = ProjectPlannerHost(None, 20, 1, False, lambda *_: None, lambda *_: None)

    def editor(kind):
        client = SimpleNamespace(save_json=lambda artifact, payload: artifact)
        session = EditorSaveSession(client, lambda: {"revision": session._revision})
        session.bind_artifact(Artifact("project", kind.value, kind))
        session.mark_dirty()
        return SimpleNamespace(
            disabled=False,
            project_id="project",
            save_before_rebuild=session.save,
            session=session,
        )

    root = SimpleNamespace(
        diagram=editor(ArtifactKind.DIAGRAM),
        workspace=editor(ArtifactKind.WORKSPACE),
        overview=SimpleNamespace(wait_for_save=lambda after, failed: after()),
        dispose=lambda: events.append("disposed"),
    )
    root.save_editors_before_rebuild = MethodType(
        ProjectPlannerRoot.save_editors_before_rebuild, root
    )
    host._planner_root = root
    app._host = host
    app._clients = SimpleNamespace(close=lambda: events.append("client closed"))
    app._api_server = SimpleNamespace(stop=lambda: events.append("server stopped"))
    monkeypatch.setattr(App, "stop", lambda self, *_: self.on_stop())
    return app, root, queued, events


def test_shutdown_waits_for_active_and_newer_editor_saves(monkeypatch) -> None:
    app, root, queued, events = build_shutdown_app(monkeypatch)
    root.diagram.session.save()
    root.diagram.session.mark_dirty()
    assert app._request_window_close() is True
    app.stop()  # Repeated close requests must not enqueue duplicate work.
    assert len(queued) == 1 and not events and app._host.disabled

    for _ in range(2):
        operation, completed, _failed = queued.pop(0)
        completed(operation())
        assert not events
    assert not root.diagram.session.dirty
    assert root.workspace.session.dirty
    operation, completed, _failed = queued.pop(0)
    completed(operation())
    assert not root.workspace.session.dirty
    assert events == ["disposed", "client closed", "server stopped"]
    app.on_stop()  # Kivy dispatches on_stop again after its event loop exits.
    assert events == ["disposed", "client closed", "server stopped"]


@pytest.mark.parametrize("failed_editor", ["diagram", "workspace"])
def test_shutdown_failure_keeps_app_open_and_allows_retry(monkeypatch, failed_editor) -> None:
    app, root, queued, events = build_shutdown_app(monkeypatch)
    app.stop()
    if failed_editor == "workspace":
        operation, completed, _failed = queued.pop(0)
        completed(operation())
    queued.pop(0)[2](TimeoutError("offline"))
    assert events == ["error"]
    assert getattr(root, failed_editor).session.dirty
    assert not app._close_requested and not app._host.disabled
    assert not root.diagram.disabled and not root.workspace.disabled
    app.stop()
    while queued:
        operation, completed, _failed = queued.pop(0)
        completed(operation())
    assert events == ["error", "disposed", "client closed", "server stopped"]


@pytest.mark.parametrize("success", [True, False])
def test_shutdown_waits_for_image_import_and_aborts_on_failure(success) -> None:
    events = []
    panel = SimpleNamespace(
        _pending_image_import=True,
        _import_waiters=[],
        _deferred_navigation=None,
        _save_session=SimpleNamespace(save=lambda **kwargs: events.append("save")),
    )
    panel.save_before_rebuild = MethodType(WorkspacePanel.save_before_rebuild, panel)
    panel.save_before_rebuild(lambda: events.append("closed"), lambda: events.append("failed"))
    assert not events
    WorkspacePanel._finish_image_import(panel, success=success)
    assert events == (["save"] if success else ["failed"])
