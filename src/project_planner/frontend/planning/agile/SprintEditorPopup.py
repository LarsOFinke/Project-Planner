from collections.abc import Callable, Sequence
from datetime import date

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from project_planner.core.domain.agile.BacklogItem import BacklogItem
from project_planner.frontend.calendar.DateInput import DateInput
from project_planner.frontend.shared.date_parser import parse_optional_date
from project_planner.frontend.shared.form_layout import build_scrollable_form
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    RED,
    field_label,
    paint_background,
    style_button,
    style_input,
)


class SprintEditorPopup(Popup):
    def __init__(
        self,
        items: Sequence[BacklogItem],
        on_save: Callable[[str, date, date, str, list[str]], None],
        **kwargs: object,
    ) -> None:
        self._on_save = on_save
        self._checks: dict[str, CheckBox] = {}
        content = self._build(items)
        super().__init__(
            title="Add sprint",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.94, dp(760)),
            height=min(Window.height * 0.94, dp(660)),
            **kwargs,
        )

    def _build(self, items: Sequence[BacklogItem]) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        self.name = self._input(form, "Sprint name", "Sprint name")
        dates = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(8))
        start_box = BoxLayout(orientation="vertical")
        start_box.add_widget(field_label("Start date"))
        self.start_date = DateInput()
        start_box.add_widget(self.start_date)
        end_box = BoxLayout(orientation="vertical")
        end_box.add_widget(field_label("End date"))
        self.end_date = DateInput()
        end_box.add_widget(self.end_date)
        dates.add_widget(start_box)
        dates.add_widget(end_box)
        form.add_widget(dates)
        self.goal = self._input(form, "Sprint goal", "One concise goal", multiline=True)
        form.add_widget(field_label("Selected backlog items"))
        rows = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        rows.bind(minimum_height=rows.setter("height"))
        if items:
            for item in items:
                row = BoxLayout(size_hint_y=None, height=dp(38))
                check = CheckBox(size_hint_x=None, width=dp(42))
                self._checks[item.id] = check
                row.add_widget(check)
                item_label = Label(text=item.title, color=PEARL_GREY, halign="left")
                item_label.bind(size=lambda widget, size: setattr(widget, "text_size", size))
                row.add_widget(item_label)
                rows.add_widget(row)
        else:
            rows.add_widget(
                Label(
                    text="No unassigned backlog items yet.",
                    color=PEARL_GREY,
                    halign="left",
                    valign="middle",
                    size_hint_y=None,
                    height=dp(42),
                )
            )
        form.add_widget(rows)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(26))
        form.add_widget(self.feedback)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = style_button(Button(text="Add sprint"), "primary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        save.bind(on_release=self._save)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        return content

    def _input(
        self, content: BoxLayout, label: str, hint: str, multiline: bool = False
    ) -> TextInput:
        content.add_widget(field_label(label))
        field = style_input(
            TextInput(
                hint_text=hint,
                multiline=multiline,
                size_hint_y=None,
                height=dp(76 if multiline else 46),
            )
        )
        content.add_widget(field)
        return field

    def _save(self, *_: object) -> None:
        try:
            start = parse_optional_date(self.start_date.text, "Start date")
            end = parse_optional_date(self.end_date.text, "End date")
            if not self.name.text.strip() or start is None or end is None:
                raise ValueError("Sprint name, start date, and end date are required")
            selected = [item_id for item_id, check in self._checks.items() if check.active]
            self._on_save(self.name.text, start, end, self.goal.text, selected)
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.dismiss()
