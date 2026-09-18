from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.services.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner_frontend.artifacts.clients.ArtifactClient import ArtifactClient
from project_planner_frontend.artifacts.clients.ImageAssetClient import ImageAssetClient
from project_planner_frontend.artifacts.views.workspace.FreehandCanvas import FreehandCanvas
from project_planner_frontend.artifacts.views.workspace.WorkspaceMode import WorkspaceMode
from project_planner_frontend.artifacts.views.workspace.WorkspaceToolbox import WorkspaceToolbox
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.todos.TodoPanel import TodoPanel
from project_planner_frontend.shared.dialogs import (
    open_image_dialog,
    show_confirmation,
)
from project_planner_frontend.shared.EditorTodoTabs import EditorTodoTabs
from project_planner_frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    title_label,
)


class WorkspacePanel(BoxLayout):
    def __init__(
        self,
        artifacts: ArtifactClient,
        documents: WorkspaceDocumentCodec,
        images: ImageAssetClient,
        todos: TodoClient,
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
        self._images = images
        self._todos = todos
        self._artifact: Artifact | None = None
        self._project_id: str | None = None
        self._dirty = False
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Free workspace"))
        self.add_widget(
            caption_label(
                "Use Select to edit objects or Draw for freehand strokes. Changes autosave locally."
            )
        )
        toolbox = WorkspaceToolbox(
            add_shape=self._add_shape,
            choose_image=self._choose_image,
            rotate=self._rotate,
            scale=self._scale,
            set_color=self._set_color,
            set_mode=self._set_mode,
            delete_selected=self._delete_selected,
            clear_all=self._clear,
            save=self._save_now,
        )
        self.canvas_editor = FreehandCanvas(self._mark_dirty)
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
        self._project_id = project_id
        self._artifact = self._artifacts.get_or_create(project_id, ArtifactKind.WORKSPACE)
        self.canvas_editor.load_document(
            self._documents.decode(self._artifacts.read_json(self._artifact))
        )
        self._dirty = False
        self.todo_panel.show_context(
            project_id,
            TodoModule.WORKSPACE,
            title="Workspace To-Dos",
        )
        self.disabled = False

    def _add_shape(self, kind: str) -> None:
        self.canvas_editor.add_shape(kind)

    def _choose_image(self, *_: object) -> None:
        if self._project_id is not None:
            open_image_dialog(self._import_image)

    def _import_image(self, source: str) -> None:
        if self._project_id is None:
            return
        managed = self._images.import_image(self._project_id, source)
        self.canvas_editor.add_image(str(managed))

    def _delete_selected(self, *_: object) -> None:
        self.canvas_editor.delete_selected()

    def _rotate(self, degrees: float) -> None:
        self.canvas_editor.rotate_selected(degrees)

    def _scale(self, factor: float) -> None:
        self.canvas_editor.scale_selected(factor)

    def _set_color(self, color: str) -> None:
        self.canvas_editor.set_color(color)

    def _set_mode(self, mode: WorkspaceMode) -> None:
        self.canvas_editor.set_mode(mode)

    def _clear(self, *_: object) -> None:
        self.canvas_editor.clear_drawing()

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
        message = "Workspace saved locally." if saved else "Workspace is already up to date."
        show_confirmation(message)

    def _autosave(self, _elapsed: float) -> None:
        self._save()

    def dispose(self) -> None:
        self._save()
        self._autosave_event.cancel()
