from collections.abc import Callable

from project_planner.frontend.shared.CategorizedToolbox import CategorizedToolbox


class DiagramToolbox(CategorizedToolbox):
    def __init__(
        self,
        add_node: Callable[..., None],
        rename_node: Callable[..., None],
        connect_selected: Callable[..., None],
        delete_selected: Callable[..., None],
        clear_all: Callable[..., None],
        save: Callable[..., None],
        **kwargs: object,
    ) -> None:
        super().__init__(
            groups={
                "Nodes": [
                    ("+ Node", add_node, "primary"),
                    ("Rename selected", rename_node, "secondary"),
                ],
                "Relations": [
                    ("Connect selected", connect_selected, "secondary"),
                ],
                "Manage": [
                    ("Delete selected", delete_selected, "danger"),
                    ("Clear all", clear_all, "danger"),
                    ("Save now", save, "primary"),
                ],
            },
            initial_group="Nodes",
            **kwargs,
        )
