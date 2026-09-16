from collections.abc import Callable

from project_planner.frontend.shared.CategorizedToolbox import CategorizedToolbox


class WorkspaceToolbox(CategorizedToolbox):
    def __init__(
        self,
        add_shape: Callable[[str], None],
        choose_image: Callable[..., None],
        rotate: Callable[[float], None],
        scale: Callable[[float], None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            groups={
                "Shapes": [
                    ("Rectangle", lambda *_: add_shape("rectangle"), "secondary"),
                    ("Ellipse", lambda *_: add_shape("ellipse"), "secondary"),
                    ("Line", lambda *_: add_shape("line"), "secondary"),
                    ("Arrow", lambda *_: add_shape("arrow"), "secondary"),
                ],
                "Media": [("Insert image", choose_image, "primary")],
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
            initial_group="Shapes",
            **kwargs,
        )
