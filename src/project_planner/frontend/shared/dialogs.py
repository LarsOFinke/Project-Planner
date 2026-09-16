from collections.abc import Callable
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    paint_background,
    style_button,
    style_input,
)


def open_text_dialog(
    title: str,
    hint: str,
    on_submit: Callable[[str], None],
    initial: str = "",
) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
    paint_background(content, NAVY_800)
    value = style_input(
        TextInput(
            text=initial,
            hint_text=hint,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
        )
    )
    submit = style_button(
        Button(text="Save", size_hint_y=None, height=dp(46)), "primary"
    )
    content.add_widget(value)
    content.add_widget(submit)
    popup = Popup(
        title=title,
        title_color=PEARL_GREY,
        separator_color=GOLD,
        background_color=NAVY_800,
        content=content,
        size_hint=(0.52, 0.32),
    )

    def accept(*_: object) -> None:
        if not value.text.strip():
            value.hint_text = "A value is required"
            return
        on_submit(value.text.strip())
        popup.dismiss()

    submit.bind(on_release=accept)
    popup.open()


def open_image_dialog(on_submit: Callable[[str], None]) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
    paint_background(content, NAVY_800)
    chooser = FileChooserListView(
        path=str(Path.home()),
        filters=[
            "*.png",
            "*.jpg",
            "*.jpeg",
            "*.gif",
            "*.bmp",
            "*.webp",
            "*.PNG",
            "*.JPG",
            "*.JPEG",
            "*.GIF",
            "*.BMP",
            "*.WEBP",
        ],
        multiselect=False,
    )
    actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
    cancel = style_button(Button(text="Cancel"), "secondary")
    insert = style_button(Button(text="Insert image"), "primary")
    actions.add_widget(cancel)
    actions.add_widget(insert)
    content.add_widget(chooser)
    content.add_widget(actions)
    popup = Popup(
        title="Insert image",
        title_color=PEARL_GREY,
        separator_color=GOLD,
        background_color=NAVY_800,
        content=content,
        size_hint=(0.86, 0.86),
    )

    def accept(*_: object) -> None:
        if chooser.selection:
            on_submit(chooser.selection[0])
            popup.dismiss()

    cancel.bind(on_release=lambda *_: popup.dismiss())
    insert.bind(on_release=accept)
    popup.open()
