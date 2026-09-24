from collections.abc import Callable
from uuid import uuid4

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView

from project_planner.modules.artifacts.documents.DiagramDocument import DiagramDocument
from project_planner.modules.artifacts.documents.DiagramNode import DiagramNode
from project_planner_frontend.artifacts.views.CanvasTransform import CanvasTransform
from project_planner_frontend.artifacts.views.diagram.NodeWidget import NodeWidget
from project_planner_frontend.artifacts.views.EditorHistory import EditorHistory
from project_planner_frontend.shared.theme import GOLD, NAVY_800, SLATE_200, SLATE_600


class DiagramCanvas(StencilView, FloatLayout):
    def __init__(
        self,
        on_change: Callable[[], None],
        on_selection_change: Callable[[int], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._on_change = on_change
        self._on_selection_change = on_selection_change or (lambda _count: None)
        self._transform = CanvasTransform(density=dp(1))
        self._history: EditorHistory[DiagramDocument] = EditorHistory()
        self._nodes: dict[str, NodeWidget] = {}
        self._positions: dict[str, tuple[float, float]] = {}
        self._sizes: dict[str, tuple[float, float]] = {}
        self._edges: list[tuple[str, str]] = []
        self._edge_instructions: list[object] = []
        self.selected_ids: list[str] = []
        self.snap_enabled = False
        with self.canvas.before:
            Color(*NAVY_800)
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_view, size=self._sync_view)

    def _sync_view(self, *_: object) -> None:
        self._transform.x, self._transform.y = self.pos
        self._background.pos, self._background.size = self.pos, self.size
        for node_id, node in self._nodes.items():
            node.pos = self._transform.to_screen(*self._positions[node_id])
            width, height = self._sizes[node_id]
            node.size = width * self._transform.unit, height * self._transform.unit
        self._redraw_edges()

    def zoom_by(self, factor: float) -> None:
        center = (self.center_x, self.center_y)
        world_center = self._transform.to_world(*center)
        self._transform.zoom = min(4.0, max(0.25, self._transform.zoom * factor))
        screen_center = self._transform.to_screen(*world_center)
        self._transform.pan_x += center[0] - screen_center[0]
        self._transform.pan_y += center[1] - screen_center[1]
        self._sync_view()

    def pan_by(self, dx: float, dy: float) -> None:
        self._transform.pan_x += dp(dx)
        self._transform.pan_y += dp(dy)
        self._sync_view()

    def toggle_snap(self) -> bool:
        self.snap_enabled = not self.snap_enabled
        return self.snap_enabled

    def add_node(
        self,
        label: str | None = None,
        pos: tuple[float, float] | None = None,
        node_id: str | None = None,
        size: tuple[float, float] = (150, 64),
        notify: bool = True,
    ) -> str:
        if notify:
            self._history.remember(self.to_document())
        resolved_id = node_id or str(uuid4())
        node = NodeWidget(
            resolved_id,
            self._select,
            self._moved,
            on_edit_start=lambda: self._history.remember(self.to_document()),
            text=label or f"Node {len(self._nodes) + 1}",
            background_normal="",
            background_color=SLATE_600,
            color=SLATE_200,
        )
        self._nodes[resolved_id] = node
        center_x, center_y = self._transform.to_world(self.center_x, self.center_y)
        offset = 20 * (len(self._nodes) % 8)
        self._positions[resolved_id] = pos or (center_x - 75 + offset, center_y - 32 + offset)
        self._sizes[resolved_id] = size
        self.add_widget(node)
        self._sync_view()
        if notify:
            self._clear_selection()
            self._select(resolved_id)
            self._on_change()
        return resolved_id

    def connect_selected(self) -> None:
        if len(self.selected_ids) != 2:
            return
        edge = tuple(self.selected_ids)
        if edge in self._edges or edge[::-1] in self._edges:
            return
        self._history.remember(self.to_document())
        self._edges.append(edge)
        self._clear_selection()
        self._redraw_edges()
        self._on_change()

    def delete_selected(self) -> None:
        if not self.selected_ids:
            return
        self._history.remember(self.to_document())
        selected = set(self.selected_ids)
        for node_id in selected:
            self.remove_widget(self._nodes.pop(node_id))
            self._positions.pop(node_id)
            self._sizes.pop(node_id)
        self._edges = [edge for edge in self._edges if not selected.intersection(edge)]
        self._clear_selection()
        self._redraw_edges()
        self._on_change()

    def rename_selected(self, label: str) -> None:
        if len(self.selected_ids) == 1 and label.strip():
            node = self._nodes[self.selected_ids[0]]
            if node.text != label:
                self._history.remember(self.to_document())
                node.text = label
                self._on_change()

    def clear_diagram(self, notify: bool = True) -> None:
        if notify and self._nodes:
            self._history.remember(self.to_document())
        self.clear_widgets()
        self._nodes.clear()
        self._positions.clear()
        self._sizes.clear()
        self._edges.clear()
        self.selected_ids.clear()
        self._on_selection_change(0)
        self._redraw_edges()
        if notify:
            self._on_change()

    def load_document(self, document: DiagramDocument, reset_history: bool = True) -> None:
        self.clear_diagram(notify=False)
        if reset_history:
            self._history.reset()
        for node in document.nodes:
            pos = (
                ((node.x - self.x) / dp(1), (node.y - self.y) / dp(1))
                if document.version < 2
                else (node.x, node.y)
            )
            self.add_node(
                node.label, pos, node.node_id, size=(node.width, node.height), notify=False
            )
        self._edges.extend(
            edge for edge in document.edges if all(item in self._nodes for item in edge)
        )
        self._sync_view()

    def to_document(self) -> DiagramDocument:
        return DiagramDocument(
            nodes=tuple(
                DiagramNode(node_id, node.text, *self._positions[node_id], *self._sizes[node_id])
                for node_id, node in self._nodes.items()
            ),
            edges=tuple(self._edges),
        )

    def undo(self) -> bool:
        previous = self._history.undo(self.to_document())
        if previous is None:
            return False
        self.load_document(previous, reset_history=False)
        self._on_change()
        return True

    def redo(self) -> bool:
        following = self._history.redo(self.to_document())
        if following is None:
            return False
        self.load_document(following, reset_history=False)
        self._on_change()
        return True

    def _select(self, node_id: str) -> None:
        if node_id in self.selected_ids:
            self.selected_ids.remove(node_id)
        else:
            self.selected_ids.append(node_id)
            self.selected_ids = self.selected_ids[-2:]
        for current_id, node in self._nodes.items():
            node.background_color = GOLD if current_id in self.selected_ids else SLATE_600
        self._on_selection_change(len(self.selected_ids))

    def selected_geometry(self) -> tuple[float, float, float, float] | None:
        if len(self.selected_ids) != 1:
            return None
        node_id = self.selected_ids[0]
        return (*self._positions[node_id], *self._sizes[node_id])

    def set_selected_geometry(self, x: float, y: float, width: float, height: float) -> None:
        if len(self.selected_ids) != 1 or width <= 0 or height <= 0:
            return
        self._history.remember(self.to_document())
        node_id = self.selected_ids[0]
        self._positions[node_id] = x, y
        self._sizes[node_id] = width, height
        self._sync_view()
        self._on_change()

    def _clear_selection(self) -> None:
        self.selected_ids.clear()
        self._on_selection_change(0)
        for node in self._nodes.values():
            node.background_color = SLATE_600

    def _moved(self, node_id: str) -> None:
        node = self._nodes[node_id]
        x, y = self._transform.to_world(*node.pos)
        if self.snap_enabled:
            x, y = round(x / 20) * 20, round(y / 20) * 20
        self._positions[node_id] = x, y
        self._sync_view()
        self._on_change()

    @staticmethod
    def _edge_anchor(node: NodeWidget, target: NodeWidget) -> tuple[float, float]:
        dx = target.center_x - node.center_x
        dy = target.center_y - node.center_y
        scale = max(abs(dx) / max(node.width / 2, 1), abs(dy) / max(node.height / 2, 1), 1)
        return node.center_x + dx / scale, node.center_y + dy / scale

    def _redraw_edges(self) -> None:
        for instruction in self._edge_instructions:
            self.canvas.after.remove(instruction)
        self._edge_instructions.clear()
        with self.canvas.after:
            self._edge_instructions.append(Color(*GOLD))
            for source_id, target_id in self._edges:
                source, target = self._nodes.get(source_id), self._nodes.get(target_id)
                if source is not None and target is not None:
                    start = self._edge_anchor(source, target)
                    end = self._edge_anchor(target, source)
                    self._edge_instructions.append(Line(points=(*start, *end), width=1.5))
