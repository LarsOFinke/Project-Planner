from collections.abc import Callable

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from project_planner_frontend.shared.theme import BORDER, RED, SLATE_200, style_button


class ProjectTreeRow(BoxLayout):
    """A project row whose entire control is offset to express hierarchy."""

    def __init__(
        self,
        title: str,
        status: str,
        depth: int,
        selected: bool,
        on_select: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint_y=None, height=dp(58), spacing=dp(5), **kwargs)
        self._depth = max(0, depth)
        self._indent_width = dp(18 * min(self._depth, 8))
        branch = Widget(size_hint_x=None, width=self._indent_width)
        self.add_widget(branch)
        self.button = style_button(
            Button(
                text=f"{title}\n{status.replace('_', ' ').title()}",
                halign="left",
                valign="middle",
            ),
            "selected" if selected else "quiet",
        )
        if status == "blocked" and not selected:
            self.button.color = RED
        elif not selected:
            self.button.color = SLATE_200
        self.button.bind(
            size=lambda widget, size: setattr(
                widget,
                "text_size",
                (size[0] - dp(20), size[1]),
            )
        )
        self.button.bind(on_release=lambda *_: on_select())
        self.add_widget(self.button)
        with self.canvas.before:
            self._branch_color = Color(*BORDER)
            self._branch_line = Line(points=[], width=1.1)
        self.bind(pos=self._sync_branch, size=self._sync_branch)
        self._sync_branch()

    def _sync_branch(self, *_: object) -> None:
        if self._depth == 0:
            self._branch_line.points = []
            return
        anchor_x = self.x + self._indent_width - dp(9)
        self._branch_line.points = [
            anchor_x,
            self.y,
            anchor_x,
            self.top,
            anchor_x,
            self.center_y,
            self.x + self._indent_width + dp(2),
            self.center_y,
        ]
