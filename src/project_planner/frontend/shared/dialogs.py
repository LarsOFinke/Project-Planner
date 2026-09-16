from collections.abc import Callable
from pathlib import Path

from kivy.core.window import Window
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
    actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
    cancel = style_button(Button(text="Cancel"), "secondary")
    submit = style_button(Button(text="Save"), "primary")
    actions.add_widget(cancel)
    actions.add_widget(submit)
    content.add_widget(value)
    content.add_widget(actions)
    popup = Popup(
        title=title,
        title_color=PEARL_GREY,
        title_size="18sp",
        separator_color=GOLD,
        background_color=NAVY_800,
        content=content,
        size_hint=(None, None),
        width=min(Window.width * 0.86, dp(560)),
        height=min(Window.height * 0.9, dp(190)),
    )

    def accept(*_: object) -> None:
        if not value.text.strip():
            value.hint_text = "A value is required"
            return
        on_submit(value.text.strip())
        popup.dismiss()

    cancel.bind(on_release=lambda *_: popup.dismiss())
    submit.bind(on_release=accept)
    value.bind(on_text_validate=accept)
    popup.open()
    value.focus = True


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
        title_size="18sp",
        separator_color=GOLD,
        background_color=NAVY_800,
        content=content,
        size_hint=(None, None),
        width=min(Window.width * 0.9, dp(1000)),
        height=min(Window.height * 0.9, dp(720)),
    )

    def accept(*_: object) -> None:
        if chooser.selection:
            on_submit(chooser.selection[0])
            popup.dismiss()

    cancel.bind(on_release=lambda *_: popup.dismiss())
    insert.bind(on_release=accept)
    popup.open()
