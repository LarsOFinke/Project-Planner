from collections.abc import Callable, Sequence
from math import cos, pi, sin

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from project_planner_frontend.shared.theme import PEARL_GREY, style_button

MenuAction = tuple[str, Callable[[], None], str, bool]


class GearMenuButton(Button):
    def __init__(self, actions: Sequence[MenuAction], **kwargs: object) -> None:
        if not actions:
            raise ValueError("A gear menu requires at least one action")
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(34), dp(34)))
        kwargs.setdefault("pos_hint", {"center_y": 0.5})
        super().__init__(text="", **kwargs)
        self.menu = DropDown(auto_width=False, width=dp(180), max_height=dp(240))
        self.action_buttons: dict[str, Button] = {}
        for label, callback, variant, disabled in actions:
            action = style_button(
                Button(text=label, size_hint_y=None, height=dp(44), disabled=disabled),
                variant,
            )
            action.bind(on_release=self._action_handler(callback))
            self.action_buttons[label] = action
            self.menu.add_widget(action)
        self.bind(on_release=lambda *_: self.menu.open(self))
        with self.canvas.after:
            Color(*PEARL_GREY)
            self._gear = Line(points=[], close=True, width=dp(1.35), joint="round")
            self._inner = Line(circle=(0, 0, 0), width=dp(1.35))
        self.bind(pos=self._sync_icon, size=self._sync_icon)
        self._sync_icon()

    def _action_handler(self, callback: Callable[[], None]) -> Callable[..., None]:
        def run(*_: object) -> None:
            self.menu.dismiss()
            callback()

        return run

    def _sync_icon(self, *_: object) -> None:
        center_x, center_y = self.center
        size = min(self.width, self.height)
        inner = size * 0.10
        root = size * 0.22
        tooth = size * 0.30
        points: list[float] = []
        for index in range(24):
            angle = -pi / 2 + index * pi / 12
            radius = tooth if index % 3 == 0 else root
            points.extend((center_x + cos(angle) * radius, center_y + sin(angle) * radius))
        self._gear.points = points
        self._inner.circle = (center_x, center_y, inner)
