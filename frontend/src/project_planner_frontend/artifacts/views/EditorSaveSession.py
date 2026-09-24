from collections.abc import Callable

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner_frontend.artifacts.clients.ArtifactClient import ArtifactClient
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.dialogs import show_error


class EditorSaveSession:
    """Serialize editor saves and keep failed or newer edits dirty."""

    def __init__(self, artifacts: ArtifactClient, snapshot: Callable[[], object]) -> None:
        self._artifacts = artifacts
        self._snapshot = snapshot
        self.artifact: Artifact | None = None
        self._revision = 0
        self._saved_revision = 0
        self._saving = False
        self._after_save: list[Callable[[], None]] = []
        self._on_failure: list[Callable[[], None]] = []

    @property
    def dirty(self) -> bool:
        return self._revision != self._saved_revision

    def bind_artifact(self, artifact: Artifact) -> None:
        if self._saving or self.dirty:
            raise RuntimeError("Cannot replace an editor with unsaved changes")
        self.artifact = artifact
        self._revision = self._saved_revision = 0

    def clear(self) -> None:
        if self._saving or self.dirty:
            raise RuntimeError("Cannot clear an editor with unsaved changes")
        self.artifact = None
        self._revision = self._saved_revision = 0

    def mark_dirty(self) -> None:
        self._revision += 1

    def save(
        self, after: Callable[[], None] | None = None, on_failure: Callable[[], None] | None = None
    ) -> bool:
        if after is not None:
            self._after_save.append(after)
        if on_failure is not None:
            self._on_failure.append(on_failure)
        if self._saving:
            return True
        if not self.dirty or self.artifact is None:
            callbacks, self._after_save = self._after_save, []
            self._on_failure.clear()
            for callback in callbacks:
                callback()
            return False
        artifact = self.artifact
        revision = self._revision
        payload = self._snapshot()
        self._saving = True

        def completed(saved: Artifact) -> None:
            self.artifact = saved
            self._saved_revision = revision
            self._saving = False
            self.save()

        def failed(error: Exception) -> None:
            self._saving = False
            self._after_save.clear()
            callbacks, self._on_failure = self._on_failure, []
            for callback in callbacks:
                callback()
            show_error(f"Could not save editor changes; they remain open for retry: {error}")

        run_background(lambda: self._artifacts.save_json(artifact, payload), completed, failed)
        return True
