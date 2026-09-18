from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup

from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner_frontend.collaboration.clients.TodoClient import TodoClient
from project_planner_frontend.collaboration.views.todos.TodoPanel import TodoPanel
from project_planner_frontend.shared.theme import GOLD, NAVY_800, PEARL_GREY


class TodoManagerPopup(Popup):
    def __init__(
        self,
        todos: TodoClient,
        project_id: str,
        module: TodoModule,
        title: str,
        phase_id: str | None = None,
        **kwargs: object,
    ) -> None:
        panel = TodoPanel(todos)
        panel.show_context(
            project_id,
            module,
            phase_id=phase_id,
            title=title,
        )
        super().__init__(
            title=title,
            title_color=PEARL_GREY,
            title_size="18sp",
            separator_color=GOLD,
            background_color=NAVY_800,
            content=panel,
            size_hint=(None, None),
            width=min(Window.width * 0.94, dp(920)),
            height=min(Window.height * 0.92, dp(720)),
            **kwargs,
        )
