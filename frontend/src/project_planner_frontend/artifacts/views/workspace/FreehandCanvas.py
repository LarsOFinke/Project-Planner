from collections.abc import Callable
from uuid import uuid4

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView

from project_planner.modules.artifacts.documents.WorkspaceDocument import (
    WorkspaceDocument,
)
from project_planner.modules.artifacts.documents.WorkspaceImage import (
    WorkspaceImage,
)
from project_planner.modules.artifacts.documents.WorkspaceShape import (
    WorkspaceShape,
)
from project_planner.modules.artifacts.documents.WorkspaceStroke import (
    WorkspaceStroke,
)
from project_planner_frontend.artifacts.views.workspace.DraggableImage import DraggableImage
from project_planner_frontend.artifacts.views.workspace.ShapeWidget import ShapeWidget
from project_planner_frontend.artifacts.views.workspace.WorkspaceMode import WorkspaceMode
from project_planner_frontend.shared.theme import NAVY_700, hex_color


class FreehandCanvas(StencilView, FloatLayout):
    DEFAULT_COLOR = "#D7DDE5"

    def __init__(self, on_change: Callable[[], None], **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._on_change = on_change
        self._strokes: list[tuple[list[float], str]] = []
        self._stroke_instructions: list[object] = []
        self._elements: dict[str, ShapeWidget | DraggableImage] = {}
        self._selected_id: str | None = None
        self._current_color = self.DEFAULT_COLOR
        self._mode = WorkspaceMode.SELECT
        self._last_canvas_pos = self.pos
        with self.canvas.before:
            Color(*NAVY_700)
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_background, size=self._sync_background)

    def _sync_background(self, *_: object) -> None:
        delta_x = self.x - self._last_canvas_pos[0]
        delta_y = self.y - self._last_canvas_pos[1]
        if delta_x or delta_y:
            for element in self._elements.values():
                element.pos = element.x + delta_x, element.y + delta_y
            self._last_canvas_pos = self.pos
        self._background.pos = self.pos
        self._background.size = self.size

    def add_shape(
        self,
        kind: str,
        *,
        element_id: str | None = None,
        pos: tuple[float, float] | None = None,
        size: tuple[float, float] | None = None,
        rotation: float = 0,
        color: str | None = None,
        notify: bool = True,
    ) -> str:
        if kind not in {"rectangle", "ellipse", "line", "arrow"}:
            raise ValueError(f"Unknown shape template: {kind}")
        resolved_id = element_id or str(uuid4())
        default_position = self._next_position(30)
        shape = ShapeWidget(
            resolved_id,
            kind,
            self._select,
            self._on_change,
            rotation_degrees=rotation,
            color_hex=color or self._current_color,
            pos=pos or default_position,
        )
        if size is not None:
            shape.size = size
        self._elements[resolved_id] = shape
        self.add_widget(shape)
        self._select(resolved_id)
        if notify:
            self._on_change()
        return resolved_id

    def add_image(
        self,
        source: str,
        *,
        element_id: str | None = None,
        pos: tuple[float, float] | None = None,
        size: tuple[float, float] | None = None,
        rotation: float = 0,
        notify: bool = True,
    ) -> str:
        resolved_id = element_id or str(uuid4())
        default_position = self._next_position(40)
        image = DraggableImage(
            resolved_id,
            self._select,
            self._on_change,
            source=source,
            rotation_degrees=rotation,
            pos=pos or default_position,
        )
        if size is not None:
            image.size = size
        self._elements[resolved_id] = image
        self.add_widget(image)
        self._select(resolved_id)
        if notify:
            self._on_change()
        return resolved_id

    def _next_position(self, base: float) -> tuple[float, float]:
        offset = dp(18) * (len(self._elements) % 8)
        return self.x + dp(base) + offset, self.y + dp(base) + offset

    def delete_selected(self) -> None:
        if self._selected_id is None:
            return
        element = self._elements.pop(self._selected_id, None)
        if element is not None:
            self.remove_widget(element)
            self._selected_id = None
            self._on_change()

    def rotate_selected(self, degrees: float) -> None:
        if self._selected_id is not None:
            self._elements[self._selected_id].rotate_by(degrees)

    def scale_selected(self, factor: float) -> None:
        if self._selected_id is not None:
            self._elements[self._selected_id].scale_by(factor)

    def set_color(self, color: str) -> None:
        hex_color(color)
        self._current_color = color.upper()
        if self._selected_id is None:
            return
        selected = self._elements[self._selected_id]
        if isinstance(selected, ShapeWidget):
            selected.set_color(self._current_color)

    def set_mode(self, mode: WorkspaceMode) -> None:
        self._mode = mode
        if mode is WorkspaceMode.DRAW:
            self._select_none()

    def _select(self, element_id: str) -> None:
        self._selected_id = element_id
        for current_id, element in self._elements.items():
            element.set_selected(current_id == element_id)

    def on_touch_down(self, touch: object) -> bool:
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._mode is WorkspaceMode.SELECT:
            if super().on_touch_down(touch):
                return True
            self._select_none()
            return True
        self._select_none()
        points = [touch.x, touch.y]
        self._strokes.append((points, self._current_color))
        with self.canvas:
            color = Color(*hex_color(self._current_color))
            line = Line(points=points, width=2)
        self._stroke_instructions.extend((color, line))
        touch.ud["planner_line"] = line
        touch.ud["planner_points"] = points
        return True

    def on_touch_move(self, touch: object) -> bool:
        line = touch.ud.get("planner_line")
        points = touch.ud.get("planner_points")
        if line is None or points is None:
            return super().on_touch_move(touch)
        points.extend((touch.x, touch.y))
        line.points = points
        return True

    def on_touch_up(self, touch: object) -> bool:
        if "planner_line" in touch.ud:
            self._on_change()
            return True
        return super().on_touch_up(touch)

    def _select_none(self) -> None:
        self._selected_id = None
        for element in self._elements.values():
            element.set_selected(False)

    def clear_drawing(self, notify: bool = True) -> None:
        for instruction in self._stroke_instructions:
            self.canvas.remove(instruction)
        self._stroke_instructions.clear()
        self._strokes.clear()
        self.clear_widgets()
        self._elements.clear()
        self._selected_id = None
        if notify:
            self._on_change()

    def load_document(self, document: WorkspaceDocument) -> None:
        self.clear_drawing(notify=False)
        self._load_strokes(document.strokes)
        self._load_shapes(document.shapes)
        self._load_images(document.images)
        self._select_none()

    def _load_strokes(self, strokes: tuple[WorkspaceStroke, ...]) -> None:
        for stroke in strokes:
            points = list(stroke.points)
            self._strokes.append((points, stroke.color))
            with self.canvas:
                color = Color(*hex_color(stroke.color))
                line = Line(points=points, width=2)
            self._stroke_instructions.extend((color, line))

    def _load_shapes(self, shapes: tuple[WorkspaceShape, ...]) -> None:
        for shape in shapes:
            self.add_shape(
                shape.kind,
                element_id=shape.element_id,
                pos=(self.x + shape.x, self.y + shape.y),
                size=(shape.width, shape.height),
                rotation=shape.rotation,
                color=shape.color,
                notify=False,
            )

    def _load_images(self, images: tuple[WorkspaceImage, ...]) -> None:
        for image in images:
            self.add_image(
                image.source,
                element_id=image.element_id,
                pos=(self.x + image.x, self.y + image.y),
                size=(image.width, image.height),
                rotation=image.rotation,
                notify=False,
            )

    def to_document(self) -> WorkspaceDocument:
        shapes: list[WorkspaceShape] = []
        images: list[WorkspaceImage] = []
        for element_id, element in self._elements.items():
            if isinstance(element, ShapeWidget):
                shapes.append(
                    WorkspaceShape(
                        element_id,
                        element.kind,
                        element.x - self.x,
                        element.y - self.y,
                        element.width,
                        element.height,
                        element.rotation_degrees,
                        element.color_hex,
                    )
                )
            else:
                images.append(
                    WorkspaceImage(
                        element_id,
                        element.source,
                        element.x - self.x,
                        element.y - self.y,
                        element.width,
                        element.height,
                        element.rotation_degrees,
                    )
                )
        return WorkspaceDocument(
            strokes=tuple(WorkspaceStroke(tuple(points), color) for points, color in self._strokes),
            shapes=tuple(shapes),
            images=tuple(images),
        )
