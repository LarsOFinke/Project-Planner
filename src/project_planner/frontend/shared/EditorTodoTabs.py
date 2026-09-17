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


class EditorTodoTabs(TabbedPanel):
    def __init__(
        self,
        editor_title: str,
        editor: Widget,
        todos: Widget,
        **kwargs: object,
    ) -> None:
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
        self._add_tab(editor_title, editor)
        self._add_tab("To-Dos", todos)
        self.bind(current_tab=self._style_tabs)

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
