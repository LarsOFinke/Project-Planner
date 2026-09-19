from collections.abc import Callable, Iterable
from math import hypot

from kivy.core.window import Window
from kivy.graphics import Color, Line, PopMatrix, PushMatrix, Translate
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from project_planner_frontend.shared.theme import GOLD_LIGHT


class ReorderableRow(BoxLayout):
    """A reusable list row that activates on click and reorders through drag and drop."""

    def __init__(
        self,
        item_id: str,
        on_activate: Callable[[], None],
        on_drag: Callable[[str, tuple[float, float] | None], None],
        on_drop: Callable[[str, tuple[float, float]], None],
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.item_id = item_id
        self._on_activate = on_activate
        self._on_drag = on_drag
        self._on_drop = on_drop
        self._action_controls: list[Widget] = []
        self._primary_control: Widget | None = None
        self._drag_touch: object | None = None
        self._drag_origin: tuple[float, float] | None = None
        self._dragging = False
        with self.canvas.before:
            PushMatrix()
            self._drag_translation = Translate(0, 0)
        with self.canvas.after:
            self._drop_target_color = Color(*GOLD_LIGHT[:3], 0)
            self._drop_target_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(7)),
                width=dp(1.6),
            )
            PopMatrix()
        self.bind(pos=self._sync_drop_target_outline, size=self._sync_drop_target_outline)
        self._sync_drop_target_outline()

    def register_action_controls(self, controls: Iterable[Widget]) -> None:
        self._action_controls.extend(controls)

    def set_primary_control(self, control: Widget) -> None:
        self._primary_control = control

    def set_drop_target(self, active: bool) -> None:
        self._drop_target_color.a = 1 if active else 0

    def on_touch_down(self, touch: object) -> bool:
        touches_action = any(control.collide_point(*touch.pos) for control in self._action_controls)
        if (
            getattr(touch, "button", "left") == "left"
            and self.collide_point(*touch.pos)
            and not touches_action
        ):
            self._drag_touch = touch
            self._drag_origin = self._window_position(touch)
            self._dragging = False
            if self._primary_control is not None:
                self._primary_control.state = "down"
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch is self._drag_touch and self._drag_origin is not None:
            position = self._window_position(touch)
            if hypot(
                position[0] - self._drag_origin[0],
                position[1] - self._drag_origin[1],
            ) >= dp(8):
                self._dragging = True
            if self._dragging:
                self.opacity = 0.68
                self._drag_translation.y = position[1] - self._drag_origin[1]
                self._on_drag(self.item_id, position)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch is self._drag_touch:
            position = self._window_position(touch)
            touch.ungrab(self)
            if self._primary_control is not None:
                self._primary_control.state = "normal"
            self.opacity = 1
            self._drag_translation.y = 0
            if self._dragging:
                self._on_drag(self.item_id, None)
                self._on_drop(self.item_id, position)
            else:
                self._on_activate()
            self._drag_touch = None
            self._drag_origin = None
            self._dragging = False
            return True
        return super().on_touch_up(touch)

    @staticmethod
    def _window_position(touch: object) -> tuple[float, float]:
        if hasattr(touch, "sx") and hasattr(touch, "sy"):
            return touch.sx * Window.width, touch.sy * Window.height
        return touch.pos

    def _sync_drop_target_outline(self, *_: object) -> None:
        inset = dp(1)
        self._drop_target_outline.rounded_rectangle = (
            self.x + inset,
            self.y + inset,
            max(0, self.width - inset * 2),
            max(0, self.height - inset * 2),
            dp(7),
        )
