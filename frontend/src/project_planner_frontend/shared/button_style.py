from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.button import Button

from project_planner_frontend.shared.palette import (
    GOLD,
    NAVY_700,
    NAVY_950,
    PEARL_GREY,
    RED_DARK,
    SLATE_200,
    SLATE_700,
)


def style_button(button: Button, variant: str = "secondary") -> Button:
    colors = {
        "primary": (GOLD, NAVY_950),
        "secondary": (SLATE_700, PEARL_GREY),
        "quiet": (NAVY_700, SLATE_200),
        "danger": (RED_DARK, PEARL_GREY),
        "selected": (GOLD, NAVY_950),
    }
    background, foreground = colors[variant]
    button.background_normal = ""
    button.background_down = ""
    button.background_color = (0, 0, 0, 0)
    button.color = foreground
    button.font_size = sp(14)
    button.padding = [dp(12), dp(6)]
    button.shorten = True
    button.shorten_from = "right"
    button.disabled_color = (*foreground[:3], 0.45)
    button._theme_button_base = background
    if not hasattr(button, "_theme_button_shape"):
        with button.canvas.before:
            button._theme_button_color = Color(*background)
            button._theme_button_shape = RoundedRectangle(
                pos=button.pos,
                size=button.size,
                radius=[dp(7)],
            )

        def update_shape(*_: object) -> None:
            button._theme_button_shape.pos = button.pos
            button._theme_button_shape.size = button.size

        def update_state(*_: object) -> None:
            base = button._theme_button_base
            factor = 0.86 if button.state == "down" else 1.0
            alpha = 0.38 if button.disabled else base[3]
            button._theme_button_color.rgba = (
                base[0] * factor,
                base[1] * factor,
                base[2] * factor,
                alpha,
            )

        button._theme_update_state = update_state
        button.bind(pos=update_shape, size=update_shape)
        button.bind(state=update_state, disabled=update_state)
    button._theme_update_state()
    return button


def set_button_background(
    button: Button,
    color: tuple[float, float, float, float],
) -> None:
    """Update a themed button without exposing its canvas implementation."""
    button._theme_button_base = color
    button._theme_update_state()
