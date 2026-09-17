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

from project_planner.core.domain.custom.SectionItem import SectionItem
from project_planner.core.domain.custom.SectionStatus import SectionStatus
from project_planner.frontend.calendar.DateInput import DateInput
from project_planner.frontend.shared.date_parser import format_optional_date, parse_optional_date
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
    style_spinner,
)


class SectionItemEditorPopup(Popup):
    def __init__(
        self,
        item: SectionItem | None,
        on_save: Callable[[str, str, str, SectionStatus, date | None], None],
        **kwargs: object,
    ) -> None:
        self._item = item
        self._on_save = on_save
        content = self._build()
        super().__init__(
            title="Edit item" if item else "New item",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.9, dp(680)),
            height=min(Window.height * 0.92, dp(590)),
            **kwargs,
        )

    def _build(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        self.title_input = self._input(form, "Title", "Item title")
        self.description = self._input(form, "Description", "Optional", True)
        self.assignee = self._input(form, "Assignee", "Optional")
        form.add_widget(field_label("Optional date"))
        self.item_date = DateInput(size_hint_y=None, height=dp(44))
        form.add_widget(self.item_date)
        form.add_widget(field_label("Status"))
        self.status = style_spinner(
            Spinner(
                text="Not Started",
                values=[value.value.replace("_", " ").title() for value in SectionStatus],
                size_hint_y=None,
                height=dp(46),
            )
        )
        form.add_widget(self.status)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(24))
        form.add_widget(self.feedback)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = style_button(Button(text="Save item"), "primary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        save.bind(on_release=self._save)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        if self._item:
            self.title_input.text = self._item.title
            self.description.text = self._item.description
            self.assignee.text = self._item.assignee
            self.item_date.text = format_optional_date(self._item.item_date)
            self.status.text = self._item.status.value.replace("_", " ").title()
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
                height=dp(76 if multiline else 44),
            )
        )
        content.add_widget(field)
        return field

    def _save(self, *_: object) -> None:
        try:
            if not self.title_input.text.strip():
                raise ValueError("Title is required")
            item_date = parse_optional_date(self.item_date.text, "Date")
            self._on_save(
                self.title_input.text,
                self.description.text,
                self.assignee.text,
                SectionStatus(self.status.text.lower().replace(" ", "_")),
                item_date,
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.dismiss()
