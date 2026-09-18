from collections.abc import Callable

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from project_planner_frontend.api.ProjectPlannerApi import ProjectPlannerApi
from project_planner_frontend.artifacts.views.diagram.DiagramPanel import DiagramPanel
from project_planner_frontend.artifacts.views.workspace.WorkspacePanel import WorkspacePanel
from project_planner_frontend.collaboration.views.links.ResourceLinksPanel import ResourceLinksPanel
from project_planner_frontend.planning.views.PlanningPanel import PlanningPanel
from project_planner_frontend.projects.views.OverviewPanel import OverviewPanel
from project_planner_frontend.projects.views.ProjectBrowser import ProjectBrowser
from project_planner_frontend.shared.theme import (
    BORDER,
    GOLD_LIGHT,
    NAVY_800,
    NAVY_900,
    NAVY_950,
    PEARL_GREY,
    paint_background,
    style_button,
    style_spinner,
)
from project_planner_frontend.system.views.AdminPanel import AdminPanel


class ProjectPlannerRoot(BoxLayout):
    def __init__(
        self,
        clients: ProjectPlannerApi,
        autosave_seconds: int,
        ui_scale: float,
        fullscreen: bool,
        on_scale_change: Callable[[float], None],
        on_fullscreen_change: Callable[[bool], None],
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", spacing=0, **kwargs)
        self._on_scale_change = on_scale_change
        self._ui_scale = ui_scale
        self._fullscreen = fullscreen
        self._on_fullscreen_change = on_fullscreen_change
        paint_background(self, NAVY_950)
        self._build_header()
        body = BoxLayout(spacing=dp(14), padding=[dp(16), dp(14), dp(16), dp(16)])
        self.browser = ProjectBrowser(
            clients.project_workflows,
            clients.project_queries,
            clients.project_categories,
            clients.sections,
            self._show_project,
            self._exit_application,
            size_hint_x=None,
            width=dp(300),
        )
        self.overview = OverviewPanel(
            clients.project_workflows,
            clients.project_queries,
            clients.links,
            clients.todos,
            self._navigate_to_project,
            self._project_saved,
        )
        self.planning = PlanningPanel(
            clients.projects,
            clients.agile,
            clients.phases,
            clients.project_workflows,
            clients.sections,
            clients.waterfall_tasks,
            clients.todos,
        )
        self.links = ResourceLinksPanel(clients.resources, clients.todos)
        self.diagram = DiagramPanel(
            clients.artifacts,
            clients.diagram_documents,
            clients.todos,
            autosave_seconds,
        )
        self.workspace = WorkspacePanel(
            clients.artifacts,
            clients.workspace_documents,
            clients.images,
            clients.todos,
            autosave_seconds,
        )
        self.admin = AdminPanel(clients.health, clients.issues)
        self.tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(128),
            tab_height=dp(48),
            strip_border=[0, 0, 0, 0],
            background_color=NAVY_900,
            background_image="",
        )
        self._tab_headers: list[TabbedPanelItem] = []
        self._add_tab(self.tabs, "Overview", self.overview)
        self._add_tab(self.tabs, "Plan Roadmap", self.planning)
        self._add_tab(self.tabs, "Diagram", self.diagram)
        self._add_tab(self.tabs, "Workspace", self.workspace)
        self._add_tab(self.tabs, "Links", self.links)
        self._add_tab(self.tabs, "Admin", self.admin)
        self.tabs.bind(current_tab=self._style_tabs)
        body.add_widget(self.browser)
        body.add_widget(self.tabs)
        self.add_widget(body)
        self.bind(width=self._update_scale)

    def _build_header(self) -> None:
        header = BoxLayout(
            size_hint_y=None,
            height=dp(72),
            padding=[dp(22), dp(10)],
            spacing=dp(12),
        )
        paint_background(header, NAVY_800, 0, BORDER)
        identity = BoxLayout(orientation="vertical")
        identity.add_widget(
            Label(
                text="PROJECT PLANNER",
                color=PEARL_GREY,
                bold=True,
                font_size="21sp",
                halign="left",
            )
        )
        identity.children[0].bind(size=lambda widget, size: setattr(widget, "text_size", size))
        identity.add_widget(
            Label(
                text="LOCAL-FIRST PLANNING WORKSPACE  ·  0.1",
                color=GOLD_LIGHT,
                font_size="12sp",
                halign="left",
            )
        )
        identity.children[0].bind(size=lambda widget, size: setattr(widget, "text_size", size))
        scale = style_spinner(
            Spinner(
                text=f"Scale {round(self._ui_scale * 100)}%",
                values=[f"Scale {percent}%" for percent in range(5, 501, 5)],
                size_hint_x=None,
                width=dp(132),
            )
        )
        scale.bind(text=self._change_scale)
        self.fullscreen_button = style_button(
            Button(
                text=self._fullscreen_action_label(),
                size_hint_x=None,
                width=dp(132),
            ),
            "secondary",
        )
        self.fullscreen_button.bind(on_release=self._toggle_fullscreen)
        header.add_widget(identity)
        header.add_widget(self.fullscreen_button)
        header.add_widget(scale)
        self.add_widget(header)

    def _change_scale(self, _spinner: Spinner, value: str) -> None:
        percent = int(value.removeprefix("Scale ").removesuffix("%"))
        self._on_scale_change(percent / 100)

    def _toggle_fullscreen(self, *_: object) -> None:
        self._fullscreen = not self._fullscreen
        self.fullscreen_button.text = self._fullscreen_action_label()
        self._on_fullscreen_change(self._fullscreen)

    def _fullscreen_action_label(self) -> str:
        return "Windowed" if self._fullscreen else "Fullscreen"

    def _add_tab(self, tabs: TabbedPanel, title: str, content: BoxLayout) -> None:
        tab = style_button(TabbedPanelItem(text=title), "quiet")
        tab.font_size = "14sp"
        tab.add_widget(content)
        tabs.add_widget(tab)
        self._tab_headers.append(tab)

    def _style_tabs(self, tabs: TabbedPanel, current: TabbedPanelItem) -> None:
        for header in self._tab_headers:
            selected = header is current
            style_button(header, "selected" if selected else "quiet")

    def _update_scale(self, _widget: BoxLayout, width: float) -> None:
        self.browser.width = min(width * 0.34, max(dp(170), width * 0.24))
        tab_space = max(0, width - self.browser.width - dp(42))
        self.tabs.tab_width = max(dp(96), tab_space / len(self._tab_headers))

    def _show_project(self, project_id: str) -> None:
        self.overview.show_project(project_id)
        self.planning.show_project(project_id)
        self.links.show_project(project_id)
        self.diagram.show_project(project_id)
        self.workspace.show_project(project_id)

    def _project_saved(self, project_id: str) -> None:
        self.browser.selected_id = project_id
        self.browser.refresh()
        self.planning.show_project(project_id)
        self.links.show_project(project_id)

    def _navigate_to_project(self, project_id: str) -> None:
        self.browser.select(project_id)
        for header in self._tab_headers:
            if header.text == "Overview":
                self.tabs.switch_to(header)
                return

    def dispose(self) -> None:
        self.diagram.dispose()
        self.workspace.dispose()

    @staticmethod
    def _exit_application() -> None:
        running = App.get_running_app()
        if running is not None:
            running.stop()
