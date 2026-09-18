from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.button import Button


class NodeWidget(Button):
    def __init__(
        self,
        node_id: str,
        on_select: Callable[[str], None],
        on_move: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(size_hint=(None, None), size=(dp(150), dp(64)), **kwargs)
        self.node_id = node_id
        self._on_select = on_select
        self._on_move = on_move
        self._drag_offset = (0.0, 0.0)

    def on_touch_down(self, touch: object) -> bool:
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._drag_offset = (touch.x - self.x, touch.y - self.y)
            self._on_select(self.node_id)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch.grab_current is self:
            self.pos = (
                touch.x - self._drag_offset[0],
                touch.y - self._drag_offset[1],
            )
            self._on_move()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            self._on_move()
            return True
        return super().on_touch_up(touch)
