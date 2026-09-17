from collections.abc import Callable

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Rectangle, Rotate
from kivy.metrics import dp
from kivy.uix.widget import Widget

from project_planner.frontend.shared.theme import GOLD, SLATE_600


class DraggableImage(Widget):
    def __init__(
        self,
        element_id: str,
        on_select: Callable[[str], None],
        on_change: Callable[[], None],
        source: str,
        rotation_degrees: float = 0,
        **kwargs: object,
    ) -> None:
        texture = CoreImage(source).texture
        initial_width = dp(180)
        initial_height = (
            initial_width * texture.height / texture.width if texture.width else dp(120)
        )
        super().__init__(
            size_hint=(None, None),
            size=(initial_width, initial_height),
            **kwargs,
        )
        self.element_id = element_id
        self.source = source
        self.rotation_degrees = rotation_degrees
        self._on_select = on_select
        self._on_change = on_change
        self._drag_offset = (0.0, 0.0)
        with self.canvas:
            PushMatrix()
            self._rotation = Rotate(angle=rotation_degrees, origin=self.center)
            self._image = Rectangle(texture=texture, pos=self.pos, size=self.size)
            self._border_color = Color(*SLATE_600)
            self._border = Line(rectangle=(*self.pos, *self.size), width=1)
            PopMatrix()
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def set_selected(self, selected: bool) -> None:
        self._border_color.rgba = GOLD if selected else SLATE_600
        self._border.width = 3 if selected else 1

    def rotate_by(self, degrees: float) -> None:
        self.rotation_degrees = (self.rotation_degrees + degrees) % 360
        self._rotation.angle = self.rotation_degrees
        self._on_change()

    def scale_by(self, factor: float) -> None:
        new_width = min(dp(600), max(dp(60), self.width * factor))
        new_height = min(dp(450), max(dp(40), self.height * factor))
        center = self.center
        self.size = (new_width, new_height)
        self.center = center
        self._on_change()

    def _update_graphics(self, *_: object) -> None:
        self._rotation.origin = self.center
        self._image.pos = self.pos
        self._image.size = self.size
        self._border.rectangle = (*self.pos, *self.size)

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
