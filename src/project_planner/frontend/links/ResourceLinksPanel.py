from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from project_planner.core.application.resources.ResourceLinkService import ResourceLinkService
from project_planner.core.application.todos.TodoService import TodoService
from project_planner.core.domain.resources.ResourceLinkKind import ResourceLinkKind
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.frontend.links.ResourceLinkKindPanel import ResourceLinkKindPanel
from project_planner.frontend.shared.SimpleTabbedPanel import SimpleTabbedPanel
from project_planner.frontend.shared.theme import (
    NAVY_900,
    caption_label,
    paint_background,
    title_label,
)
from project_planner.frontend.todos.TodoPanel import TodoPanel


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
        paint_background(self, NAVY_900)
        self.web_panel = ResourceLinkKindPanel(resources, ResourceLinkKind.WEB)
        self.file_panel = ResourceLinkKindPanel(resources, ResourceLinkKind.FILE)
        self.todo_panel = TodoPanel(todos)
        self.add_widget(title_label("Project resources"))
        self.add_widget(
            caption_label("Keep online references and local files organized separately.")
        )
        self.add_widget(
            SimpleTabbedPanel(
                {
                    "Web URLs": self.web_panel,
                    "Local Files": self.file_panel,
                    "To-Dos": self.todo_panel,
                }
            )
        )
        self.disabled = True

    def show_project(self, project_id: str) -> None:
        self.web_panel.show_project(project_id)
        self.file_panel.show_project(project_id)
        self.todo_panel.show_context(
            project_id,
            TodoModule.LINKS,
            title="Resource To-Dos",
        )
        self.disabled = False

    def refresh(self) -> None:
        self.web_panel.refresh()
        self.file_panel.refresh()
        self.todo_panel.refresh()
