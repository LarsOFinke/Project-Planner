from collections.abc import Callable

from project_planner_frontend.artifacts.views.workspace.WorkspaceMode import WorkspaceMode
from project_planner_frontend.shared.CategorizedToolbox import CategorizedToolbox
from project_planner_frontend.shared.theme import (
    NAVY_950,
    PEARL_GREY,
    hex_color,
    set_button_background,
    style_button,
)


class WorkspaceToolbox(CategorizedToolbox):
    def __init__(
        self,
        add_shape: Callable[[str], None],
        choose_image: Callable[..., None],
        rotate: Callable[[float], None],
        scale: Callable[[float], None],
        set_color: Callable[[str], None],
        set_mode: Callable[[WorkspaceMode], None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        **kwargs: object,
    ) -> None:
        self._set_color = set_color
        self._set_mode = set_mode
        self._selected_color = "#D7DDE5"
        self._selected_mode = WorkspaceMode.SELECT
        self._palette_colors = {
            "Pearl": "#D7DDE5",
            "Gold": "#C9A55C",
            "Red": "#CE6A6A",
            "Blue": "#648DB8",
            "Green": "#69A987",
        }
        super().__init__(
            groups={
                "Mode": [
                    (
                        "Select",
                        lambda *_: self._choose_mode(WorkspaceMode.SELECT),
                        "secondary",
                    ),
                    (
                        "Draw",
                        lambda *_: self._choose_mode(WorkspaceMode.DRAW),
                        "secondary",
                    ),
                ],
                "Shapes": [
                    ("Rectangle", lambda *_: add_shape("rectangle"), "secondary"),
                    ("Ellipse", lambda *_: add_shape("ellipse"), "secondary"),
                    ("Line", lambda *_: add_shape("line"), "secondary"),
                    ("Arrow", lambda *_: add_shape("arrow"), "secondary"),
                ],
                "Media": [("Insert image", choose_image, "primary")],
                "Colors": [
                    (
                        name,
                        lambda *_, color=value: self._choose_color(color),
                        "secondary",
                    )
                    for name, value in self._palette_colors.items()
                ],
                "Transform": [
                    ("Rotate left", lambda *_: rotate(-15), "secondary"),
                    ("Rotate right", lambda *_: rotate(15), "secondary"),
                    ("Scale down", lambda *_: scale(0.85), "secondary"),
                    ("Scale up", lambda *_: scale(1.15), "secondary"),
                ],
                "Manage": [
                    ("Delete selected", delete_selected, "danger"),
                    ("Clear all", clear_all, "danger"),
                    ("Save now", save, "primary"),
                ],
            },
            initial_group="Mode",
            **kwargs,
        )

    def show_group(self, name: str, *_: object) -> None:
        super().show_group(name)
        if name == "Mode":
            for button in self._actions.children:
                mode = WorkspaceMode(button.text.lower())
                style_button(
                    button,
                    "selected" if mode is self._selected_mode else "secondary",
                )
            return
        if name != "Colors":
            return
        for button in self._actions.children:
            color = self._palette_colors[button.text]
            red, green, blue, _alpha = hex_color(color)
            opacity = 1.0 if color == self._selected_color else 0.62
            set_button_background(button, (red, green, blue, opacity))
            button.color = NAVY_950 if button.text in {"Pearl", "Gold"} else PEARL_GREY

    def _choose_color(self, color: str) -> None:
        self._selected_color = color
        self._set_color(color)
        self.show_group("Colors")

    def _choose_mode(self, mode: WorkspaceMode) -> None:
        self._selected_mode = mode
        self._set_mode(mode)
        self.show_group("Mode")
