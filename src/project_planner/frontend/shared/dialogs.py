from collections.abc import Callable
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from project_planner.frontend.shared.theme import (
    GOLD,
    NAVY_800,
    PEARL_GREY,
    RED,
    paint_background,
    style_button,
    style_input,
)


def show_error(message: str) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
    paint_background(content, NAVY_800)
    details = Label(
        text=message,
        color=PEARL_GREY,
        font_size="15sp",
        halign="left",
        valign="middle",
    )
    details.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    close = style_button(Button(text="Close", size_hint_y=None, height=dp(46)), "primary")
    content.add_widget(details)
    content.add_widget(close)
    popup = Popup(
        title="Something went wrong",
        title_color=RED,
        title_size="18sp",
        separator_color=RED,
        background_color=NAVY_800,
        content=content,
        size_hint=(None, None),
        width=min(Window.width * 0.86, dp(620)),
        height=min(Window.height * 0.72, dp(260)),
    )
    close.bind(on_release=lambda *_: popup.dismiss())
    popup.open()


def open_details_dialog(title: str, details: str) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
    paint_background(content, NAVY_800)
    value = style_input(
        TextInput(
            text=details,
            readonly=True,
            multiline=True,
        )
    )
    close = style_button(Button(text="Close", size_hint_y=None, height=dp(46)), "secondary")
    content.add_widget(value)
    content.add_widget(close)
    popup = Popup(
        title=title,
        title_color=PEARL_GREY,
        title_size="18sp",
        separator_color=GOLD,
        background_color=NAVY_800,
        content=content,
        size_hint=(None, None),
        width=min(Window.width * 0.92, dp(980)),
        height=min(Window.height * 0.9, dp(680)),
    )
    close.bind(on_release=lambda *_: popup.dismiss())
    popup.open()


def show_confirmation(message: str, duration: float = 1.6) -> None:
    content = Label(
        text=message,
        color=PEARL_GREY,
        font_size="15sp",
        halign="center",
        valign="middle",
    )
    content.bind(size=lambda widget, size: setattr(widget, "text_size", size))
    popup = Popup(
        title="Saved",
        title_color=PEARL_GREY,
        title_size="17sp",
        separator_color=GOLD,
        background_color=NAVY_800,
        overlay_color=(0, 0, 0, 0.2),
        content=content,
        size_hint=(None, None),
        width=min(Window.width * 0.8, dp(460)),
        height=min(Window.height * 0.5, dp(150)),
    )
    popup.open()
    popup._dismiss_event = Clock.schedule_once(popup.dismiss, duration)


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
    actions.add_widget(submit)
    actions.add_widget(cancel)
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


def open_file_dialog(on_submit: Callable[[str], None]) -> None:
    content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
    paint_background(content, NAVY_800)
    chooser = FileChooserListView(
        path=str(Path.home()),
        multiselect=False,
        dirselect=False,
    )
    actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
    cancel = style_button(Button(text="Cancel"), "secondary")
    select = style_button(Button(text="Use selected file"), "primary")
    actions.add_widget(cancel)
    actions.add_widget(select)
    content.add_widget(chooser)
    content.add_widget(actions)
    popup = Popup(
        title="Choose file link",
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
    select.bind(on_release=accept)
    popup.open()
