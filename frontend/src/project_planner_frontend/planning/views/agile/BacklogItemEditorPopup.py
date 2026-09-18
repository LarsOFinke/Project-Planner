from collections.abc import Callable

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
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


class BacklogItemEditorPopup(Popup):
    def __init__(
        self,
        item: BacklogItem | None,
        on_save: Callable[[str, str, BacklogPriority, BacklogStatus, str], None],
        **kwargs: object,
    ) -> None:
        self._item = item
        self._on_save = on_save
        content = self._build()
        super().__init__(
            title="Edit backlog item" if item else "New backlog item",
            title_color=PEARL_GREY,
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.92, dp(700)),
            height=min(Window.height * 0.9, dp(560)),
            **kwargs,
        )

    def _build(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        paint_background(content, NAVY_800)
        scroll, form = build_scrollable_form()
        self.title_input = self._input(form, "Title", "Work item title")
        self.description = self._input(form, "Description", "Short description", multiline=True)
        self.assignee = self._input(form, "Assignee", "Optional")
        labels = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        labels.add_widget(field_label("Priority"))
        labels.add_widget(field_label("Status"))
        form.add_widget(labels)
        choices = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.priority = style_spinner(
            Spinner(values=[value.value.title() for value in BacklogPriority])
        )
        self.status = style_spinner(
            Spinner(values=[self._status_label(value) for value in BacklogStatus])
        )
        choices.add_widget(self.priority)
        choices.add_widget(self.status)
        form.add_widget(choices)
        self.feedback = Label(text="", color=RED, size_hint_y=None, height=dp(26))
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
            self.priority.text = self._item.priority.value.title()
            self.status.text = self._status_label(self._item.status)
        else:
            self.priority.text = BacklogPriority.MEDIUM.value.title()
            self.status.text = self._status_label(BacklogStatus.BACKLOG)
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
                height=dp(90 if multiline else 46),
            )
        )
        content.add_widget(field)
        return field

    def _save(self, *_: object) -> None:
        if not self.title_input.text.strip():
            self.feedback.text = "Title is required"
            return
        self._on_save(
            self.title_input.text,
            self.description.text,
            BacklogPriority(self.priority.text.lower()),
            BacklogStatus(self.status.text.lower().replace(" ", "_")),
            self.assignee.text,
        )
        self.dismiss()

    @staticmethod
    def _status_label(status: BacklogStatus) -> str:
        return status.value.replace("_", " ").title()
