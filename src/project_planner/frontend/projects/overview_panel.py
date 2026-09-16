from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from project_planner.core.bootstrap.application_container import ApplicationContainer
from project_planner.core.domain.projects.planning_method import PlanningMethod
from project_planner.core.domain.projects.project import Project
from project_planner.core.domain.projects.project_status import ProjectStatus
from project_planner.frontend.shared.theme import (
    NAVY_900,
    SLATE_400,
    caption_label,
    field_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
    title_label,
)


class OverviewPanel(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
        on_saved: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._container = container
        self._on_saved = on_saved
        self._project: Project | None = None
        self._parent_ids: dict[str, str | None] = {"No parent": None}
        paint_background(self, NAVY_900)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        form = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(24), dp(20), dp(24), dp(24)],
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(title_label("Project overview"))
        form.add_widget(caption_label("Purpose, ownership, and planning context at a glance."))
        form.add_widget(field_label("Title"))
        self.title_input = style_input(
            TextInput(
                hint_text="Give this project a clear name",
                multiline=False,
                size_hint_y=None,
                height=dp(48),
            )
        )
        form.add_widget(self.title_input)
        form.add_widget(field_label("Description"))
        self.description_input = style_input(
            TextInput(
                hint_text="What outcome should this project create?",
                size_hint_y=None,
                height=dp(150),
            )
        )
        form.add_widget(self.description_input)
        selector_labels = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(10))
        selector_labels.add_widget(field_label("Status"))
        selector_labels.add_widget(field_label("Planning method"))
        selector_labels.add_widget(field_label("Parent project"))
        form.add_widget(selector_labels)
        selectors = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.status = style_spinner(
            Spinner(values=[item.value.title() for item in ProjectStatus])
        )
        self.method = style_spinner(
            Spinner(values=[item.value.title() for item in PlanningMethod])
        )
        self.parent_spinner = style_spinner(Spinner(text="No parent"))
        selectors.add_widget(self.status)
        selectors.add_widget(self.method)
        selectors.add_widget(self.parent_spinner)
        form.add_widget(selectors)
        self.metadata = Label(
            size_hint_y=None,
            height=dp(40),
            halign="left",
            color=SLATE_400,
            font_size="12sp",
        )
        self.metadata.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        form.add_widget(self.metadata)
        form.add_widget(Widget(size_hint_y=None, height=dp(8)))
        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        actions.add_widget(Widget())
        save = style_button(
            Button(
                text="Save changes",
                size_hint_x=None,
                width=dp(180),
            ),
            "primary",
        )
        save.bind(on_release=self._save)
        actions.add_widget(save)
        form.add_widget(actions)
        scroll.add_widget(form)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        project = self._container.projects.require(project_id)
        self._project = project
        self.disabled = False
        self.title_input.text = project.title
        self.description_input.text = project.description
        self.status.text = project.status.value.title()
        self.method.text = project.planning_method.value.title()
        self._parent_ids = {"No parent": None}
        for candidate in self._container.projects.list_all():
            if candidate.id != project.id:
                self._parent_ids[candidate.title] = candidate.id
        self.parent_spinner.values = list(self._parent_ids)
        parent_title = next(
            (name for name, value in self._parent_ids.items() if value == project.parent_id),
            "No parent",
        )
        self.parent_spinner.text = parent_title
        self.metadata.text = (
            f"Created {project.created_at:%Y-%m-%d %H:%M}   ·   "
            f"Updated {project.updated_at:%Y-%m-%d %H:%M}"
        )

    def _save(self, *_: object) -> None:
        if self._project is None:
            return
        old_method = self._project.planning_method
        project = self._container.projects.update(
            self._project.id,
            title=self.title_input.text,
            description=self.description_input.text,
            status=ProjectStatus(self.status.text.lower()),
            planning_method=PlanningMethod(self.method.text.lower()),
            parent_id=self._parent_ids[self.parent_spinner.text],
        )
        if old_method != project.planning_method:
            existing = self._container.phases.list_for_project(project.id)
            if not existing:
                self._container.phases.initialize(project.id, project.planning_method)
        self.show_project(project.id)
        self._on_saved(project.id)
