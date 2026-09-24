from collections.abc import Callable

from kivy.metrics import dp, sp
from kivy.uix.button import Button

from project_planner_frontend.shared.theme import GOLD, NAVY_800, SLATE_600, hex_color


class TextWidget(Button):
    def __init__(
        self,
        element_id: str,
        text: str,
        color_hex: str,
        on_select: Callable[[str], None],
        on_edit_start: Callable[[], None],
        on_change: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            text=text,
            color=hex_color(color_hex),
            background_normal="",
            background_color=NAVY_800,
            size_hint=(None, None),
            size=(dp(180), dp(80)),
            font_size=sp(16),
            halign="left",
            valign="middle",
            **kwargs,
        )
        self.element_id = element_id
        self.color_hex = color_hex
        self._on_select = on_select
        self._on_edit_start = on_edit_start
        self._on_change = on_change
        self._drag_offset = (0.0, 0.0)
        self._drag_started = False
        self.bind(size=self._fit_text)
        self._fit_text()

    def _fit_text(self, *_: object) -> None:
        self.text_size = (max(0, self.width - dp(16)), max(0, self.height - dp(12)))

    def set_selected(self, selected: bool) -> None:
        self.background_color = GOLD if selected else SLATE_600

    def on_touch_down(self, touch: object) -> bool:
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self._drag_offset = (touch.x - self.x, touch.y - self.y)
            self._drag_started = False
            self._on_select(self.element_id)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: object) -> bool:
        if touch.grab_current is self:
            if not self._drag_started:
                self._on_edit_start()
                self._drag_started = True
            self.pos = touch.x - self._drag_offset[0], touch.y - self._drag_offset[1]
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch: object) -> bool:
        if touch.grab_current is self:
            touch.ungrab(self)
            if self._drag_started:
                self._on_change()
            return True
        return super().on_touch_up(touch)
