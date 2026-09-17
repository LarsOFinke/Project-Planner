from kivy.metrics import dp
from kivy.uix.spinner import SpinnerOption

from project_planner.frontend.shared.theme import style_button


class ThemedSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(size_hint_y=None, height=dp(44), **kwargs)
        style_button(self, "quiet")
