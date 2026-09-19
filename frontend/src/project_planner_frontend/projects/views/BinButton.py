from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button

from project_planner_frontend.shared.theme import PEARL_GREY


class BinButton(Button):
    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(34), dp(34)))
        kwargs.setdefault("pos_hint", {"center_y": 0.5})
        super().__init__(text="", **kwargs)
        with self.canvas.after:
            Color(*PEARL_GREY)
            self._body = Line(rectangle=(0, 0, 0, 0), width=dp(1.35))
            self._lid = Line(points=[], width=dp(1.35))
            self._handle = Line(points=[], width=dp(1.35))
            self._left_slot = Line(points=[], width=dp(1.0))
            self._right_slot = Line(points=[], width=dp(1.0))
        self.bind(pos=self._sync_icon, size=self._sync_icon)
        self._sync_icon()

    def _sync_icon(self, *_: object) -> None:
        size = min(self.width, self.height)
        left = self.center_x - size * 0.18
        right = self.center_x + size * 0.18
        bottom = self.center_y - size * 0.24
        top = self.center_y + size * 0.17
        self._body.rectangle = (left, bottom, right - left, top - bottom)
        lid_y = self.center_y + size * 0.24
        self._lid.points = [
            self.center_x - size * 0.25,
            lid_y,
            self.center_x + size * 0.25,
            lid_y,
        ]
        self._handle.points = [
            self.center_x - size * 0.08,
            lid_y,
            self.center_x - size * 0.08,
            self.center_y + size * 0.32,
            self.center_x + size * 0.08,
            self.center_y + size * 0.32,
            self.center_x + size * 0.08,
            lid_y,
        ]
        slot_bottom = self.center_y - size * 0.16
        slot_top = self.center_y + size * 0.09
        self._left_slot.points = [self.center_x - size * 0.07, slot_bottom]
        self._left_slot.points += [self.center_x - size * 0.07, slot_top]
        self._right_slot.points = [self.center_x + size * 0.07, slot_bottom]
        self._right_slot.points += [self.center_x + size * 0.07, slot_top]
