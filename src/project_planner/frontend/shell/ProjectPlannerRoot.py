from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from project_planner.core.bootstrap.ApplicationContainer import ApplicationContainer
from project_planner.frontend.diagram.DiagramPanel import DiagramPanel
from project_planner.frontend.links.ProjectLinksPanel import ProjectLinksPanel
from project_planner.frontend.phases.PhasePlanningPanel import PhasePlanningPanel
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
    style_spinner,
)
from project_planner.frontend.workspace.WorkspacePanel import WorkspacePanel


class ProjectPlannerRoot(BoxLayout):
    def __init__(
        self,
        container: ApplicationContainer,
        ui_scale: float,
        on_scale_change: Callable[[float], None],
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="vertical", spacing=0, **kwargs)
        self._on_scale_change = on_scale_change
        self._ui_scale = ui_scale
        paint_background(self, NAVY_950)
        self._build_header()
        body = BoxLayout(spacing=dp(12), padding=[dp(14), dp(12), dp(14), dp(14)])
        self.browser = ProjectBrowser(
            container.project_workflows,
            container.project_queries,
            self._show_project,
            size_hint_x=None,
            width=dp(300),
        )
        self.overview = OverviewPanel(
            container.project_workflows,
            container.project_queries,
            self._project_saved,
        )
        self.phases = PhasePlanningPanel(container.phases, container.project_workflows)
        self.links = ProjectLinksPanel(container.links)
        self.diagram = DiagramPanel(
            container.artifacts,
            container.diagram_documents,
            container.settings.autosave_seconds,
        )
        self.workspace = WorkspacePanel(
            container.artifacts,
            container.workspace_documents,
            container.images,
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
        self._add_tab(self.tabs, "Phases", self.phases)
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
        identity.children[0].bind(
            size=lambda widget, size: setattr(widget, "text_size", size)
        )
        identity.add_widget(
            Label(
                text="Local workspace  ·  Prototype 0.1",
                color=SLATE_200,
                font_size="12sp",
                halign="left",
            )
        )
        identity.children[0].bind(
            size=lambda widget, size: setattr(widget, "text_size", size)
        )
        scale = style_spinner(
            Spinner(
                text=f"Scale {round(self._ui_scale * 100)}%",
                values=[f"Scale {percent}%" for percent in range(5, 501, 5)],
                size_hint_x=None,
                width=dp(132),
            )
        )
        scale.bind(text=self._change_scale)
        header.add_widget(identity)
        header.add_widget(scale)
        self.add_widget(header)

    def _change_scale(self, _spinner: Spinner, value: str) -> None:
        percent = int(value.removeprefix("Scale ").removesuffix("%"))
        self._on_scale_change(percent / 100)

    def _add_tab(
        self, tabs: TabbedPanel, title: str, content: BoxLayout
    ) -> None:
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
        self.tabs.tab_width = max(
            dp(96), tab_space / len(self._tab_headers)
        )

    def _show_project(self, project_id: str) -> None:
        self.overview.show_project(project_id)
        self.phases.show_project(project_id)
        self.links.show_project(project_id)
        self.diagram.show_project(project_id)
        self.workspace.show_project(project_id)

    def _project_saved(self, project_id: str) -> None:
        self.browser.selected_id = project_id
        self.browser.refresh()
        self.phases.show_project(project_id)
        self.links.show_project(project_id)

    def dispose(self) -> None:
        self.diagram.dispose()
        self.workspace.dispose()
