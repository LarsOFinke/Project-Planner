from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.core.application.artifacts.ArtifactService import ArtifactService
from project_planner.core.application.artifacts.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.domain.artifacts.Artifact import Artifact
from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.frontend.diagram.DiagramCanvas import DiagramCanvas
from project_planner.frontend.diagram.DiagramToolbox import DiagramToolbox
from project_planner.frontend.shared.dialogs import (
    open_text_dialog,
    show_confirmation,
)
from project_planner.frontend.shared.EditorTodoTabs import EditorTodoTabs
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    title_label,
)
from project_planner.frontend.todos.TodoPanel import TodoPanel


class DiagramPanel(BoxLayout):
    def __init__(
        self,
        artifacts: ArtifactService,
        documents: DiagramDocumentCodec,
        todos: TodoService,
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
        self._todos = todos
        self._artifact: Artifact | None = None
        self._dirty = False
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Diagram"))
        self.add_widget(
            caption_label("Select two nodes to connect them. Drag nodes to reorganize.")
        )
        toolbox = DiagramToolbox(
            add_node=self._add_node,
            rename_node=self._rename,
            connect_selected=self._connect,
            delete_selected=self._delete,
            clear_all=self._clear,
            save=self._save_now,
        )
        self.canvas_editor = DiagramCanvas(self._mark_dirty)
        editor = BoxLayout(orientation="vertical", spacing=dp(8))
        editor.add_widget(toolbox)
        editor.add_widget(self.canvas_editor)
        self.todo_panel = TodoPanel(self._todos)
        self.module_tabs = EditorTodoTabs("Canvas", editor, self.todo_panel)
        self.add_widget(self.module_tabs)
        self.disabled = True
        self._autosave_event = Clock.schedule_interval(self._autosave, autosave_seconds)

    def show_project(self, project_id: str) -> None:
        self._save()
        self._artifact = self._artifacts.get_or_create(project_id, ArtifactKind.DIAGRAM)
        self.canvas_editor.load_document(
            self._documents.decode(self._artifacts.read_json(self._artifact))
        )
        self._dirty = False
        self.todo_panel.show_context(
            project_id,
            TodoModule.DIAGRAM,
            title="Diagram To-Dos",
        )
        self.disabled = False

    def _add_node(self, *_: object) -> None:
        self.canvas_editor.add_node()

    def _rename(self, *_: object) -> None:
        if len(self.canvas_editor.selected_ids) == 1:
            open_text_dialog("Rename node", "Node label", self.canvas_editor.rename_selected)

    def _connect(self, *_: object) -> None:
        self.canvas_editor.connect_selected()

    def _delete(self, *_: object) -> None:
        self.canvas_editor.delete_selected()

    def _clear(self, *_: object) -> None:
        self.canvas_editor.clear_diagram()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _save(self, *_: object) -> bool:
        if self._artifact is not None and self._dirty:
            self._artifact = self._artifacts.save_json(
                self._artifact,
                self._documents.encode(self.canvas_editor.to_document()),
            )
            self._dirty = False
            return True
        return False

    def _save_now(self, *_: object) -> None:
        saved = self._save()
        message = "Diagram saved locally." if saved else "Diagram is already up to date."
        show_confirmation(message)

    def _autosave(self, _elapsed: float) -> None:
        self._save()

    def dispose(self) -> None:
        self._save()
        self._autosave_event.cancel()
