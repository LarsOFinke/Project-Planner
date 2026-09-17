from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.domain.todos.Todo import Todo
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.core.domain.todos.TodoStatus import TodoStatus
from project_planner.frontend.shared.theme import (
    NAVY_900,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    title_label,
)
from project_planner.frontend.todos.TodoEditorPopup import TodoEditorPopup


class TodoPanel(BoxLayout):
    def __init__(self, todos: TodoService, **kwargs: object) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(22), dp(18)],
            **kwargs,
        )
        self._todos = todos
        self._project_id: str | None = None
        self._module = TodoModule.GENERAL
        self._phase_id: str | None = None
        paint_background(self, NAVY_900)
        self._heading = title_label("To-Dos")
        self.add_widget(self._heading)
        self.add_widget(
            caption_label("Actions stay attached to this planning context.")
        )
        controls = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        controls.add_widget(Label(text="", size_hint_x=1))
        add = style_button(Button(text="+ Add to-do", size_hint_x=None, width=dp(140)), "primary")
        add.bind(on_release=self._add)
        controls.add_widget(add)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(controls)
        self.add_widget(scroll)
        self.disabled = True

    def show_context(
        self,
        project_id: str,
        module: TodoModule,
        *,
        phase_id: str | None = None,
        title: str = "To-Dos",
    ) -> None:
        self._project_id = project_id
        self._module = module
        self._phase_id = phase_id
        self._heading.text = title
        self.disabled = False
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        todos = self._todos.list_for_context(
            self._project_id, self._module, self._phase_id
        )
        if not todos:
            self._rows.add_widget(
                Label(
                    text="No to-dos in this view.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(70),
                )
            )
            return
        for todo in todos:
            self._add_row(todo)

    def _add_row(self, todo: Todo) -> None:
        row = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(6))
        description = todo.description or "No description"
        edit = style_button(
            Button(
                text=(
                    f"{todo.title}\n"
                    f"{self._status_label(todo.status)}  ·  "
                    f"{todo.module.value.title()}  ·  {description}"
                ),
                halign="left",
                valign="middle",
            ),
            "quiet",
        )
        edit.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
        )
        edit.bind(on_release=partial(self._edit, todo))
        toggle_text = "Reopen" if todo.status is TodoStatus.DONE else "Done"
        toggle = style_button(Button(text=toggle_text, size_hint_x=None, width=dp(82)), "secondary")
        toggle.bind(on_release=partial(self._toggle, todo))
        remove = style_button(Button(text="Remove", size_hint_x=None, width=dp(92)), "danger")
        remove.bind(on_release=partial(self._remove, todo.id))
        row.add_widget(edit)
        row.add_widget(toggle)
        row.add_widget(remove)
        self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        if self._project_id is not None:
            TodoEditorPopup(None, self._create, self._module).open()

    def _create(
        self,
        title: str,
        description: str,
        module: TodoModule,
        status: TodoStatus,
    ) -> None:
        if self._project_id is not None:
            self._todos.add(
                self._project_id,
                title,
                description,
                self._module,
                status,
                self._phase_id,
            )
            self.refresh()

    def _edit(self, todo: Todo, *_: object) -> None:
        def save(
            title: str,
            description: str,
            module: TodoModule,
            status: TodoStatus,
        ) -> None:
            self._todos.update(
                todo.id,
                title=title,
                description=description,
                module=module,
                status=status,
            )
            self.refresh()

        TodoEditorPopup(todo, save, self._module).open()

    def _toggle(self, todo: Todo, *_: object) -> None:
        status = TodoStatus.OPEN if todo.status is TodoStatus.DONE else TodoStatus.DONE
        self._todos.update(
            todo.id,
            title=todo.title,
            description=todo.description,
            module=todo.module,
            status=status,
        )
        self.refresh()

    def _remove(self, todo_id: str, *_: object) -> None:
        self._todos.remove(todo_id)
        self.refresh()

    @staticmethod
    def _status_label(status: TodoStatus) -> str:
        return status.value.replace("_", " ").title()
