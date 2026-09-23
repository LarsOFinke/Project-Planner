import webbrowser
from functools import partial
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from project_planner.modules.resources.entities.ResourceLink import ResourceLink
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner_frontend.collaboration.clients.ResourceLinkClient import ResourceLinkClient
from project_planner_frontend.shared.background import run_background
from project_planner_frontend.shared.dialogs import open_file_dialog
from project_planner_frontend.shared.theme import (
    NAVY_900,
    RED,
    SLATE_200,
    caption_label,
    empty_state_label,
    paint_background,
    section_label,
    style_button,
    style_input,
    title_label,
)


class ResourceLinkKindPanel(BoxLayout):
    def __init__(
        self,
        resources: ResourceLinkClient,
        kind: ResourceLinkKind,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(9),
            padding=[dp(18), dp(14)],
            **kwargs,
        )
        self._resources = resources
        self._kind = kind
        self._project_id: str | None = None
        self._refresh_generation = 0
        paint_background(self, NAVY_900)
        self.add_widget(title_label(self._heading))
        self.add_widget(caption_label(self._caption))
        self.title_input = style_input(TextInput(hint_text=self._title_hint, multiline=False))
        self.target_input = style_input(TextInput(hint_text=self._target_hint, multiline=False))
        self.target_input.bind(on_text_validate=self._add)
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
        self.add_widget(section_label("Add resource"))
        self.add_widget(self._title_controls())
        self.add_widget(self._target_controls())
        self.add_widget(self.feedback)
        self.add_widget(section_label("Saved resources"))
        self.add_widget(scroll)
        self.disabled = True

    @property
    def _heading(self) -> str:
        return "Web URLs" if self._kind is ResourceLinkKind.WEB else "Local files"

    @property
    def _caption(self) -> str:
        if self._kind is ResourceLinkKind.WEB:
            return "Keep websites, documentation, and online references with this project."
        return "Keep references to files available on this computer."

    @property
    def _title_hint(self) -> str:
        return "URL title" if self._kind is ResourceLinkKind.WEB else "File title"

    @property
    def _target_hint(self) -> str:
        return "https://example.com" if self._kind is ResourceLinkKind.WEB else "/absolute/path"

    def _title_controls(self) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(48))
        row.add_widget(self.title_input)
        return row

    def _target_controls(self) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        row.add_widget(self.target_input)
        if self._kind is ResourceLinkKind.FILE:
            browse = style_button(
                Button(text="Browse", size_hint_x=None, width=dp(100)), "secondary"
            )
            browse.bind(on_release=self._browse)
            row.add_widget(browse)
        add = style_button(Button(text=self._add_label, size_hint_x=None, width=dp(120)), "primary")
        add.bind(on_release=self._add)
        row.add_widget(add)
        return row

    @property
    def _add_label(self) -> str:
        return "Add URL" if self._kind is ResourceLinkKind.WEB else "Add file"

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        self.feedback.text = ""
        self.disabled = False
        self.refresh()

    def show_project_async(self, project_id: str) -> None:
        self._project_id = project_id
        self.feedback.text = ""
        self.disabled = False
        self.refresh_async()

    def clear_project(self) -> None:
        self._refresh_generation += 1
        self._project_id = None
        self.title_input.text = ""
        self.target_input.text = ""
        self.feedback.text = ""
        self._rows.clear_widgets()
        self.disabled = True

    def refresh(self) -> None:
        self._refresh_generation += 1
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        links = self._resources.list_for_project(self._project_id, self._kind)
        self._display_links(links)

    def refresh_async(self) -> None:
        self._refresh_generation += 1
        generation = self._refresh_generation
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        project_id = self._project_id

        def display(links: list[ResourceLink]) -> None:
            if generation == self._refresh_generation:
                self._display_links(links)

        run_background(lambda: self._resources.list_for_project(project_id, self._kind), display)

    def _display_links(self, links: list[ResourceLink]) -> None:
        if not links:
            self._rows.add_widget(empty_state_label(self._empty_message))
            return
        for link in links:
            self._add_row(link)

    @property
    def _empty_message(self) -> str:
        return "No web URLs yet." if self._kind is ResourceLinkKind.WEB else "No local files yet."

    def _add_row(self, link: ResourceLink) -> None:
        row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(6))
        details = Label(
            text=f"{link.title}\n{link.target}",
            color=SLATE_200,
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        details.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(8), size[1]))
        )
        open_link = style_button(
            Button(text=self._open_label, size_hint_x=None, width=dp(96)), "secondary"
        )
        remove = style_button(Button(text="Remove", size_hint_x=None, width=dp(96)), "danger")
        open_link.bind(on_release=partial(self._open, link))
        remove.bind(on_release=partial(self._remove, link.id))
        row.add_widget(details)
        row.add_widget(open_link)
        row.add_widget(remove)
        self._rows.add_widget(row)

    @property
    def _open_label(self) -> str:
        return "Open URL" if self._kind is ResourceLinkKind.WEB else "Open file"

    def _add(self, *_: object) -> None:
        if self._project_id is None:
            return
        try:
            self._resources.add(
                self._project_id,
                self.title_input.text,
                self.target_input.text,
                self._kind,
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.title_input.text = ""
        self.target_input.text = ""
        self.feedback.text = ""
        self.refresh()

    def _open(self, link: ResourceLink, *_: object) -> None:
        target = link.target if self._kind is ResourceLinkKind.WEB else Path(link.target).as_uri()
        webbrowser.open(target)

    def _browse(self, *_: object) -> None:
        open_file_dialog(self._set_file_target)

    def _set_file_target(self, target: str) -> None:
        self.target_input.text = target
        if not self.title_input.text.strip():
            self.title_input.text = Path(target).name

    def _remove(self, link_id: str, *_: object) -> None:
        self._resources.remove(link_id)
        self.refresh()
