import webbrowser
from functools import partial
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.core.application.resources.ResourceLinkService import ResourceLinkService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.domain.resources.ResourceLink import ResourceLink
from project_planner.core.domain.resources.ResourceLinkKind import ResourceLinkKind
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.frontend.shared.dialogs import open_file_dialog
from project_planner.frontend.shared.theme import (
    NAVY_900,
    RED,
    SLATE_200,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
    title_label,
)
from project_planner.frontend.todos.TodoManagerPopup import TodoManagerPopup


class ResourceLinksPanel(BoxLayout):
    def __init__(
        self, resources: ResourceLinkService, todos: TodoService, **kwargs: object
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(9),
            padding=[dp(22), dp(18)],
            **kwargs,
        )
        self._resources = resources
        self._todos = todos
        self._project_id: str | None = None
        paint_background(self, NAVY_900)
        heading = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        heading.add_widget(title_label("Links and files"))
        todo_button = style_button(
            Button(text="Link To-Dos", size_hint_x=None, width=dp(140)), "secondary"
        )
        todo_button.bind(on_release=self._open_todos)
        heading.add_widget(todo_button)
        self.add_widget(heading)
        self.add_widget(
            caption_label("Keep web references and local file paths with the project.")
        )
        first_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.kind = style_spinner(
            Spinner(
                text="Web",
                values=[kind.value.title() for kind in ResourceLinkKind],
                size_hint_x=None,
                width=dp(120),
            )
        )
        self.title_input = style_input(
            TextInput(hint_text="Link title", multiline=False)
        )
        first_row.add_widget(self.kind)
        first_row.add_widget(self.title_input)
        second_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.target_input = style_input(
            TextInput(hint_text="https://example.com or /absolute/path", multiline=False)
        )
        add = style_button(
            Button(text="Add link", size_hint_x=None, width=dp(120)), "primary"
        )
        browse = style_button(
            Button(text="Browse", size_hint_x=None, width=dp(100)), "secondary"
        )
        browse.bind(on_release=self._browse)
        add.bind(on_release=self._add)
        self.target_input.bind(on_text_validate=self._add)
        second_row.add_widget(self.target_input)
        second_row.add_widget(browse)
        second_row.add_widget(add)
        self.feedback = Label(
            text="",
            color=RED,
            halign="left",
            size_hint_y=None,
            height=dp(26),
        )
        self.feedback.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(first_row)
        self.add_widget(second_row)
        self.add_widget(self.feedback)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        self.disabled = False
        self.feedback.text = ""
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        links = self._resources.list_for_project(self._project_id)
        if not links:
            self._rows.add_widget(
                Label(
                    text="No web or file links yet.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(70),
                )
            )
        for link in links:
            self._add_row(link)

    def _add_row(self, link: ResourceLink) -> None:
        row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(6))
        details = Label(
            text=f"{link.kind.value.upper()}  ·  {link.title}\n{link.target}",
            color=SLATE_200,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        details.bind(
            size=lambda widget, size: setattr(
                widget, "text_size", (size[0] - dp(8), size[1])
            )
        )
        open_link = style_button(
            Button(text="Open", size_hint_x=None, width=dp(82)), "secondary"
        )
        remove = style_button(
            Button(text="Remove", size_hint_x=None, width=dp(96)), "danger"
        )
        open_link.bind(on_release=partial(self._open, link))
        remove.bind(on_release=partial(self._remove, link.id))
        row.add_widget(details)
        row.add_widget(open_link)
        row.add_widget(remove)
        self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        if self._project_id is None:
            return
        try:
            self._resources.add(
                self._project_id,
                self.title_input.text,
                self.target_input.text,
                ResourceLinkKind(self.kind.text.lower()),
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.title_input.text = ""
        self.target_input.text = ""
        self.feedback.text = ""
        self.refresh()

    def _open(self, link: ResourceLink, *_: object) -> None:
        target = (
            link.target
            if link.kind is ResourceLinkKind.WEB
            else Path(link.target).as_uri()
        )
        webbrowser.open(target)

    def _browse(self, *_: object) -> None:
        self.kind.text = ResourceLinkKind.FILE.value.title()
        open_file_dialog(self._set_file_target)

    def _set_file_target(self, target: str) -> None:
        self.target_input.text = target
        if not self.title_input.text.strip():
            self.title_input.text = Path(target).name

    def _remove(self, link_id: str, *_: object) -> None:
        self._resources.remove(link_id)
        self.refresh()

    def _open_todos(self, *_: object) -> None:
        if self._project_id is not None:
            TodoManagerPopup(
                self._todos,
                self._project_id,
                TodoModule.LINKS,
                "Links and files To-Dos",
            ).open()
