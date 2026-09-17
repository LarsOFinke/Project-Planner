from collections.abc import Callable

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.core.domain.todos.Todo import Todo
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.core.domain.todos.TodoStatus import TodoStatus
from project_planner.frontend.shared.dialogs import show_confirmation
from project_planner.frontend.shared.form_layout import build_scrollable_form
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    SLATE_400,
    field_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
)


class TodoEditorPopup(Popup):
    def __init__(
        self,
        todo: Todo | None,
        on_save: Callable[[str, str, TodoModule, TodoStatus], None],
        fixed_module: TodoModule,
        **kwargs: object,
    ) -> None:
        self._todo = todo
        self._on_save = on_save
        self._fixed_module = fixed_module
        content = self._build_content()
        super().__init__(
            title="Edit to-do" if todo is not None else "New to-do",
            title_color=PEARL_GREY,
            title_size="18sp",
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.9, dp(680)),
            height=min(Window.height * 0.92, dp(560)),
            **kwargs,
        )
        self.bind(on_open=self._populate_when_sized)

    def _build_content(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        form.add_widget(field_label("Title"))
        self.title_input = style_input(
            TextInput(
                hint_text="What needs to be done?",
                multiline=False,
                size_hint_y=None,
                height=dp(48),
            )
        )
        form.add_widget(self.title_input)
        form.add_widget(field_label("Description"))
        self.description_input = style_input(
            TextInput(
                hint_text="Context, acceptance criteria, or next action",
                size_hint_y=None,
                height=dp(110),
            )
        )
        form.add_widget(self.description_input)
        selectors = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
        module_box = BoxLayout(orientation="vertical")
        module_box.add_widget(field_label("Module"))
        self.module = style_spinner(
            Spinner(
                text=self._module_label(self._fixed_module),
                values=[self._module_label(self._fixed_module)],
                disabled=True,
            )
        )
        module_box.add_widget(self.module)
        status_box = BoxLayout(orientation="vertical")
        status_box.add_widget(field_label("Status"))
        self.status = style_spinner(
            Spinner(
                text=self._status_label(TodoStatus.OPEN),
                values=[self._status_label(status) for status in TodoStatus],
            )
        )
        status_box.add_widget(self.status)
        selectors.add_widget(module_box)
        selectors.add_widget(status_box)
        form.add_widget(selectors)
        metadata = Label(
            text=self._metadata_text(),
            color=SLATE_400,
            font_size="12sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(42),
        )
        metadata.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        form.add_widget(metadata)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        cancel = style_button(Button(text="Cancel"), "secondary")
        save = style_button(Button(text="Save to-do"), "primary")
        cancel.bind(on_release=lambda *_: self.dismiss())
        save.bind(on_release=self._save)
        self.title_input.bind(on_text_validate=self._save)
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        return content

    def _populate_when_sized(self, *_: object) -> None:
        if self._todo is None:
            self.title_input.focus = True
            return
        self.title_input.bind(width=self._populate_fields)
        self._populate_fields(self.title_input, self.title_input.width)

    def _populate_fields(self, _field: TextInput, width: float) -> None:
        if self._todo is None or width == 100:
            return
        self.title_input.unbind(width=self._populate_fields)
        self.title_input.text = self._todo.title
        self.description_input.text = self._todo.description
        self.module.text = self._module_label(self._fixed_module)
        self.status.text = self._status_label(self._todo.status)
        self.title_input.focus = True

    def _metadata_text(self) -> str:
        if self._todo is None:
            return "Created and updated timestamps are assigned when this to-do is saved."
        return (
            f"Created {self._todo.created_at:%Y-%m-%d %H:%M}   ·   "
            f"Updated {self._todo.updated_at:%Y-%m-%d %H:%M}"
        )

    def _save(self, *_: object) -> None:
        title = self.title_input.text.strip()
        if not title:
            self.title_input.hint_text = "A title is required"
            return
        self._on_save(
            title,
            self.description_input.text.strip(),
            self._module_from_label(self.module.text),
            self._status_from_label(self.status.text),
        )
        self.dismiss()
        show_confirmation("To-do saved locally.")

    @staticmethod
    def _module_label(module: TodoModule) -> str:
        return module.value.title()

    @staticmethod
    def _status_label(status: TodoStatus) -> str:
        return status.value.replace("_", " ").title()

    @staticmethod
    def _module_from_label(label: str) -> TodoModule:
        return TodoModule(label.lower())

    @staticmethod
    def _status_from_label(label: str) -> TodoStatus:
        return TodoStatus(label.lower().replace(" ", "_"))
