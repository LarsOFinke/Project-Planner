from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy.uix.button import Button

from project_planner_frontend.shared.theme import PEARL_GREY


class DisclosureButton(Button):
    def __init__(self, expanded: bool, **kwargs: object) -> None:
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(34), dp(34)))
        kwargs.setdefault("pos_hint", {"center_y": 0.5})
        super().__init__(text="", **kwargs)
        self.expanded = expanded
        with self.canvas.after:
            Color(*PEARL_GREY)
            self._chevron = Line(points=[], width=dp(1.5), joint="round")
        self.bind(pos=self._sync_icon, size=self._sync_icon)
        self._sync_icon()

    def _sync_icon(self, *_: object) -> None:
        center_x, center_y = self.center
        radius = min(self.width, self.height) * 0.15
        if self.expanded:
            self._chevron.points = [
                center_x - radius,
                center_y + radius * 0.55,
                center_x,
                center_y - radius * 0.55,
                center_x + radius,
                center_y + radius * 0.55,
            ]
            return
        self._chevron.points = [
            center_x - radius * 0.55,
            center_y + radius,
            center_x + radius * 0.55,
            center_y,
            center_x - radius * 0.55,
            center_y - radius,
        ]
