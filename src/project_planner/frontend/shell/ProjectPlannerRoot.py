from collections.abc import Callable

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.frontend.diagram.DiagramPanel import DiagramPanel
from project_planner.frontend.links.ResourceLinksPanel import ResourceLinksPanel
from project_planner.frontend.planning.PlanningPanel import PlanningPanel
from project_planner.frontend.projects.OverviewPanel import OverviewPanel
from project_planner.frontend.projects.ProjectBrowser import ProjectBrowser
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    NAVY_900,
    NAVY_950,
    PEARL_GREY,
    SLATE_200,
    SLATE_700,
    paint_background,
    style_button,
    style_spinner,
)
from project_planner.frontend.workspace.WorkspacePanel import WorkspacePanel


class ProjectPlannerRoot(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
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
        body = BoxLayout(spacing=dp(12), padding=[dp(14), dp(12), dp(14), dp(14)])
        self.browser = ProjectBrowser(
            container.project_workflows,
            container.project_queries,
            container.sections,
            self._show_project,
            self._exit_application,
            size_hint_x=None,
            width=dp(300),
        )
        self.overview = OverviewPanel(
            container.project_workflows,
            container.project_queries,
            container.links,
            container.todos,
            self._navigate_to_project,
            self._project_saved,
        )
        self.planning = PlanningPanel(
            container.projects,
            container.agile,
            container.phases,
            container.project_workflows,
            container.sections,
            container.waterfall_tasks,
            container.todos,
        )
        self.links = ResourceLinksPanel(container.resources, container.todos)
        self.diagram = DiagramPanel(
            container.artifacts,
            container.diagram_documents,
            container.todos,
            container.settings.autosave_seconds,
        )
        self.workspace = WorkspacePanel(
            container.artifacts,
            container.workspace_documents,
            container.images,
            container.todos,
            container.settings.autosave_seconds,
        )
        self.tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(128),
            tab_height=dp(46),
            strip_border=[0, 0, 0, 0],
            background_color=NAVY_900,
            background_image="",
        )
        self._tab_headers: list[TabbedPanelItem] = []
        self._add_tab(self.tabs, "Overview", self.overview)
        self._add_tab(self.tabs, "Plan", self.planning)
        self._add_tab(self.tabs, "Diagram", self.diagram)
        self._add_tab(self.tabs, "Workspace", self.workspace)
        self._add_tab(self.tabs, "Links", self.links)
        self.tabs.bind(current_tab=self._style_tabs)
        body.add_widget(self.browser)
        body.add_widget(self.tabs)
        self.add_widget(body)
        self.bind(width=self._update_scale)

    def _build_header(self) -> None:
        header = BoxLayout(
            size_hint_y=None,
            height=dp(68),
            padding=[dp(20), dp(10)],
            spacing=dp(10),
        )
        paint_background(header, NAVY_800)
        identity = BoxLayout(orientation="vertical")
        identity.add_widget(
            Label(
                text="PROJECT PLANNER",
                color=PEARL_GREY,
                bold=True,
                font_size="20sp",
                halign="left",
            )
        )
        identity.children[0].bind(size=lambda widget, size: setattr(widget, "text_size", size))
        identity.add_widget(
            Label(
                text="Local workspace  ·  Prototype 0.1",
                color=SLATE_200,
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
        tab = TabbedPanelItem(text=title)
        tab.background_normal = ""
        tab.background_down = ""
        tab.background_color = SLATE_700
        tab.color = PEARL_GREY
        tab.font_size = "14sp"
        tab.add_widget(content)
        tabs.add_widget(tab)
        self._tab_headers.append(tab)

    def _style_tabs(self, tabs: TabbedPanel, current: TabbedPanelItem) -> None:
        for header in self._tab_headers:
            selected = header is current
            header.background_color = GOLD if selected else SLATE_700
            header.color = NAVY_950 if selected else PEARL_GREY

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
