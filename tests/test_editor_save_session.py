from project_planner_frontend.artifacts.views import EditorSaveSession as save_module
from project_planner_frontend.artifacts.views.EditorSaveSession import EditorSaveSession

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind


def test_save_session_serializes_revisions_and_runs_navigation_last(monkeypatch) -> None:
    queued = []
    writes = []

    def schedule(operation, completed, failed):
        queued.append((operation, completed, failed))

    monkeypatch.setattr(save_module, "run_background", schedule)
    artifact = Artifact("project", "Diagram", ArtifactKind.DIAGRAM)
    session = EditorSaveSession(None, lambda: {"revision": session._revision})
    session.bind_artifact(artifact)
    session._artifacts = type(
        "Client", (), {"save_json": lambda _self, a, data: writes.append(data) or a}
    )()
    session.mark_dirty()
    session.save()
    session.mark_dirty()
    called = []
    session.save(after=lambda: called.append("navigated"))
    assert len(queued) == 1
    operation, completed, _failed = queued.pop()
    completed(operation())
    assert session.dirty and len(queued) == 1 and not called
    operation, completed, _failed = queued.pop()
    completed(operation())
    assert writes == [{"revision": 1}, {"revision": 2}]
    assert not session.dirty and called == ["navigated"]


def test_save_session_keeps_failed_revision_open(monkeypatch) -> None:
    queued = []
    errors = []
    monkeypatch.setattr(
        save_module,
        "run_background",
        lambda operation, completed, failed: queued.append((operation, completed, failed)),
    )
    monkeypatch.setattr(save_module, "show_error", errors.append)
    session = EditorSaveSession(None, lambda: {"value": 1})
    session.bind_artifact(Artifact("project", "Workspace", ArtifactKind.WORKSPACE))
    session.mark_dirty()
    navigated = []
    session.save(after=lambda: navigated.append(True))
    queued.pop()[2](TimeoutError("timeout"))
    assert session.dirty and not navigated
    assert errors and "timeout" in errors[0]
