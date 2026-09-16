from collections.abc import Callable
from functools import partial

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from project_planner.frontend.shared.theme import (
    NAVY_800,
    paint_background,
    style_button,
)


class WorkspaceToolbox(BoxLayout):
    def __init__(
        self,
        add_shape: Callable[[str], None],
        choose_image: Callable[..., None],
        rotate: Callable[[float], None],
        scale: Callable[[float], None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(5),
            size_hint_y=None,
            height=dp(92),
            padding=dp(5),
            **kwargs,
        )
        paint_background(self, NAVY_800, 6)
        self._groups: dict[str, list[tuple[str, Callable[..., None], str]]] = {
            "Shapes": [
                ("Rectangle", lambda *_: add_shape("rectangle"), "secondary"),
                ("Ellipse", lambda *_: add_shape("ellipse"), "secondary"),
                ("Line", lambda *_: add_shape("line"), "secondary"),
                ("Arrow", lambda *_: add_shape("arrow"), "secondary"),
            ],
            "Media": [("Insert image", choose_image, "primary")],
            "Transform": [
                ("Rotate left", lambda *_: rotate(-15), "secondary"),
                ("Rotate right", lambda *_: rotate(15), "secondary"),
                ("Scale down", lambda *_: scale(0.85), "secondary"),
                ("Scale up", lambda *_: scale(1.15), "secondary"),
            ],
            "Manage": [
                ("Delete selected", delete_selected, "danger"),
                ("Clear all", clear_all, "danger"),
                ("Save now", save, "primary"),
            ],
        }
        self._category_buttons: dict[str, Button] = {}
        categories = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(5))
        for name in self._groups:
            button = style_button(Button(text=name), "quiet")
            button.bind(on_release=partial(self._show_group, name))
            self._category_buttons[name] = button
            categories.add_widget(button)
        self._actions = BoxLayout(spacing=dp(5))
        self.add_widget(categories)
        self.add_widget(self._actions)
        self._show_group("Shapes")

    def _show_group(self, name: str, *_: object) -> None:
        self._actions.clear_widgets()
        for category, button in self._category_buttons.items():
            style_button(button, "selected" if category == name else "quiet")
        for label, callback, variant in self._groups[name]:
            button = style_button(Button(text=label), variant)
            button.bind(on_release=callback)
            self._actions.add_widget(button)
