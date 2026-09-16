from collections.abc import Callable
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner.core.bootstrap.application_container import ApplicationContainer
from project_planner.core.domain.projects.project import Project
from project_planner.frontend.shared.dialogs import open_text_dialog
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    RED,
    SLATE_400,
    caption_label,
    paint_background,
    style_button,
)


class ProjectBrowser(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
        on_select: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12), dp(14)],
            **kwargs,
        )
        self._container = container
        self._on_select = on_select
        self.selected_id: str | None = None
        paint_background(self, NAVY_800, 8)
        self._list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self._list.bind(minimum_height=self._list.setter("height"))
        self._build_header()
        scroll = ScrollView()
        scroll.add_widget(self._list)
        self.add_widget(scroll)
        self.refresh()

    def _build_header(self) -> None:
        self.add_widget(
            Label(
                text="PROJECTS",
                color=GOLD,
                bold=True,
                font_size="13sp",
                size_hint_y=None,
                height=dp(28),
                halign="left",
            )
        )
        self.children[0].bind(
            size=lambda widget, size: setattr(widget, "text_size", size)
        )
        self.add_widget(caption_label("Organize work from portfolio to task."))
        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(7))
        new_root = style_button(Button(text="+ Project"), "primary")
        new_child = style_button(Button(text="+ Child"), "secondary")
        new_root.bind(on_release=lambda *_: self._create(None))
        new_child.bind(on_release=lambda *_: self._create(self.selected_id))
        controls.add_widget(new_root)
        controls.add_widget(new_child)
        self.add_widget(controls)

    def _create(self, parent_id: str | None) -> None:
        if parent_id is None and self.selected_id is not None:
            parent_id = None

        def submit(title: str) -> None:
            project = self._container.projects.create(title, parent_id=parent_id)
            self._container.phases.initialize(project.id, project.planning_method)
            self.refresh()
            self.select(project.id)

        open_text_dialog("New project", "Project title", submit)

    def refresh(self) -> None:
        self._list.clear_widgets()
        projects = list(self._container.projects.list_all())
        by_parent: dict[str | None, list[Project]] = {}
        for project in projects:
            by_parent.setdefault(project.parent_id, []).append(project)

        if not projects:
            empty = Label(
                text="No projects yet\nCreate one to begin planning.",
                color=SLATE_400,
                font_size="13sp",
                halign="center",
                size_hint_y=None,
                height=dp(90),
            )
            empty.bind(size=lambda widget, size: setattr(widget, "text_size", size))
            self._list.add_widget(empty)
            return

        def append_children(parent_id: str | None, depth: int) -> None:
            for project in by_parent.get(parent_id, []):
                prefix = "    " * depth
                selected = project.id == self.selected_id
                marker = ">" if selected else " "
                button = Button(
                    text=(
                        f"{prefix}{marker}  {project.title}\n"
                        f"{prefix}    {project.status.value.title()}"
                    ),
                    size_hint_y=None,
                    height=dp(54),
                    halign="left",
                    valign="middle",
                )
                style_button(button, "selected" if selected else "quiet")
                button.color = (
                    RED
                    if project.status.value == "blocked" and not selected
                    else (GOLD if not selected else button.color)
                )
                button.font_size = "13sp"
                button.bind(
                    size=lambda widget, size: setattr(
                        widget, "text_size", (size[0] - dp(16), size[1])
                    )
                )
                button.bind(on_release=partial(self._select_event, project.id))
                self._list.add_widget(button)
                append_children(project.id, depth + 1)

        append_children(None, 0)

    def _select_event(self, project_id: str, *_: object) -> None:
        self.select(project_id)

    def select(self, project_id: str) -> None:
        self.selected_id = project_id
        self.refresh()
        self._on_select(project_id)
