from collections.abc import Callable
from datetime import date
from functools import partial

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from project_planner.core.application.calendar.CalendarService import CalendarService
from project_planner.core.domain.calendar.CalendarDay import CalendarDay
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    SLATE_400,
    paint_background,
    style_button,
)


class CalendarPopup(Popup):
    def __init__(
        self,
        selected: date | None,
        on_select: Callable[[date | None], None],
        service: CalendarService | None = None,
        **kwargs: object,
    ) -> None:
        self._service = service or CalendarService()
        self._selected = selected
        self._displayed = selected or self._service.today()
        self._on_select = on_select
        content = self._build()
        super().__init__(
            title="Select date",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.92, dp(620)),
            height=min(Window.height * 0.92, dp(590)),
            **kwargs,
        )
        self._render_month()

    def _build(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        navigation = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        previous = style_button(Button(text="Previous"), "secondary")
        next_month = style_button(Button(text="Next"), "secondary")
        previous.bind(on_release=partial(self._move_month, -1))
        next_month.bind(on_release=partial(self._move_month, 1))
        self._month_label = Label(text="", color=PEARL_GREY, bold=True)
        navigation.add_widget(previous)
        navigation.add_widget(self._month_label)
        navigation.add_widget(next_month)
        content.add_widget(navigation)
        weekdays = GridLayout(cols=7, size_hint_y=None, height=dp(32), spacing=dp(3))
        for weekday in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"):
            weekdays.add_widget(Label(text=weekday, color=SLATE_400, bold=True))
        content.add_widget(weekdays)
        self._days = GridLayout(cols=7, spacing=dp(3))
        content.add_widget(self._days)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        today = style_button(Button(text="Today"), "primary")
        clear = style_button(Button(text="Clear"), "secondary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        today.bind(on_release=self._select_today)
        clear.bind(on_release=self._clear)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(today)
        actions.add_widget(clear)
        actions.add_widget(cancel)
        content.add_widget(actions)
        return content

    def _render_month(self) -> None:
        self._days.clear_widgets()
        self._month_label.text = self._displayed.strftime("%B %Y")
        for week in self._service.month(self._displayed.year, self._displayed.month):
            for day in week:
                variant = "primary" if day.value == self._selected else "quiet"
                button = style_button(Button(text=str(day.value.day)), variant)
                if not day.in_month and day.value != self._selected:
                    button.color = SLATE_400
                button.bind(on_release=partial(self._select_day, day))
                self._days.add_widget(button)

    def _move_month(self, offset: int, *_: object) -> None:
        self._displayed = self._service.shift_month(self._displayed, offset)
        self._render_month()

    def _select_day(self, day: CalendarDay, *_: object) -> None:
        self._on_select(day.value)
        self.dismiss()

    def _select_today(self, *_: object) -> None:
        self._on_select(self._service.today())
        self.dismiss()

    def _clear(self, *_: object) -> None:
        self._on_select(None)
        self.dismiss()
