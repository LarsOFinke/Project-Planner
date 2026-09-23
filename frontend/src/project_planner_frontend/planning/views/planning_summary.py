from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from project_planner_frontend.shared.theme import SLATE_200, SLATE_400, style_button


def planning_summary(
    title: str,
    fields: tuple[tuple[str, str, float], ...],
) -> tuple[BoxLayout, Button]:
    """Build a left-aligned title with stable metadata columns below it."""
    content = BoxLayout(orientation="vertical", spacing=dp(3))
    title_button = style_button(
        Button(
            text=title,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(36),
        ),
        "quiet",
    )
    title_button.bind(
        size=lambda widget, size: setattr(widget, "text_size", (max(0, size[0] - dp(20)), size[1]))
    )
    content.add_widget(title_button)

    details = BoxLayout(
        size_hint_y=None,
        height=dp(38),
        spacing=dp(8),
        padding=[dp(10), 0, dp(4), 0],
    )
    for heading, value, width_weight in fields:
        cell = BoxLayout(orientation="vertical", size_hint_x=width_weight)
        heading_label = Label(
            text=heading.upper(),
            color=SLATE_400,
            font_size=sp(9),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(16),
            shorten=True,
        )
        value_label = Label(
            text=value,
            color=SLATE_200,
            font_size=sp(11),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
            shorten=True,
        )
        for label in (heading_label, value_label):
            label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
            cell.add_widget(label)
        details.add_widget(cell)
    content.add_widget(details)
    return content, title_button
