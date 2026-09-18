from typing import Any

from kivy.graphics import Color, InstructionGroup, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner_frontend.shared.button_style import set_button_background, style_button
from project_planner_frontend.shared.color import hex_color
from project_planner_frontend.shared.palette import (
    BLACK,
    BORDER,
    GOLD,
    GOLD_LIGHT,
    NAVY_700,
    NAVY_800,
    NAVY_900,
    NAVY_950,
    PEARL_GREY,
    RED,
    RED_DARK,
    SLATE_200,
    SLATE_400,
    SLATE_600,
    SLATE_700,
    SUCCESS,
)

__all__ = [
    "BLACK",
    "BORDER",
    "GOLD",
    "GOLD_LIGHT",
    "NAVY_700",
    "NAVY_800",
    "NAVY_900",
    "NAVY_950",
    "PEARL_GREY",
    "RED",
    "RED_DARK",
    "SLATE_200",
    "SLATE_400",
    "SLATE_600",
    "SLATE_700",
    "SUCCESS",
    "caption_label",
    "empty_state_label",
    "field_label",
    "hex_color",
    "paint_background",
    "section_label",
    "set_button_background",
    "style_button",
    "style_input",
    "style_spinner",
    "title_label",
]


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


def style_input(field: TextInput) -> TextInput:
    field.background_normal = ""
    field.background_active = ""
    field.background_color = (0, 0, 0, 0)
    field.foreground_color = PEARL_GREY
    field.disabled_foreground_color = (*SLATE_400[:3], 0.55)
    field.hint_text_color = SLATE_400
    field.cursor_color = GOLD_LIGHT
    field.selection_color = (*GOLD[:3], 0.45)
    field.padding = [dp(14), dp(11)]
    field.font_size = sp(15)
    if not hasattr(field, "_theme_input_shape"):
        field._theme_input_background = InstructionGroup()
        field._theme_input_color = Color(*NAVY_700)
        field._theme_input_shape = RoundedRectangle(
            pos=field.pos,
            size=field.size,
            radius=[dp(7)],
        )
        field._theme_input_background.add(field._theme_input_color)
        field._theme_input_background.add(field._theme_input_shape)
        # Kivy's TextInput rule leaves its foreground/cursor Color as the final
        # canvas.before instruction. The custom surface must precede that rule;
        # appending it would tint text navy and paint over the cursor.
        field.canvas.before.insert(0, field._theme_input_background)
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


def style_spinner(spinner: Spinner) -> Spinner:
    from project_planner_frontend.shared.ThemedSpinnerOption import ThemedSpinnerOption

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
