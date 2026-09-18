from collections.abc import Callable, Sequence

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
        super().__init__(text="", size_hint_x=None, width=dp(42), **kwargs)
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
            self._outer = Line(circle=(0, 0, 0), width=1.3)
            self._inner = Line(circle=(0, 0, 0), width=1.3)
            self._horizontal = Line(points=[], width=1.3)
            self._vertical = Line(points=[], width=1.3)
            self._rising = Line(points=[], width=1.3)
            self._falling = Line(points=[], width=1.3)
        self.bind(pos=self._sync_icon, size=self._sync_icon)
        self._sync_icon()

    def _action_handler(self, callback: Callable[[], None]) -> Callable[..., None]:
        def run(*_: object) -> None:
            self.menu.dismiss()
            callback()

        return run

    def _sync_icon(self, *_: object) -> None:
        center_x, center_y = self.center
        inner = min(self.width, self.height) * 0.10
        outer = min(self.width, self.height) * 0.24
        tooth = min(self.width, self.height) * 0.32
        diagonal = tooth * 0.71
        self._outer.circle = (center_x, center_y, outer)
        self._inner.circle = (center_x, center_y, inner)
        self._horizontal.points = [center_x - tooth, center_y, center_x + tooth, center_y]
        self._vertical.points = [center_x, center_y - tooth, center_x, center_y + tooth]
        self._rising.points = [
            center_x - diagonal,
            center_y - diagonal,
            center_x + diagonal,
            center_y + diagonal,
        ]
        self._falling.points = [
            center_x - diagonal,
            center_y + diagonal,
            center_x + diagonal,
            center_y - diagonal,
        ]
