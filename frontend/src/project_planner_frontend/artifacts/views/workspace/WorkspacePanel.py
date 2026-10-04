from collections.abc import Callable

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
from project_planner_frontend.artifacts.views.EditorSaveSession import EditorSaveSession
from project_planner_frontend.artifacts.views.workspace.FreehandCanvas import FreehandCanvas
from project_planner_frontend.artifacts.views.workspace.WorkspaceMode import WorkspaceMode
from project_planner_frontend.artifacts.views.workspace.WorkspaceToolbox import WorkspaceToolbox
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.todos.TodoPanel import TodoPanel
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.dialogs import (
    open_choice_dialog,
    open_confirmation_dialog,
    open_geometry_dialog,
    open_image_dialog,
    open_text_dialog,
    show_confirmation,
    show_error,
)
from project_planner_frontend.shared.EditorTodoTabs import EditorTodoTabs
from project_planner_frontend.shared.theme import NAVY_900, paint_background


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
            padding=[dp(10), dp(8)],
            **kwargs,
        )
        self._artifacts = artifacts
        self._documents = documents
        self._images = images
        self._todos = todos
        self._artifact: Artifact | None = None
        self._project_id: str | None = None
        self._loading_project_id: str | None = None
        self._load_generation = 0
        self._pending_image_import = False
        self._import_waiters: list[tuple[Callable[[], None], Callable[[], None]]] = []
        self._deferred_navigation: Callable[[], None] | None = None
        paint_background(self, NAVY_900)
        self.toolbox = WorkspaceToolbox(
            add_shape=self._add_shape,
            choose_image=self._choose_image,
            add_text=self._add_text,
            edit_text=self._edit_text,
            edit_geometry=self._edit_geometry,
            rotate=self._rotate,
            scale=self._scale,
            zoom=self.canvas_zoom,
            pan=self.canvas_pan,
            toggle_snap=self._toggle_snap,
            undo=self._undo,
            redo=self._redo,
            set_color=self._set_color,
            set_mode=self._set_mode,
            delete_selected=self._delete_selected,
            clear_all=self._clear,
            save=self._save_now,
            revisions=self._show_revisions,
        )
        self.canvas_editor = FreehandCanvas(self._mark_dirty, self.toolbox.set_selection)
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
        if self._pending_image_import:
            self._deferred_navigation = lambda: self.show_project_async(project_id)
            self.disabled = True
            return
        self._load_generation += 1
        self._loading_project_id = project_id
        generation = self._load_generation
        self.disabled = True

        def fetch():
            artifact = self._artifacts.get_or_create(project_id, ArtifactKind.WORKSPACE)
            document = self._documents.decode(self._artifacts.read_json(artifact))
            for image in document.images:
                self._images.materialize(project_id, image.source)
            return artifact, document

        def display(result: tuple[object, object]) -> None:
            if generation != self._load_generation:
                return
            self._project_id = project_id
            self._loading_project_id = None
            self._artifact, document = result
            self._save_session.bind_artifact(self._artifact)
            self.canvas_editor.load_document(
                document,
                lambda source: str(self._images.materialize(project_id, source)),
            )
            self.todo_panel.show_context_async(
                project_id, TodoModule.WORKSPACE, title="Workspace To-Dos"
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
            show_error(f"Could not load workspace: {error}")

    def clear_project(self) -> None:
        if self._pending_image_import:
            self._deferred_navigation = self.clear_project
            self.disabled = True
            return
        self._load_generation += 1
        self._loading_project_id = None
        self.disabled = True

        def clear() -> None:
            self._save_session.clear()
            self._artifact = None
            self._project_id = None
            self.canvas_editor.clear_drawing(notify=False)
            self.todo_panel.clear_context()

        self._save_session.save(after=clear, on_failure=lambda: setattr(self, "disabled", False))

    def _add_shape(self, kind: str) -> None:
        self.canvas_editor.add_shape(kind)

    def _add_text(self, *_: object) -> None:
        open_text_dialog("Add canvas text", "Text", self.canvas_editor.add_text, multiline=True)

    def _edit_text(self, *_: object) -> None:
        current = self.canvas_editor.selected_text()
        if current is not None:
            open_text_dialog(
                "Edit canvas text",
                "Text",
                self.canvas_editor.edit_selected_text,
                initial=current,
                multiline=True,
            )

    def _edit_geometry(self, *_: object) -> None:
        geometry = self.canvas_editor.selected_geometry()
        if geometry is not None:
            open_geometry_dialog(
                "Position and size", geometry, self.canvas_editor.set_selected_geometry
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

    def _choose_image(self, *_: object) -> None:
        if self._project_id is not None:
            open_image_dialog(self._import_image)

    def _import_image(self, source: str) -> None:
        if self._project_id is None or self._pending_image_import:
            return
        project_id = self._project_id
        self._pending_image_import = True

        def upload() -> tuple[str, str]:
            uploaded = self._images.upload_image(project_id, source)
            managed = self._images.materialize(project_id, uploaded.reference)
            return uploaded.reference, str(managed)

        def display(result: tuple[str, str]) -> None:
            try:
                self.canvas_editor.add_image(result[0], render_source=result[1])
            except Exception as error:
                show_error(f"Could not display imported image: {error}")
                self._finish_image_import(success=False)
            else:
                self._finish_image_import(success=True)

        def failed(error: Exception) -> None:
            show_error(f"Could not import image: {error}")
            self._finish_image_import(success=False)

        run_background(upload, display, failed)

    def _finish_image_import(self, *, success: bool) -> None:
        self._pending_image_import = False
        navigation, self._deferred_navigation = self._deferred_navigation, None
        waiters, self._import_waiters = self._import_waiters, []
        if navigation is not None and (success or not waiters):
            navigation()
        for after, on_failure in waiters:
            if success:
                self.save_before_rebuild(after, on_failure)
            else:
                on_failure()

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
        open_confirmation_dialog(
            "Clear workspace",
            "Remove all objects and strokes? You can undo until you leave the project.",
            self.canvas_editor.clear_drawing,
        )

    def _mark_dirty(self) -> None:
        self._save_session.mark_dirty()

    def _save(self, *_: object) -> bool:
        return self._save_session.save()

    def _save_now(self, *_: object) -> None:
        if self._save_session.dirty:
            self._save_session.save(after=lambda: show_confirmation("Workspace saved locally."))
        else:
            show_confirmation("Workspace is already up to date.")

    def _show_revisions(self, *_: object) -> None:
        generation = self._load_generation

        def fetch() -> None:
            artifact = self._save_session.artifact
            if artifact is None or generation != self._load_generation:
                return

            def display(revisions: object) -> None:
                if generation != self._load_generation:
                    return
                if not revisions:
                    show_confirmation("No earlier saved versions are available.")
                    return
                choices = tuple(
                    (revision.id, revision.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"))
                    for revision in revisions
                )
                open_choice_dialog("Restore workspace version", choices, self._restore_revision)

            run_background(lambda: self._artifacts.list_revisions(artifact), display)

        self._save_session.save(after=fetch)

    def _restore_revision(self, revision_id: str) -> None:
        artifact = self._save_session.artifact
        project_id = self._project_id
        if artifact is None or project_id is None:
            return
        generation = self._load_generation
        if self._save_session.dirty:

            def continue_restore() -> None:
                current = self._save_session.artifact
                if (
                    generation == self._load_generation
                    and current is not None
                    and current.id == artifact.id
                ):
                    self._restore_revision(revision_id)

            self._save_session.save(after=continue_restore)
            return
        self.disabled = True

        def restore() -> tuple[Artifact, object]:
            saved = self._artifacts.restore_revision(artifact, revision_id)
            document = self._documents.decode(self._artifacts.read_json(saved))
            for image in document.images:
                self._images.materialize(project_id, image.source)
            return saved, document

        def display(result: tuple[Artifact, object]) -> None:
            if generation != self._load_generation:
                return
            saved, document = result
            self._artifact = saved
            self._save_session.bind_artifact(saved)
            self.canvas_editor.load_document(
                document, lambda source: str(self._images.materialize(project_id, source))
            )
            self.disabled = False
            show_confirmation("Workspace version restored.")

        def failed(error: Exception) -> None:
            if generation != self._load_generation:
                return
            self.disabled = False
            show_error(f"Could not restore workspace: {error}")

        run_background(restore, display, failed)

    def _autosave(self, _elapsed: float) -> None:
        self._save()

    def dispose(self) -> None:
        self._save()
        self._autosave_event.cancel()

    def save_before_rebuild(
        self, after: Callable[[], None], on_failure: Callable[[], None]
    ) -> None:
        if self._pending_image_import:
            self._import_waiters.append((after, on_failure))
            return
        self._save_session.save(after=after, on_failure=on_failure)
