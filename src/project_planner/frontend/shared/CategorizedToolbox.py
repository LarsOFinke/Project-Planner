from collections.abc import Callable, Mapping, Sequence
from functools import partial

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from project_planner.frontend.shared.theme import (
    BORDER,
    NAVY_800,
    paint_background,
    style_button,
)

ToolboxAction = tuple[str, Callable[..., None], str]


class CategorizedToolbox(BoxLayout):
    def __init__(
        self,
        groups: Mapping[str, Sequence[ToolboxAction]],
        *,
        initial_group: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(102),
            padding=dp(7),
            **kwargs,
        )
        if not groups:
            raise ValueError("A toolbox requires at least one group")
        self._groups = {name: tuple(actions) for name, actions in groups.items()}
        paint_background(self, NAVY_800, 8, BORDER)
        self._category_buttons: dict[str, Button] = {}
        categories = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        for name in self._groups:
            button = style_button(Button(text=name), "quiet")
            if len(self._groups) > 4:
                button.font_size = sp(12)
            button.bind(on_release=partial(self.show_group, name))
            self._category_buttons[name] = button
            categories.add_widget(button)
        self._actions = BoxLayout(spacing=dp(5))
        self.add_widget(categories)
        self.add_widget(self._actions)
        self.show_group(initial_group or next(iter(self._groups)))

    def show_group(self, name: str, *_: object) -> None:
        if name not in self._groups:
            raise ValueError(f"Unknown toolbox group: {name}")
        self._actions.clear_widgets()
        for category, button in self._category_buttons.items():
            style_button(button, "selected" if category == name else "quiet")
        for label, callback, variant in self._groups[name]:
            button = style_button(Button(text=label), variant)
            if len(self._groups[name]) > 4:
                button.font_size = sp(12)
            button.bind(on_release=callback)
            self._actions.add_widget(button)
