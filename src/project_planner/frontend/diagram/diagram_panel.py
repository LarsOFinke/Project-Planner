from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from project_planner.core.bootstrap.application_container import ApplicationContainer
from project_planner.core.domain.artifacts.artifact import Artifact
from project_planner.core.domain.artifacts.artifact_kind import ArtifactKind
from project_planner.frontend.diagram.diagram_canvas import DiagramCanvas
from project_planner.frontend.shared.dialogs import open_text_dialog
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    style_button,
    title_label,
)


class DiagramPanel(BoxLayout):
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
        toolbar = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        actions = [
            ("+ Node", self._add_node, "primary"),
            ("Rename", self._rename, "secondary"),
            ("Connect selected", self._connect, "secondary"),
            ("Delete", self._delete, "danger"),
            ("Clear all", self._clear, "danger"),
            ("Save now", self._save, "secondary"),
        ]
        for title, callback, variant in actions:
            button = style_button(Button(text=title), variant)
            button.bind(on_release=callback)
            toolbar.add_widget(button)
        self.canvas_editor = DiagramCanvas(self._mark_dirty)
        self.add_widget(toolbar)
        self.add_widget(self.canvas_editor)
        self.disabled = True
        Clock.schedule_interval(
            self._autosave, self._container.settings.autosave_seconds
        )

    def show_project(self, project_id: str) -> None:
        self._save()
        self._artifact = self._container.artifacts.get_or_create(
            project_id, ArtifactKind.DIAGRAM
        )
        self.canvas_editor.load_data(
            self._container.artifacts.read_json(self._artifact)
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
            self._artifact = self._container.artifacts.save_json(
                self._artifact, self.canvas_editor.to_data()
            )
            self._dirty = False

    def _autosave(self, _elapsed: float) -> None:
        self._save()
