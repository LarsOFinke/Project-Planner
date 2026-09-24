from collections.abc import Callable

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.services.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner_frontend.artifacts.clients.ArtifactClient import ArtifactClient
from project_planner_frontend.artifacts.views.diagram.DiagramCanvas import DiagramCanvas
from project_planner_frontend.artifacts.views.diagram.DiagramToolbox import DiagramToolbox
from project_planner_frontend.artifacts.views.EditorSaveSession import EditorSaveSession
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.todos.TodoPanel import TodoPanel
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.dialogs import (
    open_confirmation_dialog,
    open_geometry_dialog,
    open_text_dialog,
    show_confirmation,
    show_error,
)
from project_planner_frontend.shared.EditorTodoTabs import EditorTodoTabs
from project_planner_frontend.shared.theme import NAVY_900, paint_background


class DiagramPanel(BoxLayout):
    def __init__(
        self,
        artifacts: ArtifactClient,
        documents: DiagramDocumentCodec,
        todos: TodoClient,
        autosave_seconds: float,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(10), dp(8)],
            **kwargs,
        )
        self._artifacts = artifacts
        self._documents = documents
        self._todos = todos
        self._artifact: Artifact | None = None
        self._project_id: str | None = None
        self._loading_project_id: str | None = None
        self._load_generation = 0
        paint_background(self, NAVY_900)
        self.toolbox = DiagramToolbox(
            add_node=self._add_node,
            rename_node=self._rename,
            edit_geometry=self._edit_geometry,
            connect_selected=self._connect,
            zoom=self.canvas_zoom,
            pan=self.canvas_pan,
            toggle_snap=self._toggle_snap,
            undo=self._undo,
            redo=self._redo,
            delete_selected=self._delete,
            clear_all=self._clear,
            save=self._save_now,
        )
        self.canvas_editor = DiagramCanvas(self._mark_dirty, self.toolbox.set_selection)
        self._save_session = EditorSaveSession(
            artifacts,
            lambda: self._documents.encode(self.canvas_editor.to_document()),
        )
        editor = BoxLayout(orientation="horizontal", spacing=dp(8))
        editor.add_widget(self.toolbox)
        editor.add_widget(self.canvas_editor)
        self.todo_panel = TodoPanel(self._todos)
        self.module_tabs = EditorTodoTabs("Canvas", editor, self.todo_panel)
        self.add_widget(self.module_tabs)
        self.disabled = True
        self._autosave_event = Clock.schedule_interval(self._autosave, autosave_seconds)

    def show_project(self, project_id: str) -> None:
        self.show_project_async(project_id)

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def loading_project_id(self) -> str | None:
        return self._loading_project_id

    def show_project_async(self, project_id: str) -> None:
        if self._loading_project_id == project_id:
            return
        self._load_generation += 1
        self._loading_project_id = project_id
        generation = self._load_generation
        self.disabled = True

        def fetch():
            artifact = self._artifacts.get_or_create(project_id, ArtifactKind.DIAGRAM)
            document = self._documents.decode(self._artifacts.read_json(artifact))
            return artifact, document

        def display(result: tuple[object, object]) -> None:
            if generation != self._load_generation:
                return
            self._artifact, document = result
            self._project_id = project_id
            self._loading_project_id = None
            self._save_session.bind_artifact(self._artifact)
            self.canvas_editor.load_document(document)
            self.todo_panel.show_context_async(
                project_id, TodoModule.DIAGRAM, title="Diagram To-Dos"
            )
            self.disabled = False

        self._save_session.save(
            after=lambda: run_background(
                fetch, display, lambda error: self._load_failed(error, generation)
            ),
            on_failure=lambda: self._load_failed(None, generation),
        )

    def _load_failed(self, error: Exception | None, generation: int) -> None:
        if generation != self._load_generation:
            return
        self._loading_project_id = None
        self.disabled = self._artifact is None
        if error is not None:
            show_error(f"Could not load diagram: {error}")

    def clear_project(self) -> None:
        self._load_generation += 1
        self._loading_project_id = None
        self.disabled = True

        def clear() -> None:
            self._save_session.clear()
            self._artifact = None
            self._project_id = None
            self.canvas_editor.clear_diagram(notify=False)
            self.todo_panel.clear_context()

        self._save_session.save(after=clear, on_failure=lambda: setattr(self, "disabled", False))

    def _add_node(self, *_: object) -> None:
        self.canvas_editor.add_node()

    def _rename(self, *_: object) -> None:
        if len(self.canvas_editor.selected_ids) == 1:
            open_text_dialog("Rename node", "Node label", self.canvas_editor.rename_selected)

    def _edit_geometry(self, *_: object) -> None:
        geometry = self.canvas_editor.selected_geometry()
        if geometry is not None:
            open_geometry_dialog(
                "Node position and size", geometry, self.canvas_editor.set_selected_geometry
            )

    def _connect(self, *_: object) -> None:
        self.canvas_editor.connect_selected()

    def _delete(self, *_: object) -> None:
        self.canvas_editor.delete_selected()

    def _clear(self, *_: object) -> None:
        open_confirmation_dialog(
            "Clear diagram",
            "Remove all nodes and connections? You can undo this until you leave the project.",
            self.canvas_editor.clear_diagram,
        )

    def canvas_zoom(self, factor: float) -> None:
        self.canvas_editor.zoom_by(factor)

    def canvas_pan(self, dx: float, dy: float) -> None:
        self.canvas_editor.pan_by(dx, dy)

    def _toggle_snap(self, *_: object) -> None:
        state = self.canvas_editor.toggle_snap()
        show_confirmation(f"Snap to 20-unit grid {'on' if state else 'off'}.")

    def _undo(self, *_: object) -> None:
        self.canvas_editor.undo()

    def _redo(self, *_: object) -> None:
        self.canvas_editor.redo()

    def _mark_dirty(self) -> None:
        self._save_session.mark_dirty()

    def _save(self, *_: object) -> bool:
        return self._save_session.save()

    def _save_now(self, *_: object) -> None:
        if self._save_session.dirty:
            self._save_session.save(after=lambda: show_confirmation("Diagram saved locally."))
        else:
            show_confirmation("Diagram is already up to date.")

    def _autosave(self, _elapsed: float) -> None:
        self._save()

    def dispose(self) -> None:
        self._save()
        self._autosave_event.cancel()

    def save_before_rebuild(
        self, after: Callable[[], None], on_failure: Callable[[], None]
    ) -> None:
        self._save_session.save(after=after, on_failure=on_failure)
