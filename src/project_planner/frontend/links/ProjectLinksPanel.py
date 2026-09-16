from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.core.application.links.ProjectLinkService import ProjectLinkService
from project_planner.core.domain.links.ProjectLink import ProjectLink
from project_planner.frontend.shared.theme import (
    NAVY_900,
    SLATE_200,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
    title_label,
)


class ProjectLinksPanel(BoxLayout):
    def __init__(
        self, links: ProjectLinkService, **kwargs: object
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(22), dp(18)],
            **kwargs,
        )
        self._links = links
        self._project_id: str | None = None
        self._target_ids: dict[str, str] = {}
        paint_background(self, NAVY_900)
        self.add_widget(title_label("Linked projects"))
        self.add_widget(
            caption_label("Make dependencies and cross-project relationships visible.")
        )
        controls = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.target = style_spinner(Spinner(text="Choose project"))
        self.relation = style_input(
            TextInput(text="related", multiline=False, hint_text="Relation")
        )
        add = style_button(
            Button(text="Add link", size_hint_x=None, width=dp(120)), "primary"
        )
        add.bind(on_release=self._add)
        controls.add_widget(self.target)
        controls.add_widget(self.relation)
        controls.add_widget(add)
        self._rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self._rows.bind(minimum_height=self._rows.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._rows)
        self.add_widget(controls)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self._project_id = project_id
        self.disabled = False
        self._target_ids = {
            choice.label: choice.project_id
            for choice in self._links.available_targets(project_id)
            if choice.project_id is not None
        }
        self.target.values = list(self._target_ids)
        self.target.text = next(iter(self._target_ids), "No other projects")
        self.refresh()

    def refresh(self) -> None:
        self._rows.clear_widgets()
        if self._project_id is None:
            return
        links = self._links.list_resolved(self._project_id)
        if not links:
            self._rows.add_widget(
                Label(
                    text="No linked projects yet.",
                    color=SLATE_400,
                    size_hint_y=None,
                    height=dp(70),
                )
            )
        for resolved in links:
            link = resolved.link
            direction = "OUT" if resolved.outgoing else "IN"
            other_title = (
                resolved.other_project.title
                if resolved.other_project is not None
                else "Missing project"
            )
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
            relationship = Label(
                text=f"{direction}  ·  {link.relation}  ·  {other_title}",
                color=SLATE_200,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            relationship.bind(
                size=lambda widget, size: setattr(
                    widget, "text_size", (size[0] - dp(8), size[1])
                )
            )
            row.add_widget(relationship)
            remove = style_button(
                Button(text="Remove", size_hint_x=None, width=dp(96)), "danger"
            )
            remove.bind(on_release=partial(self._remove, link))
            row.add_widget(remove)
            self._rows.add_widget(row)

    def _add(self, *_: object) -> None:
        if self._project_id is None or self.target.text not in self._target_ids:
            return
        self._links.add(
            self._project_id,
            self._target_ids[self.target.text],
            self.relation.text or "related",
        )
        self.refresh()

    def _remove(self, link: ProjectLink, *_: object) -> None:
        self._links.remove(link)
        self.refresh()
