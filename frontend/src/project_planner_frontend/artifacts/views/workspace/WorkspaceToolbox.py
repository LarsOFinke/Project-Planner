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
        add_text: Callable[..., None],
        edit_text: Callable[..., None],
        edit_geometry: Callable[..., None],
        rotate: Callable[[float], None],
        scale: Callable[[float], None],
        zoom: Callable[[float], None],
        pan: Callable[[float, float], None],
        toggle_snap: Callable[..., None],
        undo: Callable[..., None],
        redo: Callable[..., None],
        set_color: Callable[[str], None],
        set_mode: Callable[[WorkspaceMode], None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        revisions: Callable[..., None] | None = None,
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
                "Quick edit": [
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
                    ("Size -", lambda *_: scale(0.85), "secondary"),
                    ("Size +", lambda *_: scale(1.15), "secondary"),
                    ("Rectangle", lambda *_: add_shape("rectangle"), "secondary"),
                    ("Add text", add_text, "secondary"),
                ],
                "Add to canvas": [
                    ("Rectangle", lambda *_: add_shape("rectangle"), "secondary"),
                    ("Ellipse", lambda *_: add_shape("ellipse"), "secondary"),
                    ("Line", lambda *_: add_shape("line"), "secondary"),
                    ("Arrow", lambda *_: add_shape("arrow"), "secondary"),
                    ("Add text", add_text, "secondary"),
                    ("Image", choose_image, "secondary"),
                ],
                "Object details": [
                    ("Geometry", edit_geometry, "primary"),
                    ("Edit text", edit_text, "secondary"),
                    ("Rotate -", lambda *_: rotate(-15), "secondary"),
                    ("Rotate +", lambda *_: rotate(15), "secondary"),
                    ("Delete", delete_selected, "danger"),
                ],
                "Colors": [
                    (
                        name,
                        lambda *_, color=value: self._choose_color(color),
                        "secondary",
                    )
                    for name, value in self._palette_colors.items()
                ],
                "Canvas view": [
                    ("Zoom -", lambda *_: zoom(0.8), "secondary"),
                    ("Zoom +", lambda *_: zoom(1.25), "secondary"),
                    ("Pan left", lambda *_: pan(-40, 0), "secondary"),
                    ("Pan right", lambda *_: pan(40, 0), "secondary"),
                    ("Pan up", lambda *_: pan(0, 40), "secondary"),
                    ("Pan down", lambda *_: pan(0, -40), "secondary"),
                    ("Snap grid", toggle_snap, "secondary"),
                ],
                "History & file": [
                    ("Undo", undo, "secondary"),
                    ("Redo", redo, "secondary"),
                    ("Save now", save, "primary"),
                    ("Restore version", revisions or (lambda *_: None), "secondary"),
                    ("Clear all", clear_all, "danger"),
                ],
            },
            **kwargs,
        )
        self._refresh_mode()
        self._refresh_colors()
        self.set_selection(None)
        self.button("History & file", "Restore version").disabled = revisions is None

    def set_selection(self, kind: str | None) -> None:
        self.set_group_label("Quick edit", f"Selected: {kind or 'none'}")
        for label in ("Size -", "Size +"):
            self.button("Quick edit", label).disabled = kind is None
        for label in ("Rotate -", "Rotate +"):
            self.button("Object details", label).disabled = kind is None or kind == "text"
        self.button("Object details", "Geometry").disabled = kind is None
        self.button("Object details", "Edit text").disabled = kind != "text"
        self.button("Object details", "Delete").disabled = kind is None

    def _refresh_mode(self) -> None:
        for mode in WorkspaceMode:
            button = self.button("Quick edit", mode.value.capitalize())
            style_button(button, "selected" if mode is self._selected_mode else "secondary")

    def _refresh_colors(self) -> None:
        for name, color in self._palette_colors.items():
            button = self.button("Colors", name)
            red, green, blue, _alpha = hex_color(color)
            opacity = 1.0 if color == self._selected_color else 0.62
            set_button_background(button, (red, green, blue, opacity))
            button.color = NAVY_950 if name in {"Pearl", "Gold"} else PEARL_GREY

    def _choose_color(self, color: str) -> None:
        self._selected_color = color
        self._set_color(color)
        self._refresh_colors()

    def _choose_mode(self, mode: WorkspaceMode) -> None:
        self._selected_mode = mode
        self._set_mode(mode)
        self._refresh_mode()
