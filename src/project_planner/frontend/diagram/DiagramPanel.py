from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.core.application.artifacts.ArtifactService import ArtifactService
from project_planner.core.application.artifacts.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.core.domain.artifacts.Artifact import Artifact
from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.frontend.diagram.DiagramCanvas import DiagramCanvas
from project_planner.frontend.diagram.DiagramToolbox import DiagramToolbox
from project_planner.frontend.shared.dialogs import open_text_dialog
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    title_label,
)


class DiagramPanel(BoxLayout):
    def __init__(
        self,
        artifacts: ArtifactService,
        documents: DiagramDocumentCodec,
        autosave_seconds: float,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(18), dp(14)],
            **kwargs,
        )
        self._artifacts = artifacts
        self._documents = documents
        self._artifact: Artifact | None = None
        self._dirty = False
        paint_background(self, NAVY_900)
        heading = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(8))
        heading_text = BoxLayout(orientation="vertical")
        heading_text.add_widget(title_label("Diagram"))
        heading_text.add_widget(
            caption_label("Select two nodes to connect them. Drag nodes to reorganize.")
        )
        heading.add_widget(heading_text)
        self.add_widget(heading)
        toolbox = DiagramToolbox(
            add_node=self._add_node,
            rename_node=self._rename,
            connect_selected=self._connect,
            delete_selected=self._delete,
            clear_all=self._clear,
            save=self._save,
        )
        self.canvas_editor = DiagramCanvas(self._mark_dirty)
        self.add_widget(toolbox)
        self.add_widget(self.canvas_editor)
        self.disabled = True
        self._autosave_event = Clock.schedule_interval(
            self._autosave, autosave_seconds
        )

    def show_project(self, project_id: str) -> None:
        self._save()
        self._artifact = self._artifacts.get_or_create(
            project_id, ArtifactKind.DIAGRAM
        )
        self.canvas_editor.load_document(
            self._documents.decode(self._artifacts.read_json(self._artifact))
        )
        self._dirty = False
        self.disabled = False

    def _add_node(self, *_: object) -> None:
        self.canvas_editor.add_node()

    def _rename(self, *_: object) -> None:
        if len(self.canvas_editor.selected_ids) == 1:
            open_text_dialog(
                "Rename node", "Node label", self.canvas_editor.rename_selected
            )

    def _connect(self, *_: object) -> None:
        self.canvas_editor.connect_selected()

    def _delete(self, *_: object) -> None:
        self.canvas_editor.delete_selected()

    def _clear(self, *_: object) -> None:
        self.canvas_editor.clear_diagram()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _save(self, *_: object) -> None:
        if self._artifact is not None and self._dirty:
            self._artifact = self._artifacts.save_json(
                self._artifact,
                self._documents.encode(self.canvas_editor.to_document()),
            )
            self._dirty = False

    def _autosave(self, _elapsed: float) -> None:
        self._save()

    def dispose(self) -> None:
        self._save()
        self._autosave_event.cancel()
