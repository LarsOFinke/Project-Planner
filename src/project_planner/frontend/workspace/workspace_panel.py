from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.core.bootstrap.application_container import ApplicationContainer
from project_planner.core.domain.artifacts.artifact import Artifact
from project_planner.core.domain.artifacts.artifact_kind import ArtifactKind
from project_planner.frontend.shared.dialogs import open_image_dialog
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    title_label,
)
from project_planner.frontend.workspace.freehand_canvas import FreehandCanvas
from project_planner.frontend.workspace.workspace_toolbox import WorkspaceToolbox


class WorkspacePanel(BoxLayout):
    def __init__(
        self, container: ApplicationContainer, **kwargs: object
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(18), dp(14)],
            **kwargs,
        )
        self._container = container
        self._artifact: Artifact | None = None
        self._project_id: str | None = None
        self._dirty = False
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Free workspace"))
        self.add_widget(
            caption_label(
                "Draw freely or place movable shapes and images. Changes autosave locally."
            )
        )
        toolbox = WorkspaceToolbox(
            add_shape=self._add_shape,
            choose_image=self._choose_image,
            rotate=self._rotate,
            scale=self._scale,
            delete_selected=self._delete_selected,
            clear_all=self._clear,
            save=self._save,
        )
        self.canvas_editor = FreehandCanvas(self._mark_dirty)
        self.add_widget(toolbox)
        self.add_widget(self.canvas_editor)
        self.disabled = True
        Clock.schedule_interval(
            self._autosave, self._container.settings.autosave_seconds
        )

    def show_project(self, project_id: str) -> None:
        self._save()
        self._project_id = project_id
        self._artifact = self._container.artifacts.get_or_create(
            project_id, ArtifactKind.WORKSPACE
        )
        self.canvas_editor.load_data(
            self._container.artifacts.read_json(self._artifact)
        )
        self._dirty = False
        self.disabled = False

    def _add_shape(self, kind: str) -> None:
        self.canvas_editor.add_shape(kind)

    def _choose_image(self, *_: object) -> None:
        if self._project_id is not None:
            open_image_dialog(self._import_image)

    def _import_image(self, source: str) -> None:
        if self._project_id is None:
            return
        managed = self._container.images.import_image(self._project_id, source)
        self.canvas_editor.add_image(str(managed))

    def _delete_selected(self, *_: object) -> None:
        self.canvas_editor.delete_selected()

    def _rotate(self, degrees: float) -> None:
        self.canvas_editor.rotate_selected(degrees)

    def _scale(self, factor: float) -> None:
        self.canvas_editor.scale_selected(factor)

    def _clear(self, *_: object) -> None:
        self.canvas_editor.clear_drawing()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _save(self, *_: object) -> None:
        if self._artifact is not None and self._dirty:
            self._artifact = self._container.artifacts.save_json(
                self._artifact, self.canvas_editor.to_data()
            )
            self._dirty = False

    def _autosave(self, _elapsed: float) -> None:
        self._save()
