from typing import Any

from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


def hex_color(value: str) -> tuple[float, float, float, float]:
    cleaned = value.lstrip("#")
    return tuple(int(cleaned[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (1,)


# Calm, low-glare application palette. Existing semantic names remain stable so
# feature modules do not need to know the exact visual tokens.
NAVY_950 = hex_color("#09111D")
NAVY_900 = hex_color("#0E1928")
NAVY_800 = hex_color("#142235")
NAVY_700 = hex_color("#1B2D44")
SLATE_700 = hex_color("#30435A")
SLATE_600 = hex_color("#52657A")
SLATE_400 = hex_color("#A8B4C2")
SLATE_200 = hex_color("#D7DDE5")
PEARL_GREY = hex_color("#EDF0F3")
GOLD = hex_color("#C9A55C")
GOLD_LIGHT = hex_color("#E0C17C")
RED = hex_color("#CE6A6A")
RED_DARK = hex_color("#753E48")
BLACK = hex_color("#05090F")
BORDER = hex_color("#2B3C52")
SUCCESS = hex_color("#69A987")


def paint_background(
    widget: Any,
    color: tuple[float, float, float, float],
    radius: float = 0,
    border_color: tuple[float, float, float, float] | None = None,
) -> None:
    with widget.canvas.before:
        background_color = Color(*color)
        background = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        outline_color = Color(*(border_color or color))
        outline = Line(
            rounded_rectangle=(*widget.pos, *widget.size, dp(radius)),
            width=1,
        )

    def update(*_: object) -> None:
        background.pos = widget.pos
        background.size = widget.size
        outline.rounded_rectangle = (*widget.pos, *widget.size, dp(radius))

    widget.bind(pos=update, size=update)
    widget._theme_background_color = background_color
    widget._theme_background = background
    widget._theme_outline_color = outline_color
    widget._theme_outline = outline


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


def style_input(field: TextInput) -> TextInput:
    field.background_normal = ""
    field.background_active = ""
    field.background_color = (0, 0, 0, 0)
    field.foreground_color = PEARL_GREY
    field.hint_text_color = SLATE_400
    field.cursor_color = GOLD_LIGHT
    field.selection_color = (*GOLD[:3], 0.45)
    field.padding = [dp(14), dp(11)]
    field.font_size = sp(15)
    if not hasattr(field, "_theme_input_shape"):
        with field.canvas.before:
            field._theme_input_color = Color(*NAVY_700)
            field._theme_input_shape = RoundedRectangle(
                pos=field.pos,
                size=field.size,
                radius=[dp(7)],
            )
        with field.canvas.after:
            field._theme_input_border_color = Color(*BORDER)
            field._theme_input_border = Line(
                rounded_rectangle=(*field.pos, *field.size, dp(7)),
                width=1,
            )

        def update_shape(*_: object) -> None:
            field._theme_input_shape.pos = field.pos
            field._theme_input_shape.size = field.size
            field._theme_input_border.rounded_rectangle = (
                *field.pos,
                *field.size,
                dp(7),
            )

        def update_focus(*_: object) -> None:
            field._theme_input_border_color.rgba = GOLD if field.focus else BORDER

        field.bind(pos=update_shape, size=update_shape, focus=update_focus)
    return field


def set_button_background(
    button: Button,
    color: tuple[float, float, float, float],
) -> None:
    """Update a themed button without exposing its canvas implementation."""
    button._theme_button_base = color
    button._theme_update_state()


def style_spinner(spinner: Spinner) -> Spinner:
    from project_planner.frontend.shared.ThemedSpinnerOption import ThemedSpinnerOption

    style_button(spinner, "secondary")
    spinner.option_cls = ThemedSpinnerOption
    spinner.sync_height = True
    return spinner


def _fit_label_height(label: Label, minimum_height: float) -> None:
    def fit_width(widget: Label, width: float) -> None:
        widget.text_size = (width, None)

    def fit_height(widget: Label, texture_size: tuple[float, float]) -> None:
        widget.height = max(minimum_height, texture_size[1])

    label.bind(width=fit_width, texture_size=fit_height)


def title_label(text: str) -> Label:
    label = Label(
        text=text,
        color=PEARL_GREY,
        font_size=sp(23),
        bold=True,
        halign="left",
        valign="middle",
        size_hint_y=None,
        height=dp(38),
    )
    _fit_label_height(label, dp(38))
    return label


def caption_label(text: str) -> Label:
    label = Label(
        text=text,
        color=SLATE_400,
        font_size=sp(13),
        halign="left",
        valign="middle",
        size_hint_y=None,
        height=dp(26),
    )
    _fit_label_height(label, dp(26))
    return label


def field_label(text: str) -> Label:
    label = Label(
        text=text.upper(),
        color=SLATE_400,
        font_size=sp(12),
        bold=True,
        halign="left",
        valign="bottom",
        size_hint_y=None,
        height=dp(24),
    )
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    return label


def section_label(text: str) -> Label:
    label = Label(
        text=text.upper(),
        color=GOLD_LIGHT,
        font_size=sp(12),
        bold=True,
        halign="left",
        valign="middle",
        size_hint_y=None,
        height=dp(32),
    )
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    return label


def empty_state_label(text: str, height: float = 72) -> Label:
    label = Label(
        text=text,
        color=SLATE_400,
        font_size=sp(13),
        halign="center",
        valign="middle",
        size_hint_y=None,
        height=dp(height),
    )
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    return label
