from collections.abc import Callable
from datetime import date

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner_frontend.calendar.DateInput import DateInput
from project_planner_frontend.shared.date_parser import format_optional_date, parse_optional_date
from project_planner_frontend.shared.form_layout import build_scrollable_form
from project_planner_frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    RED,
    field_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
)


class WaterfallTaskEditorPopup(Popup):
    def __init__(
        self,
        task: WaterfallTask | None,
        on_save: Callable[[str, str, str, date | None, date | None, WaterfallTaskStatus], None],
        **kwargs: object,
    ) -> None:
        self._task = task
        self._on_save = on_save
        content = self._build()
        super().__init__(
            title="Edit task" if task else "New task",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.92, dp(720)),
            height=min(Window.height * 0.94, dp(650)),
            **kwargs,
        )

    def _build(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        self.title_input = self._input(form, "Title", "Task title")
        self.description = self._input(form, "Description", "Short description", True)
        self.assignee = self._input(form, "Assignee", "Optional")
        dates = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(8))
        start_box = BoxLayout(orientation="vertical")
        start_box.add_widget(field_label("Start date"))
        self.start_date = DateInput()
        start_box.add_widget(self.start_date)
        due_box = BoxLayout(orientation="vertical")
        due_box.add_widget(field_label("Due date"))
        self.due_date = DateInput()
        due_box.add_widget(self.due_date)
        dates.add_widget(start_box)
        dates.add_widget(due_box)
        form.add_widget(dates)
        form.add_widget(field_label("Status"))
        self.status = style_spinner(
            Spinner(
                text=self._label(WaterfallTaskStatus.NOT_STARTED),
                values=[self._label(value) for value in WaterfallTaskStatus],
                size_hint_y=None,
                height=dp(46),
            )
        )
        form.add_widget(self.status)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(26))
        form.add_widget(self.feedback)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = style_button(Button(text="Save task"), "primary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        save.bind(on_release=self._save)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        if self._task:
            self.title_input.text = self._task.title
            self.description.text = self._task.description
            self.assignee.text = self._task.assignee
            self.start_date.text = format_optional_date(self._task.start_date)
            self.due_date.text = format_optional_date(self._task.due_date)
            self.status.text = self._label(self._task.status)
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
                height=dp(88 if multiline else 46),
            )
        )
        content.add_widget(field)
        return field

    def _save(self, *_: object) -> None:
        try:
            if not self.title_input.text.strip():
                raise ValueError("Title is required")
            start = parse_optional_date(self.start_date.text, "Start date")
            due = parse_optional_date(self.due_date.text, "Due date")
            if start and due and due < start:
                raise ValueError("Due date must not be before start date")
            self._on_save(
                self.title_input.text,
                self.description.text,
                self.assignee.text,
                start,
                due,
                WaterfallTaskStatus(self.status.text.lower().replace(" ", "_")),
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.dismiss()

    @staticmethod
    def _label(status: WaterfallTaskStatus) -> str:
        return status.value.replace("_", " ").title()
