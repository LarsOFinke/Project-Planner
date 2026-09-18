from collections.abc import Callable

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.popup import Popup

from project_planner_frontend.collaboration.clients.ProjectLinkClient import ProjectLinkClient
from project_planner_frontend.collaboration.views.links.ProjectLinksPanel import ProjectLinksPanel
from project_planner_frontend.shared.theme import GOLD, NAVY_800, PEARL_GREY


class ProjectLinksPopup(Popup):
    def __init__(
        self,
        links: ProjectLinkClient,
        project_id: str,
        on_navigate: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        panel = ProjectLinksPanel(links, self._navigate)
        panel.show_project(project_id)
        self._on_navigate = on_navigate
        super().__init__(
            title="Linked projects",
            title_color=PEARL_GREY,
            title_size="18sp",
            separator_color=GOLD,
            background_color=NAVY_800,
            content=panel,
            size_hint=(None, None),
            width=min(Window.width * 0.94, dp(980)),
            height=min(Window.height * 0.9, dp(700)),
            **kwargs,
        )

    def _navigate(self, project_id: str) -> None:
        self.dismiss()
        self._on_navigate(project_id)
