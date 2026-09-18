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

from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner_frontend.calendar.DateInput import DateInput
from project_planner_frontend.shared.date_parser import parse_optional_date
from project_planner_frontend.shared.form_layout import build_scrollable_form
from project_planner_frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    RED,
    SLATE_400,
    field_label,
    paint_background,
    section_label,
    style_button,
    style_input,
    style_spinner,
)


class NewProjectPopup(Popup):
    def __init__(
        self,
        on_create: Callable[
            [
                str,
                str,
                date | None,
                date | None,
                PlanningMethod,
                str,
                str,
                SectionType | None,
            ],
            None,
        ],
        **kwargs: object,
    ) -> None:
        self._on_create = on_create
        content = self._build_content()
        super().__init__(
            title="New project",
            title_color=PEARL_GREY,
            title_size="18sp",
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.94, dp(760)),
            height=min(Window.height * 0.94, dp(760)),
            **kwargs,
        )

    def _build_content(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        form.add_widget(section_label("Project brief"))
        self.name = self._field(form, "Project name", "Clear, short project name")
        self.description = self._field(
            form, "Short description", "What should this project accomplish?", multiline=True
        )
        form.add_widget(section_label("Schedule and planning"))
        dates = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(10))
        start_box = BoxLayout(orientation="vertical")
        start_box.add_widget(field_label("Start date"))
        self.start_date = DateInput()
        start_box.add_widget(self.start_date)
        target_box = BoxLayout(orientation="vertical")
        target_box.add_widget(field_label("Target date"))
        self.target_date = DateInput()
        target_box.add_widget(self.target_date)
        dates.add_widget(start_box)
        dates.add_widget(target_box)
        form.add_widget(dates)
        form.add_widget(field_label("Planning model"))
        self.method = style_spinner(
            Spinner(
                text="Custom",
                values=[method.value.title() for method in PlanningMethod],
                size_hint_y=None,
                height=dp(48),
            )
        )
        self.method.bind(text=self._method_changed)
        form.add_widget(self.method)
        self.guidance = Label(
            text="Custom: choose a planning model per section.",
            color=SLATE_400,
            halign="left",
            size_hint_y=None,
            height=dp(34),
        )
        self.guidance.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        form.add_widget(self.guidance)
        form.add_widget(field_label("Custom starting structure"))
        self.custom_start = style_spinner(
            Spinner(
                text="Start Blank",
                values=["Start Blank", "Add Agile Structure", "Add Waterfall Structure"],
                size_hint_y=None,
                height=dp(48),
            )
        )
        form.add_widget(self.custom_start)
        form.add_widget(section_label("People"))
        people = BoxLayout(size_hint_y=None, height=dp(76), spacing=dp(10))
        owner_box = BoxLayout(orientation="vertical")
        owner_box.add_widget(field_label("Project owner"))
        self.owner = style_input(TextInput(hint_text="Optional", multiline=False))
        owner_box.add_widget(self.owner)
        assignee_box = BoxLayout(orientation="vertical")
        assignee_box.add_widget(field_label("Assignee"))
        self.assignee = style_input(TextInput(hint_text="Optional", multiline=False))
        assignee_box.add_widget(self.assignee)
        people.add_widget(owner_box)
        people.add_widget(assignee_box)
        form.add_widget(people)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(28))
        form.add_widget(self.feedback)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = style_button(Button(text="Create project"), "primary")
        cancel = style_button(Button(text="Cancel"), "secondary")
        save.bind(on_release=self._save)
        cancel.bind(on_release=lambda *_: self.dismiss())
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        return content

    def _field(self, form: BoxLayout, label: str, hint: str, multiline: bool = False) -> TextInput:
        form.add_widget(field_label(label))
        field = style_input(
            TextInput(
                hint_text=hint,
                multiline=multiline,
                size_hint_y=None,
                height=dp(92 if multiline else 48),
            )
        )
        form.add_widget(field)
        return field

    def _method_changed(self, _spinner: Spinner, value: str) -> None:
        guidance = {
            "Agile": "Agile: iterative work in Backlog, planned Sprints, and Completed.",
            "Waterfall": "Waterfall: sequential Phases, Tasks, and Timeline.",
            "Custom": "Custom: choose Free, Agile, or Waterfall per section.",
        }
        self.guidance.text = guidance[value]
        self.custom_start.disabled = value != "Custom"

    def _save(self, *_: object) -> None:
        try:
            if not self.name.text.strip():
                raise ValueError("Project name is required")
            start_date = parse_optional_date(self.start_date.text, "Start date")
            target_date = parse_optional_date(self.target_date.text, "Target date")
            method = PlanningMethod(self.method.text.lower())
            custom_type = {
                "Start Blank": None,
                "Add Agile Structure": SectionType.AGILE,
                "Add Waterfall Structure": SectionType.WATERFALL,
            }[self.custom_start.text]
            self._on_create(
                self.name.text.strip(),
                self.description.text.strip(),
                start_date,
                target_date,
                method,
                self.owner.text.strip(),
                self.assignee.text.strip(),
                custom_type if method is PlanningMethod.CUSTOM else None,
            )
        except ValueError as error:
            self.feedback.text = str(error)
            return
        self.dismiss()
