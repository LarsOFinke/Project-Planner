from collections.abc import Callable

from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from project_planner.core.domain.phases.Phase import Phase
from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.frontend.shared.dialogs import show_confirmation
from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    SLATE_400,
    field_label,
    paint_background,
    style_button,
    style_input,
    style_spinner,
)


class PhaseEditorPopup(Popup):
    def __init__(
        self,
        phase: Phase | None,
        on_save: Callable[[str, str, PhaseStatus], None],
        **kwargs: object,
    ) -> None:
        self._phase = phase
        self._on_save = on_save
        content = self._build_content()
        super().__init__(
            title="Edit phase" if phase is not None else "New phase",
            title_color=PEARL_GREY,
            title_size="18sp",
            separator_color=GOLD,
            background_color=NAVY_800,
            content=content,
            size_hint=(None, None),
            width=min(Window.width * 0.9, dp(680)),
            height=min(Window.height * 0.92, dp(520)),
            **kwargs,
        )
        self.bind(on_open=self._queue_population)

    def _build_content(self) -> BoxLayout:
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        paint_background(content, NAVY_800)
        form = BoxLayout(
            orientation="vertical",
            spacing=dp(7),
            size_hint_y=None,
            padding=[dp(2), 0, dp(7), 0],
        )
        form.bind(minimum_height=form.setter("height"))
        form.add_widget(field_label("Name"))
        self.name_input = style_input(
            TextInput(
                hint_text="Phase name",
                multiline=False,
                size_hint_y=None,
                height=dp(48),
            )
        )
        form.add_widget(self.name_input)
        form.add_widget(field_label("Description"))
        self.description_input = style_input(
            TextInput(
                hint_text="Purpose, deliverables, and completion criteria",
                size_hint_y=None,
                height=dp(110),
            )
        )
        form.add_widget(self.description_input)
        form.add_widget(field_label("Status"))
        initial_status = self._phase.status if self._phase is not None else PhaseStatus.PLANNED
        self.status = style_spinner(
            Spinner(
                text=initial_status.value.title(),
                values=[status.value.title() for status in PhaseStatus],
                size_hint_y=None,
                height=dp(48),
            )
        )
        form.add_widget(self.status)
        metadata = Label(
            text=self._metadata_text(),
            color=SLATE_400,
            font_size="12sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(42),
        )
        metadata.bind(size=lambda widget, size: setattr(widget, "text_size", size))
        form.add_widget(metadata)
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(5))
        scroll.add_widget(form)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        cancel = style_button(Button(text="Cancel"), "secondary")
        save = style_button(Button(text="Save phase"), "primary")
        cancel.bind(on_release=lambda *_: self.dismiss())
        save.bind(on_release=self._save)
        self.name_input.bind(on_text_validate=self._save)
        actions.add_widget(save)
        actions.add_widget(cancel)
        content.add_widget(scroll)
        content.add_widget(actions)
        return content

    def _queue_population(self, *_: object) -> None:
        if self._phase is None:
            self.name_input.focus = True
            return
        self.name_input.bind(width=self._populate_fields)
        self._populate_fields(self.name_input, self.name_input.width)

    def _populate_fields(self, _field: TextInput, width: float) -> None:
        if self._phase is None or width == 100:
            return
        self.name_input.unbind(width=self._populate_fields)
        self.name_input.text = self._phase.name
        self.description_input.text = self._phase.description
        self.name_input.focus = True

    def _metadata_text(self) -> str:
        if self._phase is None:
            return "Created and updated timestamps are assigned when this phase is saved."
        return (
            f"Created {self._phase.created_at:%Y-%m-%d %H:%M}   ·   "
            f"Updated {self._phase.updated_at:%Y-%m-%d %H:%M}"
        )

    def _save(self, *_: object) -> None:
        name = self.name_input.text.strip()
        if not name:
            self.name_input.hint_text = "A phase name is required"
            return
        self._on_save(
            name,
            self.description_input.text.strip(),
            PhaseStatus(self.status.text.lower()),
        )
        self.dismiss()
        show_confirmation("Phase changes saved locally.")
