import os

from project_planner.frontend.bootstrap.CutbufferLogFilter import CutbufferLogFilter

_configured = False


def configure_clipboard() -> None:
    global _configured
    if _configured:
        return
    os.environ.setdefault("KIVY_CLIPBOARD", "sdl2")
    from kivy.logger import Logger

    Logger.addFilter(CutbufferLogFilter())
    _configured = True
