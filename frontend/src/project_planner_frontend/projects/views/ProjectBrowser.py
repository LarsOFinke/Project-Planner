from collections.abc import Callable
from datetime import date
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner_frontend.planning.clients.SectionClient import SectionClient
from project_planner_frontend.projects.clients.ProjectCategoryClient import (
    ProjectCategoryClient,
)
from project_planner_frontend.projects.clients.ProjectQueryClient import ProjectQueryClient
from project_planner_frontend.projects.clients.ProjectServiceClient import ProjectServiceClient
from project_planner_frontend.projects.clients.ProjectWorkflowClient import (
    ProjectWorkflowClient,
)
from project_planner_frontend.projects.views.NewProjectPopup import NewProjectPopup
from project_planner_frontend.projects.views.ProjectCategoryRow import ProjectCategoryRow
from project_planner_frontend.projects.views.ProjectTreeRow import ProjectTreeRow
from project_planner_frontend.shared.dialogs import (
    open_confirmation_dialog,
    open_text_dialog,
    show_confirmation,
)
from project_planner_frontend.shared.theme import (
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
        projects: ProjectServiceClient,
        workflows: ProjectWorkflowClient,
        queries: ProjectQueryClient,
        categories: ProjectCategoryClient,
        sections: SectionClient,
        on_select: Callable[[str | None, bool], None],
        on_exit: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12), dp(14)],
            **kwargs,
        )
        self._projects = projects
        self._workflows = workflows
        self._queries = queries
        self._categories = categories
        self._sections = sections
        self._on_select = on_select
        self._on_exit = on_exit
        self.selected_id: str | None = None
        self.selected_category_id: str | None = None
        self._directory = ()
        self._project_by_id: dict[str, Project] = {}
        self._category_by_project_id: dict[str, str | None] = {}
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
        self.add_widget(caption_label("Categories contain projects and their child hierarchy."))
        category_controls = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(7))
        add_category = style_button(Button(text="+ Category"), "secondary")
        self._rename_category_button = style_button(Button(text="Rename"), "secondary")
        self._remove_category_button = style_button(Button(text="− Category"), "danger")
        add_category.bind(on_release=lambda *_: self._create_category())
        self._rename_category_button.bind(on_release=lambda *_: self._rename_category())
        self._remove_category_button.bind(on_release=lambda *_: self._remove_category())
        category_controls.add_widget(add_category)
        category_controls.add_widget(self._rename_category_button)
        category_controls.add_widget(self._remove_category_button)
        self.add_widget(category_controls)
        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(7))
        new_root = style_button(Button(text="+ Project"), "primary")
        self._new_child_button = style_button(Button(text="+ Child"), "secondary")
        new_root.bind(on_release=lambda *_: self._create(None))
        self._new_child_button.bind(on_release=lambda *_: self._create(self.selected_id))
        controls.add_widget(new_root)
        controls.add_widget(self._new_child_button)
        self.add_widget(controls)
        lifecycle = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(7))
        self._archive_project_button = style_button(Button(text="Archive"), "secondary")
        self._delete_project_button = style_button(Button(text="Delete project"), "danger")
        self._archive_project_button.bind(on_release=lambda *_: self._archive_project())
        self._delete_project_button.bind(on_release=lambda *_: self._delete_project())
        lifecycle.add_widget(self._archive_project_button)
        lifecycle.add_widget(self._delete_project_button)
        self.add_widget(lifecycle)

    def _create(self, parent_id: str | None) -> None:
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
            category_id = self.selected_category_id
            if parent_id is not None:
                category_id = self._queries.get_overview(parent_id).project.category_id
            project = self._workflows.create_project(
                title,
                description=description,
                parent_id=parent_id,
                category_id=category_id,
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

    def _create_category(self) -> None:
        def submit(name: str) -> None:
            category = self._categories.create(name)
            self.selected_id = None
            self.selected_category_id = category.id
            self.refresh()

        open_text_dialog("New project category", "Category name", submit)

    def _rename_category(self) -> None:
        if self.selected_category_id is None:
            return
        category = self._categories.require(self.selected_category_id)

        def submit(name: str) -> None:
            self._categories.rename(category.id, name)
            self.refresh()

        open_text_dialog(
            "Rename project category",
            "Category name",
            submit,
            initial=category.name,
        )

    def _remove_category(self) -> None:
        if self.selected_category_id is None:
            return
        category = self._categories.require(self.selected_category_id)

        def remove() -> None:
            self._categories.delete(category.id)
            self.selected_category_id = None
            self.refresh()

        open_confirmation_dialog(
            "Delete project category",
            f"Delete {category.name!r}? Its projects will move to Uncategorized.",
            remove,
        )

    def _archive_project(self) -> None:
        project = self._selected_project()
        if project is None or project.status is ProjectStatus.ARCHIVED:
            return

        def archive() -> None:
            self._projects.archive(project.id)
            self.refresh()
            self._on_select(project.id, True)
            show_confirmation(f"{project.title!r} archived.")

        open_confirmation_dialog(
            "Archive project",
            f"Archive {project.title!r}? Its planning data will remain available.",
            archive,
            confirm_text="Archive",
            confirm_variant="primary",
        )

    def _delete_project(self) -> None:
        project = self._selected_project()
        if project is None:
            return

        def delete() -> None:
            self._projects.delete(project.id)
            self._on_select(None, True)
            self.selected_id = None
            self.refresh()
            replacement_id = next(iter(self._project_by_id), None)
            if replacement_id is not None:
                self.select(replacement_id)
            show_confirmation(f"{project.title!r} deleted.")

        open_confirmation_dialog(
            "Delete project",
            (
                f"Permanently delete {project.title!r} and its planning data? "
                "Child projects will remain as root projects."
            ),
            delete,
        )

    def _selected_project(self) -> Project | None:
        if self.selected_id is None:
            return None
        return self._project_by_id.get(self.selected_id)

    def refresh(self, *, reload: bool = True) -> None:
        self._list.clear_widgets()
        if reload:
            self._directory = self._queries.list_directory()
            self._project_by_id = {
                item.project.id: item.project
                for section in self._directory
                for item in section.projects
            }
            self._category_by_project_id = {
                item.project.id: section.category.id if section.category is not None else None
                for section in self._directory
                for item in section.projects
            }
        self._sync_controls()

        if not self._directory:
            self._list.add_widget(
                empty_state_label("No projects yet\nCreate a project to begin planning.", 92)
            )
            return

        for section in self._directory:
            category = section.category
            category_id = category.id if category is not None else None
            self._list.add_widget(
                ProjectCategoryRow(
                    category.name if category is not None else "Uncategorized",
                    len(section.projects),
                    category_id is not None and category_id == self.selected_category_id,
                    partial(self._select_category, category_id),
                )
            )
            for item in section.projects:
                project = item.project
                selected = project.id == self.selected_id
                self._list.add_widget(
                    ProjectTreeRow(
                        project.title,
                        project.status.value,
                        item.depth + 1,
                        selected,
                        partial(self.select, project.id),
                    )
                )

    def _select_category(self, category_id: str | None) -> None:
        self.selected_id = None
        self.selected_category_id = category_id
        self.refresh(reload=False)

    def select(self, project_id: str) -> None:
        self.selected_id = project_id
        self.selected_category_id = self._category_by_project_id.get(project_id)
        self.refresh(reload=False)
        self._on_select(project_id, False)

    def _sync_controls(self) -> None:
        project = self._selected_project()
        self._new_child_button.disabled = project is None
        self._archive_project_button.disabled = (
            project is None or project.status is ProjectStatus.ARCHIVED
        )
        self._archive_project_button.text = (
            "Archived"
            if project is not None and project.status is ProjectStatus.ARCHIVED
            else "Archive"
        )
        self._delete_project_button.disabled = project is None
        self._rename_category_button.disabled = self.selected_category_id is None
        self._remove_category_button.disabled = self.selected_category_id is None
