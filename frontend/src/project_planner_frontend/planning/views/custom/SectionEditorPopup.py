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

from project_planner.modules.planning.entities.PlanningSection import PlanningSection
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner_frontend.calendar.DateInput import DateInput
from project_planner_frontend.shared.date_parser import format_optional_date, parse_optional_date
from project_planner_frontend.shared.form_layout import build_scrollable_form
from project_planner_frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    RED,
    caption_label,
    field_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
)


class SectionEditorPopup(Popup):
    def __init__(
        self,
        section: PlanningSection | None,
        default_type: SectionType,
        on_save: Callable[[str, str, SectionType, date | None, date | None, SectionStatus], None],
        **kwargs: object,
    ) -> None:
        self._section = section
        self._on_save = on_save
        content = self._build(default_type)
        super().__init__(
            title="Edit section" if section else "Add section",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.92, dp(720)),
            height=min(Window.height * 0.94, dp(690)),
            **kwargs,
        )

    def _build(self, default_type: SectionType) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        self.name_input = self._input(form, "Section name", "e.g. Discovery")
        self.description = self._input(form, "Description", "Optional", True)
        form.add_widget(field_label("Planning model"))
        self.section_type = style_spinner(
            Spinner(
                text=default_type.value.title(),
                values=[value.value.title() for value in SectionType],
                size_hint_y=None,
                height=dp(46),
            )
        )
        form.add_widget(self.section_type)
        form.add_widget(
            caption_label(
                text=(
                    "Agile: iterative cycles · Waterfall: sequential phases · "
                    "Free: no predefined planning structure"
                )
            )
        )
        dates = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(8))
        start_box = BoxLayout(orientation="vertical")
        start_box.add_widget(field_label("Optional start date"))
        self.start_date = DateInput()
        start_box.add_widget(self.start_date)
        end_box = BoxLayout(orientation="vertical")
        end_box.add_widget(field_label("Optional end date"))
        self.end_date = DateInput()
        end_box.add_widget(self.end_date)
        dates.add_widget(start_box)
        dates.add_widget(end_box)
        form.add_widget(dates)
        form.add_widget(field_label("Status"))
        self.status = style_spinner(
            Spinner(
                text=self._status_label(SectionStatus.NOT_STARTED),
                values=[self._status_label(value) for value in SectionStatus],
                size_hint_y=None,
                height=dp(46),
            )
        )
        form.add_widget(self.status)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(26))
        form.add_widget(self.feedback)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = style_button(Button(text="Save section"), "primary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        save.bind(on_release=self._save)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        if self._section:
            self.name_input.text = self._section.name
            self.description.text = self._section.description
            self.section_type.text = self._section.section_type.value.title()
            self.start_date.text = format_optional_date(self._section.start_date)
            self.end_date.text = format_optional_date(self._section.end_date)
            self.status.text = self._status_label(self._section.status)
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
                height=dp(82 if multiline else 46),
            )
        )
        content.add_widget(field)
        return field

    def _save(self, *_: object) -> None:
        try:
            if not self.name_input.text.strip():
                raise ValueError("Section name is required")
            start = parse_optional_date(self.start_date.text, "Start date")
            end = parse_optional_date(self.end_date.text, "End date")
            if start and end and end < start:
                raise ValueError("End date must not be before start date")
            self._on_save(
                self.name_input.text,
                self.description.text,
                SectionType(self.section_type.text.lower()),
                start,
                end,
                SectionStatus(self.status.text.lower().replace(" ", "_")),
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.dismiss()

    @staticmethod
    def _status_label(status: SectionStatus) -> str:
        return status.value.replace("_", " ").title()
