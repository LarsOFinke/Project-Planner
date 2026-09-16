from typing import Any

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


def hex_color(value: str) -> tuple[float, float, float, float]:
    cleaned = value.lstrip("#")
    return tuple(int(cleaned[index : index + 2], 16) / 255 for index in (0, 2, 4)) + (1,)


NAVY_950 = hex_color("#070B14")
NAVY_900 = hex_color("#0B132B")
NAVY_800 = hex_color("#111C36")
NAVY_700 = hex_color("#192847")
SLATE_700 = hex_color("#46546A")
SLATE_600 = hex_color("#5C6A80")
SLATE_400 = hex_color("#AEB8C6")
SLATE_200 = hex_color("#D5DAE2")
PEARL_GREY = hex_color("#E7E9ED")
GOLD = hex_color("#D4A72C")
GOLD_LIGHT = hex_color("#F0C75E")
RED = hex_color("#C84B4B")
RED_DARK = hex_color("#7D2F36")
BLACK = hex_color("#030509")


def paint_background(
    widget: Any,
    color: tuple[float, float, float, float],
    radius: float = 0,
) -> None:
    with widget.canvas.before:
        background_color = Color(*color)
        background = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])

    def update(*_: object) -> None:
        background.pos = widget.pos
        background.size = widget.size

    widget.bind(pos=update, size=update)
    widget._theme_background_color = background_color
    widget._theme_background = background


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
    button.background_color = background
    button.color = foreground
    button.font_size = sp(14)
    return button


def style_input(field: TextInput) -> TextInput:
    field.background_normal = ""
    field.background_active = ""
    field.background_color = NAVY_700
    field.foreground_color = PEARL_GREY
    field.hint_text_color = SLATE_400
    field.cursor_color = GOLD_LIGHT
    field.selection_color = (*GOLD[:3], 0.45)
    field.padding = [dp(12), dp(10)]
    field.font_size = sp(15)
    return field


def style_spinner(spinner: Spinner) -> Spinner:
    style_button(spinner, "secondary")
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
        font_size=sp(24),
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
        color=SLATE_200,
        font_size=sp(12),
        bold=True,
        halign="left",
        valign="bottom",
        size_hint_y=None,
        height=dp(24),
    )
    label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    return label
