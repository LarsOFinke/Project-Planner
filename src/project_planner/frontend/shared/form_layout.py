from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView


def build_scrollable_form() -> tuple[ScrollView, BoxLayout]:
    form = BoxLayout(
        orientation="vertical",
        spacing=dp(8),
        padding=[dp(2), 0, dp(7), dp(4)],
        size_hint_y=None,
    )
    form.bind(minimum_height=form.setter("height"))
    scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
    viewport = AnchorLayout(anchor_y="top", size_hint_y=None)
    viewport.add_widget(form)

    def fit_viewport(*_: object) -> None:
        viewport.height = max(form.height, scroll.height)

    form.bind(height=fit_viewport)
    scroll.bind(height=fit_viewport)
    scroll.add_widget(viewport)
    return scroll, form
