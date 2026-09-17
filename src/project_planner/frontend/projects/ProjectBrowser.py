from collections.abc import Callable
from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from project_planner.core.application.custom.SectionService import SectionService
from project_planner.core.application.projects.ProjectQueryService import ProjectQueryService
from project_planner.core.application.projects.ProjectWorkflowService import (
    ProjectWorkflowService,
)
from project_planner.core.domain.custom.SectionType import SectionType
from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.frontend.projects.NewProjectPopup import NewProjectPopup
from project_planner.frontend.projects.ProjectTreeRow import ProjectTreeRow
from project_planner.frontend.shared.theme import (
    BORDER,
    NAVY_800,
    caption_label,
    empty_state_label,
    paint_background,
    section_label,
    style_button,
)


class ProjectBrowser(BoxLayout):
    def __init__(
        self,
        workflows: ProjectWorkflowService,
        queries: ProjectQueryService,
        sections: SectionService,
        on_select: Callable[[str], None],
        on_exit: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12), dp(14)],
            **kwargs,
        )
        self._workflows = workflows
        self._queries = queries
        self._sections = sections
        self._on_select = on_select
        self._on_exit = on_exit
        self.selected_id: str | None = None
        paint_background(self, NAVY_800, 10, BORDER)
        self._list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self._list.bind(minimum_height=self._list.setter("height"))
        self._build_header()
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(self._list)
        self.add_widget(scroll)
        self.exit_button = style_button(
            Button(text="Exit", size_hint_y=None, height=dp(46)), "danger"
        )
        self.exit_button.bind(on_release=lambda *_: self._on_exit())
        self.add_widget(self.exit_button)
        self.refresh()

    def _build_header(self) -> None:
        self.add_widget(section_label("Project directory"))
        self.add_widget(caption_label("Projects and child projects in one hierarchy."))
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

        def submit(
            title: str,
            description: str,
            start_date: date | None,
            target_date: date | None,
            method: PlanningMethod,
            owner: str,
            assignee: str,
            custom_type: SectionType | None,
        ) -> None:
            project = self._workflows.create_project(
                title,
                description=description,
                parent_id=parent_id,
                start_date=start_date,
                target_date=target_date,
                planning_method=method,
                owner=owner,
                assignee=assignee,
            )
            if custom_type is not None:
                self._sections.add(
                    project.id,
                    f"{custom_type.value.title()} Section",
                    custom_type,
                )
            self.refresh()
            self.select(project.id)

        NewProjectPopup(submit).open()

    def refresh(self) -> None:
        self._list.clear_widgets()
        items = self._queries.list_tree()

        if not items:
            self._list.add_widget(
                empty_state_label("No projects yet\nCreate a project to begin planning.", 92)
            )
            return

        for item in items:
            project = item.project
            selected = project.id == self.selected_id
            self._list.add_widget(
                ProjectTreeRow(
                    project.title,
                    project.status.value,
                    item.depth,
                    selected,
                    partial(self.select, project.id),
                )
            )

    def select(self, project_id: str) -> None:
        self.selected_id = project_id
        self.refresh()
        self._on_select(project_id)
