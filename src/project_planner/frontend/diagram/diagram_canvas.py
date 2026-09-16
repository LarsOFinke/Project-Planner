from collections.abc import Callable
from uuid import uuid4

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout

from project_planner.frontend.diagram.node_widget import NodeWidget
from project_planner.frontend.shared.theme import GOLD, NAVY_800, SLATE_200, SLATE_600


class DiagramCanvas(FloatLayout):
    def __init__(
        self, on_change: Callable[[], None], **kwargs: object
    ) -> None:
        super().__init__(**kwargs)
        self._on_change = on_change
        self._nodes: dict[str, NodeWidget] = {}
        self._edges: list[tuple[str, str]] = []
        self.selected_ids: list[str] = []
        with self.canvas.before:
            Color(*NAVY_800)
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_background, size=self._sync_background)

    def _sync_background(self, *_: object) -> None:
        self._background.pos = self.pos
        self._background.size = self.size
        self._redraw_edges()

    def add_node(
        self,
        label: str | None = None,
        pos: tuple[float, float] | None = None,
        node_id: str | None = None,
        notify: bool = True,
    ) -> str:
        resolved_id = node_id or str(uuid4())
        resolved_pos = pos or (self.x + dp(40), self.top - dp(110))
        node = NodeWidget(
            resolved_id,
            self._select,
            self._moved,
            text=label or f"Node {len(self._nodes) + 1}",
            pos=resolved_pos,
            background_normal="",
            background_color=SLATE_600,
            color=SLATE_200,
        )
        self._nodes[resolved_id] = node
        self.add_widget(node)
        if notify:
            self._on_change()
        return resolved_id

    def connect_selected(self) -> None:
        if len(self.selected_ids) != 2:
            return
        edge = (self.selected_ids[0], self.selected_ids[1])
        if edge not in self._edges and (edge[1], edge[0]) not in self._edges:
            self._edges.append(edge)
        self._clear_selection()
        self._redraw_edges()
        self._on_change()

    def delete_selected(self) -> None:
        selected = set(self.selected_ids)
        for node_id in selected:
            node = self._nodes.pop(node_id, None)
            if node is not None:
                self.remove_widget(node)
        self._edges = [
            edge for edge in self._edges if not selected.intersection(edge)
        ]
        self._clear_selection()
        self._redraw_edges()
        self._on_change()

    def rename_selected(self, label: str) -> None:
        if len(self.selected_ids) == 1:
            self._nodes[self.selected_ids[0]].text = label
            self._on_change()

    def clear_diagram(self, notify: bool = True) -> None:
        self.clear_widgets()
        self._nodes.clear()
        self._edges.clear()
        self.selected_ids.clear()
        self._redraw_edges()
        if notify:
            self._on_change()

    def load_data(self, data: object) -> None:
        self.clear_diagram(notify=False)
        if not isinstance(data, dict):
            return
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        if isinstance(nodes, list):
            for entry in nodes:
                if not isinstance(entry, dict):
                    continue
                self.add_node(
                    label=str(entry.get("label", "Node")),
                    pos=(float(entry.get("x", 40)), float(entry.get("y", 40))),
                    node_id=str(entry.get("id", uuid4())),
                    notify=False,
                )
        if isinstance(edges, list):
            for entry in edges:
                if (
                    isinstance(entry, list)
                    and len(entry) == 2
                    and all(str(item) in self._nodes for item in entry)
                ):
                    self._edges.append((str(entry[0]), str(entry[1])))
        self._redraw_edges()

    def to_data(self) -> dict[str, object]:
        return {
            "version": 1,
            "nodes": [
                {"id": node_id, "label": node.text, "x": node.x, "y": node.y}
                for node_id, node in self._nodes.items()
            ],
            "edges": [list(edge) for edge in self._edges],
        }

    def _select(self, node_id: str) -> None:
        if node_id in self.selected_ids:
            self.selected_ids.remove(node_id)
        else:
            self.selected_ids.append(node_id)
            self.selected_ids = self.selected_ids[-2:]
        for current_id, node in self._nodes.items():
            node.background_color = (
                GOLD
                if current_id in self.selected_ids
                else SLATE_600
            )

    def _clear_selection(self) -> None:
        self.selected_ids.clear()
        for node in self._nodes.values():
            node.background_color = SLATE_600

    def _moved(self) -> None:
        self._redraw_edges()
        self._on_change()

    def _redraw_edges(self) -> None:
        self.canvas.after.clear()
        with self.canvas.after:
            Color(*GOLD)
            for source_id, target_id in self._edges:
                source = self._nodes.get(source_id)
                target = self._nodes.get(target_id)
                if source is not None and target is not None:
                    Line(
                        points=[
                            source.center_x,
                            source.center_y,
                            target.center_x,
                            target.center_y,
                        ],
                        width=1.5,
                    )
