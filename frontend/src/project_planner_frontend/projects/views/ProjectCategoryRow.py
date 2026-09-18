from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from project_planner_frontend.shared.theme import GOLD_LIGHT, SLATE_400, style_button


class ProjectCategoryRow(BoxLayout):
    def __init__(
        self,
        name: str,
        project_count: int,
        selected: bool,
        on_select: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint_y=None, height=dp(42), **kwargs)
        label = f"{name.upper()}  ·  {project_count}"
        self.button = style_button(
            Button(text=label, halign="left", valign="middle"),
            "selected" if selected else "secondary",
        )
        self.button.color = GOLD_LIGHT if not selected else self.button.color
        if name == "Uncategorized" and not selected:
            self.button.color = SLATE_400
        self.button.bind(
            size=lambda widget, size: setattr(widget, "text_size", (size[0] - dp(18), size[1]))
        )
        self.button.bind(on_release=lambda *_: on_select())
        self.add_widget(self.button)
