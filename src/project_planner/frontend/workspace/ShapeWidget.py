from collections.abc import Callable

from kivy.graphics import Color, Ellipse, Line, PopMatrix, PushMatrix, Rectangle, Rotate
from kivy.metrics import dp
from kivy.uix.widget import Widget

from project_planner.frontend.shared.theme import GOLD, hex_color


class ShapeWidget(Widget):
    def __init__(
        self,
        element_id: str,
        kind: str,
        on_select: Callable[[str], None],
        on_change: Callable[[], None],
        rotation_degrees: float = 0,
        color_hex: str = "#D5DAE2",
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint=(None, None), size=(dp(130), dp(86)), **kwargs)
        self.element_id = element_id
        self.kind = kind
        self.rotation_degrees = rotation_degrees
        self.color_hex = color_hex
        self._base_color = hex_color(color_hex)
        self._on_select = on_select
        self._on_change = on_change
        self._drag_offset = (0.0, 0.0)
        with self.canvas:
            PushMatrix()
            self._rotation = Rotate(angle=rotation_degrees, origin=self.center)
            self._fill_color = Color(*self._shape_fill())
            self._fill = (
                Ellipse(pos=self.pos, size=self.size)
                if kind == "ellipse"
                else Rectangle(pos=self.pos, size=self.size)
            )
            self._line_color = Color(*self._base_color)
            self._outline = Line(width=2)
            self._selection_color = Color(*GOLD[:3], 0)
            self._selection_outline = Line(width=2)
            PopMatrix()
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        self._update_graphics()

    def set_selected(self, selected: bool) -> None:
        self._selection_color.rgba = (*GOLD[:3], 1 if selected else 0)

    def set_color(self, color_hex: str) -> None:
        self.color_hex = color_hex
        self._base_color = hex_color(color_hex)
        self._fill_color.rgba = self._shape_fill()
        self._line_color.rgba = self._base_color
        self._on_change()

    def _shape_fill(self) -> tuple[float, float, float, float]:
        return self._base_color

    def rotate_by(self, degrees: float) -> None:
        self.rotation_degrees = (self.rotation_degrees + degrees) % 360
        self._rotation.angle = self.rotation_degrees
        self._on_change()

    def scale_by(self, factor: float) -> None:
        new_width = min(dp(420), max(dp(40), self.width * factor))
        new_height = min(dp(320), max(dp(32), self.height * factor))
        center = self.center
        self.size = (new_width, new_height)
        self.center = center
        self._on_change()

    def _update_graphics(self, *_: object) -> None:
        x, y = self.pos
        width, height = self.size
        self._rotation.origin = self.center
        selection_padding = dp(4)
        self._selection_outline.rectangle = (
            x - selection_padding,
            y - selection_padding,
            width + selection_padding * 2,
            height + selection_padding * 2,
        )
        if self.kind == "ellipse":
            self._fill.pos = self.pos
            self._fill.size = self.size
            self._outline.ellipse = (x, y, width, height)
            self._outline.points = []
        elif self.kind in {"line", "arrow"}:
            self._fill.size = (0, 0)
            middle = y + height / 2
            self._outline.ellipse = (0, 0, 0, 0)
            self._outline.points = [x, middle, x + width, middle]
            if self.kind == "arrow":
                self._outline.points += [
                    x + width - dp(18),
                    middle + dp(14),
                    x + width,
                    middle,
                    x + width - dp(18),
                    middle - dp(14),
                ]
        else:
            self._fill.pos = self.pos
            self._fill.size = self.size
            self._outline.ellipse = (0, 0, 0, 0)
            self._outline.rectangle = (x, y, width, height)
            self._outline.points = []

    def on_touch_down(self, touch: object) -> bool:
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._drag_offset = (touch.x - self.x, touch.y - self.y)
            self._on_select(self.element_id)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch.grab_current is self:
            self.pos = (
                touch.x - self._drag_offset[0],
                touch.y - self._drag_offset[1],
            )
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self._on_change()
            return True
        return super().on_touch_up(touch)
