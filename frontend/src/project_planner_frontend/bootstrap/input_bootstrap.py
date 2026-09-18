def configure_mouse_input() -> None:
    from kivy.config import Config

    Config.set("input", "mouse", "mouse,disable_multitouch")
