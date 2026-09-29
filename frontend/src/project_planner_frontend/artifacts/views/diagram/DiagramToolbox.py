from collections.abc import Callable

from project_planner_frontend.shared.CategorizedToolbox import CategorizedToolbox


class DiagramToolbox(CategorizedToolbox):
    def __init__(
        self,
        add_node: Callable[..., None],
        rename_node: Callable[..., None],
        edit_geometry: Callable[..., None],
        connect_selected: Callable[..., None],
        zoom: Callable[[float], None],
        pan: Callable[[float, float], None],
        toggle_snap: Callable[..., None],
        undo: Callable[..., None],
        redo: Callable[..., None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        revisions: Callable[..., None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            groups={
                "Quick edit": [
                    ("+ Node", add_node, "primary"),
                    ("Connect", connect_selected, "secondary"),
                    ("Geometry", edit_geometry, "secondary"),
                    ("Rename", rename_node, "secondary"),
                ],
                "Selection": [
                    ("Delete", delete_selected, "danger"),
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
        self.set_selection(0)
        self.button("History & file", "Restore version").disabled = revisions is None

    def set_selection(self, count: int) -> None:
        label = "none" if count == 0 else f"{count} node{'s' if count != 1 else ''}"
        self.set_group_label("Quick edit", f"Selected: {label}")
        self.button("Quick edit", "Connect").disabled = count != 2
        self.button("Quick edit", "Geometry").disabled = count != 1
        self.button("Quick edit", "Rename").disabled = count != 1
        self.button("Selection", "Delete").disabled = count == 0
