from datetime import date

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

from project_planner.modules.calendar.services.CalendarService import CalendarService
from project_planner_frontend.calendar.CalendarPopup import CalendarPopup
from project_planner_frontend.shared.theme import style_button, style_input


class DateInput(BoxLayout):
    def __init__(
        self,
        hint_text: str = "YYYY-MM-DD",
        service: CalendarService | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(orientation="horizontal", spacing=dp(5), **kwargs)
        self._service = service or CalendarService()
        self.input = style_input(TextInput(hint_text=hint_text, multiline=False))
        self.button = style_button(Button(text="Date", size_hint_x=None, width=dp(72)), "secondary")
        self.button.bind(on_release=self._open_calendar)
        self.add_widget(self.input)
        self.add_widget(self.button)

    @property
    def text(self) -> str:
        return self.input.text

    @text.setter
    def text(self, value: str) -> None:
        self.input.text = value

    @property
    def hint_text(self) -> str:
        return self.input.hint_text

    @hint_text.setter
    def hint_text(self, value: str) -> None:
        self.input.hint_text = value

    def _open_calendar(self, *_: object) -> None:
        try:
            selected = date.fromisoformat(self.text.strip()) if self.text.strip() else None
        except ValueError:
            selected = None
        CalendarPopup(selected, self._set_date, self._service).open()

    def _set_date(self, selected: date | None) -> None:
        self.text = selected.isoformat() if selected is not None else ""
