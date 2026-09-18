from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button

from project_planner_frontend.shared.theme import PEARL_GREY


class BinButton(Button):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(text="", size_hint_x=None, width=dp(42), **kwargs)
        with self.canvas.after:
            Color(*PEARL_GREY)
            self._body = Line(rectangle=(0, 0, 0, 0), width=1.4)
            self._lid = Line(points=[], width=1.4)
            self._handle = Line(points=[], width=1.4)
            self._left_slot = Line(points=[], width=1.0)
            self._right_slot = Line(points=[], width=1.0)
        self.bind(pos=self._sync_icon, size=self._sync_icon)
        self._sync_icon()

    def _sync_icon(self, *_: object) -> None:
        left = self.x + self.width * 0.32
        right = self.x + self.width * 0.68
        bottom = self.y + self.height * 0.22
        top = self.y + self.height * 0.63
        self._body.rectangle = (left, bottom, right - left, top - bottom)
        lid_y = self.y + self.height * 0.70
        self._lid.points = [
            self.x + self.width * 0.25,
            lid_y,
            self.x + self.width * 0.75,
            lid_y,
        ]
        self._handle.points = [
            self.x + self.width * 0.42,
            lid_y,
            self.x + self.width * 0.42,
            self.y + self.height * 0.79,
            self.x + self.width * 0.58,
            self.y + self.height * 0.79,
            self.x + self.width * 0.58,
            lid_y,
        ]
        slot_bottom = self.y + self.height * 0.30
        slot_top = self.y + self.height * 0.56
        self._left_slot.points = [self.x + self.width * 0.43, slot_bottom]
        self._left_slot.points += [self.x + self.width * 0.43, slot_top]
        self._right_slot.points = [self.x + self.width * 0.57, slot_bottom]
        self._right_slot.points += [self.x + self.width * 0.57, slot_top]
