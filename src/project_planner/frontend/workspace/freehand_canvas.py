from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView

from project_planner.frontend.shared.theme import NAVY_700, SLATE_200
from project_planner.frontend.workspace.draggable_image import DraggableImage
from project_planner.frontend.workspace.shape_widget import ShapeWidget


class FreehandCanvas(StencilView, FloatLayout):
    def __init__(
        self, on_change: Callable[[], None], **kwargs: object
    ) -> None:
        super().__init__(**kwargs)
        self._on_change = on_change
        self._strokes: list[list[float]] = []
        self._stroke_instructions: list[object] = []
        self._elements: dict[str, ShapeWidget | DraggableImage] = {}
        self._selected_id: str | None = None
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

    def _select(self, element_id: str) -> None:
        self._selected_id = element_id
        for current_id, element in self._elements.items():
            element.set_selected(current_id == element_id)

    def on_touch_down(self, touch: object) -> bool:
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if super().on_touch_down(touch):
            return True
        self._select_none()
        points = [touch.x, touch.y]
        self._strokes.append(points)
        with self.canvas:
            color = Color(*SLATE_200)
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

    def load_data(self, data: object) -> None:
        self.clear_drawing(notify=False)
        if not isinstance(data, dict):
            return
        self._load_strokes(data.get("strokes", []))
        self._load_shapes(data.get("shapes", []))
        self._load_images(data.get("images", []))
        self._select_none()

    def _load_strokes(self, strokes: object) -> None:
        if not isinstance(strokes, list):
            return
        for raw_stroke in strokes:
            if not isinstance(raw_stroke, list) or len(raw_stroke) < 4:
                continue
            points = [float(value) for value in raw_stroke]
            self._strokes.append(points)
            with self.canvas:
                color = Color(*SLATE_200)
                line = Line(points=points, width=2)
            self._stroke_instructions.extend((color, line))

    def _load_shapes(self, shapes: object) -> None:
        if not isinstance(shapes, list):
            return
        for entry in shapes:
            if not isinstance(entry, dict):
                continue
            self.add_shape(
                str(entry.get("kind", "rectangle")),
                element_id=str(entry.get("id", uuid4())),
                pos=self._entry_position(entry, 30),
                size=self._entry_size(entry, 130, 86),
                rotation=float(entry.get("rotation", 0)),
                notify=False,
            )

    def _load_images(self, images: object) -> None:
        if not isinstance(images, list):
            return
        for entry in images:
            if not isinstance(entry, dict):
                continue
            source = str(entry.get("source", ""))
            if not Path(source).is_file():
                continue
            self.add_image(
                source,
                element_id=str(entry.get("id", uuid4())),
                pos=self._entry_position(entry, 40),
                size=self._entry_size(entry, 180, 120),
                rotation=float(entry.get("rotation", 0)),
                notify=False,
            )

    def _entry_position(
        self, entry: dict[object, object], fallback: float
    ) -> tuple[float, float]:
        return (
            self.x + float(entry.get("x", dp(fallback))),
            self.y + float(entry.get("y", dp(fallback))),
        )

    @staticmethod
    def _entry_size(
        entry: dict[object, object], width: float, height: float
    ) -> tuple[float, float]:
        return (
            float(entry.get("width", dp(width))),
            float(entry.get("height", dp(height))),
        )

    def to_data(self) -> dict[str, object]:
        shapes: list[dict[str, object]] = []
        images: list[dict[str, object]] = []
        for element_id, element in self._elements.items():
            common = {
                "id": element_id,
                "x": element.x - self.x,
                "y": element.y - self.y,
                "width": element.width,
                "height": element.height,
                "rotation": element.rotation_degrees,
            }
            if isinstance(element, ShapeWidget):
                shapes.append({**common, "kind": element.kind})
            else:
                images.append({**common, "source": element.source})
        return {
            "version": 3,
            "strokes": self._strokes,
            "shapes": shapes,
            "images": images,
        }
