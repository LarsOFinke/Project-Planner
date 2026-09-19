from collections.abc import Callable
from datetime import date
from functools import partial
from typing import Any

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
    show_error,
)
from project_planner_frontend.shared.theme import (
    BORDER,
    NAVY_800,
    caption_label,
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
        self._collapsed_category_ids: set[str | None] = set()
        self._collapsed_project_ids: set[str] = set()
        self._directory = ()
        self._project_by_id: dict[str, Project] = {}
        self._category_by_project_id: dict[str, str | None] = {}
        self._parent_by_project_id: dict[str, str | None] = {}
        self._drop_target_widget: ProjectCategoryRow | ProjectTreeRow | None = None
        paint_background(self, NAVY_800, 10, BORDER)
        self._list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        self._list.bind(minimum_height=self._list.setter("height"))
        self._build_header()
        self._scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(7),
            scroll_type=["bars"],
        )
        self._scroll.add_widget(self._list)
        self.add_widget(self._scroll)
        self.exit_button = style_button(
            Button(text="Exit", size_hint_y=None, height=dp(46)), "danger"
        )
        self.exit_button.bind(on_release=lambda *_: self._on_exit())
        self.add_widget(self.exit_button)
        self.refresh()

    def _build_header(self) -> None:
        self.add_widget(section_label("Project directory"))
        self.add_widget(
            caption_label("Expand the hierarchy, or drag a project row onto a category or project.")
        )
        category_controls = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(7))
        add_category = style_button(Button(text="+ Category"), "secondary")
        add_category.bind(on_release=lambda *_: self._create_category())
        category_controls.add_widget(add_category)
        self.add_widget(category_controls)

    def _create(self, parent_id: str | None, category_id: str | None) -> None:
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
            selected_category_id = category_id
            if parent_id is not None:
                selected_category_id = self._queries.get_overview(parent_id).project.category_id
            project = self._workflows.create_project(
                title,
                description=description,
                parent_id=parent_id,
                category_id=selected_category_id,
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

    def _rename_category(self, category_id: str) -> None:
        category = self._categories.require(category_id)

        def submit(name: str) -> None:
            self._categories.rename(category.id, name)
            self.refresh()

        open_text_dialog(
            "Rename project category",
            "Category name",
            submit,
            initial=category.name,
        )

    def _remove_category(self, category_id: str) -> None:
        category = self._categories.require(category_id)

        def remove() -> None:
            self._categories.delete(category.id)
            self._collapsed_category_ids.discard(category.id)
            if self.selected_category_id == category.id:
                self.selected_category_id = None
            self.refresh()
            if self.selected_id is not None:
                self.selected_category_id = self._category_by_project_id.get(self.selected_id)
                self.refresh(reload=False)
                self._on_select(self.selected_id, True)

        open_confirmation_dialog(
            "Delete project category",
            f"Delete {category.name!r}? Its projects will move to Uncategorized.",
            remove,
        )

    def _archive_project(self, project_id: str) -> None:
        project = self._project_by_id.get(project_id)
        if project is None or project.status is ProjectStatus.ARCHIVED:
            return

        def archive() -> None:
            self._projects.archive(project.id)
            self.refresh()
            if self.selected_id == project.id:
                self._on_select(project.id, True)
            show_confirmation(f"{project.title!r} archived.")

        open_confirmation_dialog(
            "Archive project",
            f"Archive {project.title!r}? Its planning data will remain available.",
            archive,
            confirm_text="Archive",
            confirm_variant="primary",
        )

    def _delete_project(self, project_id: str) -> None:
        project = self._project_by_id.get(project_id)
        if project is None:
            return

        def delete() -> None:
            self._projects.delete(project.id)
            deleted_selected_project = self.selected_id == project.id
            if deleted_selected_project:
                self._on_select(None, True)
                self.selected_id = None
            self.refresh()
            if deleted_selected_project:
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

    def refresh(self, *, reload: bool = True) -> None:
        if self._drop_target_widget is not None:
            self._drop_target_widget.set_drop_target(False)
            self._drop_target_widget = None
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
            self._parent_by_project_id = {
                item.project.id: item.project.parent_id
                for section in self._directory
                for item in section.projects
            }
            project_ids = set(self._project_by_id)
            category_ids = {
                section.category.id for section in self._directory if section.category is not None
            }
            self._collapsed_project_ids.intersection_update(project_ids)
            self._collapsed_category_ids.intersection_update({None, *category_ids})
        for section in self._directory:
            category = section.category
            category_id = category.id if category is not None else None
            category_expanded = category_id not in self._collapsed_category_ids
            self._list.add_widget(
                ProjectCategoryRow(
                    category_id,
                    category.name if category is not None else "Uncategorized",
                    len(section.projects),
                    category_id is not None and category_id == self.selected_category_id,
                    category_expanded,
                    partial(self._select_category, category_id),
                    partial(self._toggle_category, category_id),
                    partial(self._create, None, category_id),
                    partial(self._rename_category, category_id)
                    if category_id is not None
                    else None,
                    partial(self._remove_category, category_id)
                    if category_id is not None
                    else None,
                )
            )
            if not category_expanded:
                continue
            for item, has_children in self._visible_project_items(section.projects):
                project = item.project
                selected = project.id == self.selected_id
                self._list.add_widget(
                    ProjectTreeRow(
                        project.id,
                        project.title,
                        project.status.value,
                        item.depth + 1,
                        selected,
                        has_children,
                        project.id not in self._collapsed_project_ids,
                        partial(self.select, project.id),
                        partial(self._drag_project, project.id),
                        partial(self._drop_project, project.id),
                        partial(self._toggle_project, project.id),
                        partial(self._create, project.id, category_id),
                        partial(self._archive_project, project.id),
                        partial(self._delete_project, project.id),
                    )
                )

    def _drag_project(
        self,
        project_id: str,
        position: tuple[float, float] | None,
    ) -> None:
        target = None if position is None else self._drop_target_at(project_id, position)
        if position is not None:
            self._auto_scroll(position)
        if target is self._drop_target_widget:
            return
        if self._drop_target_widget is not None:
            self._drop_target_widget.set_drop_target(False)
        self._drop_target_widget = target
        if target is not None:
            target.set_drop_target(True)

    def _drop_target_at(
        self,
        project_id: str,
        position: tuple[float, float],
    ) -> ProjectCategoryRow | ProjectTreeRow | None:
        if not self._scroll.collide_point(*position):
            return None
        list_position = self._list.to_widget(*position)
        for widget in self._list.children:
            if not widget.collide_point(*list_position):
                continue
            if isinstance(widget, ProjectCategoryRow):
                return widget
            if (
                isinstance(widget, ProjectTreeRow)
                and widget.project_id != project_id
                and not self._would_create_cycle(project_id, widget.project_id)
            ):
                return widget
        return None

    def _would_create_cycle(self, project_id: str, target_id: str) -> bool:
        current_id: str | None = target_id
        visited: set[str] = set()
        while current_id is not None and current_id not in visited:
            if current_id == project_id:
                return True
            visited.add(current_id)
            current_id = self._parent_by_project_id.get(current_id)
        return False

    def _auto_scroll(self, position: tuple[float, float]) -> None:
        if self._list.height <= self._scroll.height:
            return
        margin = min(dp(48), self._scroll.height * 0.2)
        if position[1] <= self._scroll.y + margin:
            self._scroll.scroll_y = max(0, self._scroll.scroll_y - 0.035)
        elif position[1] >= self._scroll.top - margin:
            self._scroll.scroll_y = min(1, self._scroll.scroll_y + 0.035)

    def _drop_project(self, project_id: str, position: tuple[float, float]) -> None:
        target = self._drop_target_at(project_id, position)
        self._drag_project(project_id, None)
        if isinstance(target, ProjectCategoryRow):
            self._move_project(project_id, None, target.category_id)
        elif isinstance(target, ProjectTreeRow):
            category_id = self._category_by_project_id.get(target.project_id)
            self._move_project(project_id, target.project_id, category_id)

    def _move_project(
        self,
        project_id: str,
        parent_id: str | None,
        category_id: str | None,
    ) -> None:
        try:
            project = self._projects.move(
                project_id,
                parent_id=parent_id,
                category_id=category_id,
            )
        except ValueError as error:
            show_error(f"Project could not be moved:\n{error}")
            return
        self._collapsed_category_ids.discard(project.category_id)
        if parent_id is not None:
            self._collapsed_project_ids.discard(parent_id)
        self.refresh()
        if self.selected_id is not None:
            self._on_select(self.selected_id, True)
        target = "the selected category" if parent_id is None else "its new parent"
        show_confirmation(f"{project.title!r} moved to {target}.")

    def _visible_project_items(
        self,
        items: tuple[Any, ...],
    ) -> tuple[tuple[Any, bool], ...]:
        visible: list[tuple[Any, bool]] = []
        hidden_below_depth: int | None = None
        for index, item in enumerate(items):
            if hidden_below_depth is not None:
                if item.depth > hidden_below_depth:
                    continue
                hidden_below_depth = None
            has_children = index + 1 < len(items) and items[index + 1].depth > item.depth
            visible.append((item, has_children))
            if has_children and item.project.id in self._collapsed_project_ids:
                hidden_below_depth = item.depth
        return tuple(visible)

    def _toggle_category(self, category_id: str | None) -> None:
        if category_id in self._collapsed_category_ids:
            self._collapsed_category_ids.remove(category_id)
        else:
            self._collapsed_category_ids.add(category_id)
        self.refresh(reload=False)

    def _toggle_project(self, project_id: str) -> None:
        if project_id in self._collapsed_project_ids:
            self._collapsed_project_ids.remove(project_id)
        else:
            self._collapsed_project_ids.add(project_id)
        self.refresh(reload=False)

    def _select_category(self, category_id: str | None) -> None:
        self.selected_id = None
        self.selected_category_id = category_id
        self.refresh(reload=False)
        self._on_select(None, True)

    def select(self, project_id: str) -> None:
        self.selected_id = project_id
        self.selected_category_id = self._category_by_project_id.get(project_id)
        self._collapsed_category_ids.discard(self.selected_category_id)
        ancestor_id = self._parent_by_project_id.get(project_id)
        visited: set[str] = set()
        while ancestor_id is not None and ancestor_id not in visited:
            visited.add(ancestor_id)
            self._collapsed_project_ids.discard(ancestor_id)
            ancestor_id = self._parent_by_project_id.get(ancestor_id)
        self.refresh(reload=False)
        self._on_select(project_id, False)
