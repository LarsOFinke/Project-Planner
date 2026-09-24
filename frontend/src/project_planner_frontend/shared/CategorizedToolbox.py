from collections.abc import Callable, Mapping, Sequence

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from project_planner_frontend.shared.theme import (
    BORDER,
    GOLD_LIGHT,
    NAVY_800,
    paint_background,
    style_button,
)

ToolboxAction = tuple[str, Callable[..., None], str]


class CategorizedToolbox(BoxLayout):
    """Always-visible, scrollable editor dock with task-oriented sections."""

    def __init__(
        self,
        groups: Mapping[str, Sequence[ToolboxAction]],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            size_hint_x=None,
            width=dp(148),
            padding=dp(7),
            **kwargs,
        )
        if not groups:
            raise ValueError("A toolbox requires at least one group")
        paint_background(self, NAVY_800, 8, BORDER)
        self._buttons: dict[tuple[str, str], Button] = {}
        self._sections: dict[str, BoxLayout] = {}
        self._headings: dict[str, Label] = {}
        stack = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        stack.bind(minimum_height=stack.setter("height"))
        for title, actions in groups.items():
            section = self._section(title, actions)
            self._sections[title] = section
            stack.add_widget(section)
        self._scroll = ScrollView(
            do_scroll_x=False, do_scroll_y=True, bar_width=dp(4), scroll_type=["bars", "content"]
        )
        self._scroll.add_widget(stack)
        self.add_widget(self._scroll)

    def button(self, group: str, label: str) -> Button:
        return self._buttons[group, label]

    def set_group_label(self, group: str, text: str) -> None:
        self._headings[group].text = text.upper()

    def _section(self, title: str, actions: Sequence[ToolboxAction]) -> BoxLayout:
        section = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        section.bind(minimum_height=section.setter("height"))
        heading = Label(
            text=title.upper(),
            color=GOLD_LIGHT,
            bold=True,
            font_size=sp(11),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
        )
        heading.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        self._headings[title] = heading
        section.add_widget(heading)
        grid = GridLayout(
            cols=2,
            size_hint_y=None,
            spacing=dp(4),
            row_force_default=True,
            row_default_height=dp(36),
        )
        grid.bind(minimum_height=grid.setter("height"))
        for label, callback, variant in actions:
            button = style_button(Button(text=label), variant)
            button.font_size = sp(11)
            button.halign = "center"
            button.valign = "middle"
            button.bind(size=lambda widget, size: setattr(widget, "text_size", size))
            button.bind(on_release=callback)
            grid.add_widget(button)
            self._buttons[title, label] = button
        section.add_widget(grid)
        return section
