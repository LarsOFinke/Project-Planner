from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner_frontend.calendar.DateInput import DateInput
from project_planner_frontend.collaboration.clients.ProjectLinkClient import ProjectLinkClient
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.links.ProjectLinksPopup import ProjectLinksPopup
from project_planner_frontend.collaboration.views.todos.TodoManagerPopup import TodoManagerPopup
from project_planner_frontend.projects.clients.ProjectQueryClient import ProjectQueryClient
from project_planner_frontend.projects.clients.ProjectWorkflowClient import (
    ProjectWorkflowClient,
)
from project_planner_frontend.shared.date_parser import (
    format_optional_date,
    parse_optional_date,
)
from project_planner_frontend.shared.dialogs import show_confirmation
from project_planner_frontend.shared.theme import (
    NAVY_900,
    SLATE_400,
    caption_label,
    field_label,
    paint_background,
    section_label,
    style_button,
    style_input,
    style_spinner,
    title_label,
)


class OverviewPanel(BoxLayout):
    def __init__(
        self,
        workflows: ProjectWorkflowClient,
        queries: ProjectQueryClient,
        links: ProjectLinkClient,
        todos: TodoClient,
        on_navigate: Callable[[str], None],
        on_saved: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", **kwargs)
        self._workflows = workflows
        self._queries = queries
        self._links = links
        self._todos = todos
        self._on_navigate = on_navigate
        self._on_saved = on_saved
        self._project: Project | None = None
        self._parent_ids: dict[str, str | None] = {"No parent": None}
        paint_background(self, NAVY_900)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        form = BoxLayout(
            orientation="vertical",
            spacing=dp(9),
            padding=[dp(24), dp(20), dp(24), dp(24)],
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(title_label("Project overview"))
        form.add_widget(caption_label("Purpose, ownership, and planning context at a glance."))
        form.add_widget(section_label("Project brief"))
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
                height=dp(132),
            )
        )
        form.add_widget(self.description_input)
        form.add_widget(section_label("Schedule and structure"))
        date_labels = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(10))
        date_labels.add_widget(field_label("Start date"))
        date_labels.add_widget(field_label("Target date"))
        form.add_widget(date_labels)
        dates = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.start_date = DateInput()
        self.target_date = DateInput()
        dates.add_widget(self.start_date)
        dates.add_widget(self.target_date)
        form.add_widget(dates)
        selector_labels = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(10))
        selector_labels.add_widget(field_label("Status"))
        selector_labels.add_widget(field_label("Planning method"))
        selector_labels.add_widget(field_label("Parent project"))
        form.add_widget(selector_labels)
        selectors = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.status = style_spinner(Spinner(values=[item.value.title() for item in ProjectStatus]))
        self.method = style_spinner(Spinner(values=[item.value.title() for item in PlanningMethod]))
        self.parent_spinner = style_spinner(Spinner(text="No parent"))
        selectors.add_widget(self.status)
        selectors.add_widget(self.method)
        selectors.add_widget(self.parent_spinner)
        form.add_widget(selectors)
        form.add_widget(section_label("People"))
        people_labels = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(10))
        people_labels.add_widget(field_label("Project owner"))
        people_labels.add_widget(field_label("Assignee"))
        form.add_widget(people_labels)
        people = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        self.owner = style_input(TextInput(hint_text="Optional", multiline=False))
        self.assignee = style_input(TextInput(hint_text="Optional", multiline=False))
        people.add_widget(self.owner)
        people.add_widget(self.assignee)
        form.add_widget(people)
        form.add_widget(section_label("Notes and activity"))
        form.add_widget(field_label("Project notes"))
        self.notes = style_input(
            TextInput(
                hint_text="Simple shared notes",
                multiline=True,
                size_hint_y=None,
                height=dp(120),
            )
        )
        form.add_widget(self.notes)
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
        actions = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        save = style_button(
            Button(
                text="Save changes",
                size_hint_x=None,
                width=dp(180),
            ),
            "primary",
        )
        todos = style_button(Button(text="General To-Dos"), "secondary")
        relationships = style_button(Button(text="Linked projects"), "secondary")
        save.bind(on_release=self._save)
        todos.bind(on_release=self._open_todos)
        relationships.bind(on_release=self._open_project_links)
        actions.add_widget(save)
        actions.add_widget(todos)
        actions.add_widget(relationships)
        form.add_widget(actions)
        scroll.add_widget(form)
        self.add_widget(scroll)
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        overview = self._queries.get_overview(project_id)
        project = overview.project
        self._project = project
        self.disabled = False
        self.title_input.text = project.title
        self.description_input.text = project.description
        self.status.text = project.status.value.title()
        self.method.text = project.planning_method.value.title()
        self.start_date.text = format_optional_date(project.start_date)
        self.target_date.text = format_optional_date(project.target_date)
        self.owner.text = project.owner
        self.assignee.text = project.assignee
        self.notes.text = project.notes
        self._parent_ids = {choice.label: choice.project_id for choice in overview.parent_choices}
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
        try:
            project = self._workflows.update_project(
                self._project.id,
                title=self.title_input.text,
                description=self.description_input.text,
                status=ProjectStatus(self.status.text.lower()),
                planning_method=PlanningMethod(self.method.text.lower()),
                parent_id=self._parent_ids[self.parent_spinner.text],
                start_date=parse_optional_date(self.start_date.text, "Start date"),
                target_date=parse_optional_date(self.target_date.text, "Target date"),
                owner=self.owner.text,
                assignee=self.assignee.text,
                notes=self.notes.text,
            )
        except ValueError as error:
            show_confirmation(str(error), duration=2.5)
            return
        self.show_project(project.id)
        self._on_saved(project.id)
        show_confirmation("Project changes saved locally.")

    def _open_todos(self, *_: object) -> None:
        if self._project is not None:
            TodoManagerPopup(
                self._todos,
                self._project.id,
                TodoModule.GENERAL,
                "General project To-Dos",
            ).open()

    def _open_project_links(self, *_: object) -> None:
        if self._project is not None:
            ProjectLinksPopup(self._links, self._project.id, self._on_navigate).open()
