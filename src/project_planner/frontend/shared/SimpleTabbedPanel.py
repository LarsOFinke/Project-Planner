from collections.abc import Mapping

from kivy.metrics import dp
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.widget import Widget

from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_900,
    NAVY_950,
    PEARL_GREY,
    SLATE_700,
)


class SimpleTabbedPanel(TabbedPanel):
    def __init__(self, tabs: Mapping[str, Widget], **kwargs: object) -> None:
        super().__init__(
            do_default_tab=False,
            tab_width=dp(150),
            tab_height=dp(42),
            strip_border=[0, 0, 0, 0],
            background_color=NAVY_900,
            background_image="",
            **kwargs,
        )
        self._headers: list[TabbedPanelItem] = []
        for title, content in tabs.items():
            self._add_tab(title, content)
        self.bind(current_tab=self._style_tabs)
        self.bind(disabled=self._sync_content_disabled)

    def _add_tab(self, title: str, content: Widget) -> None:
        tab = TabbedPanelItem(text=title)
        tab.background_normal = ""
        tab.background_down = ""
        tab.background_color = SLATE_700
        tab.color = PEARL_GREY
        tab.font_size = "14sp"
        tab.add_widget(content)
        self.add_widget(tab)
        self._headers.append(tab)

    def _style_tabs(self, _tabs: TabbedPanel, current: TabbedPanelItem) -> None:
        for header in self._headers:
            selected = header is current
            header.background_color = GOLD if selected else SLATE_700
            header.color = NAVY_950 if selected else PEARL_GREY

    def _sync_content_disabled(self, _tabs: TabbedPanel, disabled: bool) -> None:
        """Undo stale nested-content state after an owning panel becomes interactive."""
        self.content.disabled = disabled
