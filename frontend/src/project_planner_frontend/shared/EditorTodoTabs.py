from kivy.metrics import dp
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.widget import Widget

from project_planner_frontend.shared.theme import NAVY_900, style_button


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
            tab_width=dp(164),
            tab_height=dp(44),
            strip_border=[0, 0, 0, 0],
            background_color=NAVY_900,
            background_image="",
            **kwargs,
        )
        self._headers: list[TabbedPanelItem] = []
        self._add_tab(editor_title, editor)
        self._add_tab("To-Dos", todos)
        self.bind(current_tab=self._style_tabs)
        self.bind(disabled=self._sync_content_disabled)

    def _add_tab(self, title: str, content: Widget) -> None:
        tab = style_button(TabbedPanelItem(text=title), "quiet")
        tab.font_size = "14sp"
        tab.add_widget(content)
        self.add_widget(tab)
        self._headers.append(tab)

    def _style_tabs(self, _tabs: TabbedPanel, current: TabbedPanelItem) -> None:
        for header in self._headers:
            selected = header is current
            style_button(header, "selected" if selected else "quiet")

    def _sync_content_disabled(self, _tabs: TabbedPanel, disabled: bool) -> None:
        """Keep Kivy's internal content state aligned with the effective tab state."""
        self.content.disabled = disabled
