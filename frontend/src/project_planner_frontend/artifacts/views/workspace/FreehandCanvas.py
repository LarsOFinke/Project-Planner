from collections.abc import Callable
from uuid import uuid4

from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stencilview import StencilView

from project_planner.modules.artifacts.documents.WorkspaceDocument import WorkspaceDocument
from project_planner.modules.artifacts.documents.WorkspaceImage import WorkspaceImage
from project_planner.modules.artifacts.documents.WorkspaceShape import WorkspaceShape
from project_planner.modules.artifacts.documents.WorkspaceStroke import WorkspaceStroke
from project_planner.modules.artifacts.documents.WorkspaceText import WorkspaceText
from project_planner_frontend.artifacts.views.CanvasTransform import CanvasTransform
from project_planner_frontend.artifacts.views.EditorHistory import EditorHistory
from project_planner_frontend.artifacts.views.workspace.DraggableImage import DraggableImage
from project_planner_frontend.artifacts.views.workspace.ShapeWidget import ShapeWidget
from project_planner_frontend.artifacts.views.workspace.TextWidget import TextWidget
from project_planner_frontend.artifacts.views.workspace.WorkspaceMode import WorkspaceMode
from project_planner_frontend.shared.theme import NAVY_700, hex_color


class FreehandCanvas(StencilView, FloatLayout):
    DEFAULT_COLOR = "#D7DDE5"

    def __init__(
        self,
        on_change: Callable[[], None],
        on_selection_change: Callable[[str | None], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._on_change = on_change
        self._on_selection_change = on_selection_change or (lambda _kind: None)
        self._transform = CanvasTransform(density=dp(1))
        self._history: EditorHistory[WorkspaceDocument] = EditorHistory()
        self._strokes: list[tuple[list[float], str]] = []
        self._stroke_instructions: list[object] = []
        self._elements: dict[str, ShapeWidget | DraggableImage | TextWidget] = {}
        self._geometry: dict[str, tuple[float, float, float, float]] = {}
        self._selected_id: str | None = None
        self._current_color = self.DEFAULT_COLOR
        self._mode = WorkspaceMode.SELECT
        self.snap_enabled = False
        self._image_resolver: Callable[[str], str] | None = None
        with self.canvas.before:
            Color(*NAVY_700)
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_view, size=self._sync_view)

    def _sync_view(self, *_: object) -> None:
        self._transform.x, self._transform.y = self.pos
        self._background.pos, self._background.size = self.pos, self.size
        for element_id, element in self._elements.items():
            x, y, width, height = self._geometry[element_id]
            element.pos = self._transform.to_screen(x, y)
            element.size = width * self._transform.unit, height * self._transform.unit
        self._redraw_strokes()

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

    def _snap(self, value: float) -> float:
        return round(value / 20) * 20 if self.snap_enabled else value

    def _next_position(self, base: float) -> tuple[float, float]:
        offset = 18 * (len(self._elements) % 8)
        visible_x, visible_y = self._transform.to_world(self.x, self.y)
        return visible_x + base + offset, visible_y + base + offset

    def _register(
        self,
        element: ShapeWidget | DraggableImage | TextWidget,
        pos: tuple[float, float],
        size: tuple[float, float],
        notify: bool,
    ) -> str:
        if notify:
            self._remember()
        self._elements[element.element_id] = element
        self._geometry[element.element_id] = (*pos, *size)
        self.add_widget(element)
        self._sync_view()
        self._select(element.element_id)
        if notify:
            self._on_change()
        return element.element_id

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
        shape = ShapeWidget(
            resolved_id,
            kind,
            self._select,
            self._element_changed,
            on_edit_start=self._remember,
            rotation_degrees=rotation,
            color_hex=color or self._current_color,
        )
        return self._register(shape, pos or self._next_position(30), size or (130, 86), notify)

    def add_image(
        self,
        source: str,
        *,
        element_id: str | None = None,
        pos: tuple[float, float] | None = None,
        size: tuple[float, float] | None = None,
        rotation: float = 0,
        notify: bool = True,
        render_source: str | None = None,
    ) -> str:
        resolved_id = element_id or str(uuid4())
        image = DraggableImage(
            resolved_id,
            self._select,
            self._element_changed,
            source=source,
            on_edit_start=self._remember,
            render_source=render_source,
            rotation_degrees=rotation,
        )
        dimensions = size or (image.width / dp(1), image.height / dp(1))
        return self._register(image, pos or self._next_position(40), dimensions, notify)

    def add_text(
        self,
        text: str,
        *,
        element_id: str | None = None,
        pos: tuple[float, float] | None = None,
        size: tuple[float, float] | None = None,
        color: str | None = None,
        notify: bool = True,
    ) -> str:
        resolved_id = element_id or str(uuid4())
        widget = TextWidget(
            resolved_id,
            text,
            color or self._current_color,
            self._select,
            self._remember,
            self._element_changed,
        )
        return self._register(widget, pos or self._next_position(50), size or (180, 80), notify)

    def selected_text(self) -> str | None:
        element = self._elements.get(self._selected_id or "")
        return element.text if isinstance(element, TextWidget) else None

    def selected_geometry(self) -> tuple[float, float, float, float] | None:
        return self._geometry.get(self._selected_id or "")

    def set_selected_geometry(self, x: float, y: float, width: float, height: float) -> None:
        if self._selected_id is None or width <= 0 or height <= 0:
            return
        self._remember()
        self._geometry[self._selected_id] = x, y, width, height
        self._sync_view()
        self._on_change()

    def edit_selected_text(self, text: str) -> None:
        element = self._elements.get(self._selected_id or "")
        if isinstance(element, TextWidget) and text.strip() and element.text != text:
            self._remember()
            element.text = text
            self._on_change()

    def _remember(self) -> None:
        self._history.remember(self.to_document())

    def _element_changed(self) -> None:
        if self._selected_id in self._elements:
            element = self._elements[self._selected_id]
            x, y = self._transform.to_world(*element.pos)
            self._geometry[self._selected_id] = (
                self._snap(x),
                self._snap(y),
                element.width / self._transform.unit,
                element.height / self._transform.unit,
            )
            self._sync_view()
        self._on_change()

    def delete_selected(self) -> None:
        if self._selected_id is None:
            return
        self._remember()
        self.remove_widget(self._elements.pop(self._selected_id))
        self._geometry.pop(self._selected_id)
        self._selected_id = None
        self._on_selection_change(None)
        self._on_change()

    def rotate_selected(self, degrees: float) -> None:
        element = self._elements.get(self._selected_id or "")
        if isinstance(element, ShapeWidget | DraggableImage):
            self._remember()
            element.rotate_by(degrees)

    def scale_selected(self, factor: float) -> None:
        element = self._elements.get(self._selected_id or "")
        if element is None:
            return
        x, y, width, height = self._geometry[self._selected_id]
        if isinstance(element, DraggableImage):
            minimum = max(60 / width, 40 / height)
            maximum = min(600 / width, 450 / height)
        elif isinstance(element, TextWidget):
            minimum = max(80 / width, 40 / height)
            maximum = min(600 / width, 450 / height)
        else:
            minimum = max(40 / width, 32 / height)
            maximum = min(420 / width, 320 / height)
        factor = min(maximum, max(minimum, factor))
        if factor == 1:
            return
        self._remember()
        new_width, new_height = width * factor, height * factor
        self._geometry[self._selected_id] = (
            x + (width - new_width) / 2,
            y + (height - new_height) / 2,
            new_width,
            new_height,
        )
        self._sync_view()
        self._on_change()

    def set_color(self, color: str) -> None:
        hex_color(color)
        self._current_color = color.upper()
        element = self._elements.get(self._selected_id or "")
        if isinstance(element, ShapeWidget):
            self._remember()
            element.set_color(self._current_color)
        elif isinstance(element, TextWidget):
            self._remember()
            element.color_hex = self._current_color
            element.color = hex_color(self._current_color)
            self._on_change()

    def set_mode(self, mode: WorkspaceMode) -> None:
        self._mode = mode
        if mode is WorkspaceMode.DRAW:
            self._select_none()

    def _select(self, element_id: str) -> None:
        self._selected_id = element_id
        selected = self._elements[element_id]
        if isinstance(selected, ShapeWidget):
            kind = selected.kind
        elif isinstance(selected, TextWidget):
            kind = "text"
        else:
            kind = "image"
        self._on_selection_change(kind)
        for current_id, element in self._elements.items():
            element.set_selected(current_id == element_id)

    def _select_none(self) -> None:
        self._selected_id = None
        self._on_selection_change(None)
        for element in self._elements.values():
            element.set_selected(False)

    def on_touch_down(self, touch: object) -> bool:
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self._mode is WorkspaceMode.SELECT:
            if super().on_touch_down(touch):
                return True
            self._select_none()
            return True
        self._select_none()
        self._remember()
        points = list(self._transform.to_world(touch.x, touch.y))
        self._strokes.append((points, self._current_color))
        touch.ud["planner_points"] = points
        self._redraw_strokes()
        touch.ud["planner_line"] = self._stroke_instructions[-1]
        return True

    def on_touch_move(self, touch: object) -> bool:
        points = touch.ud.get("planner_points")
        if points is None:
            return super().on_touch_move(touch)
        points.extend(self._transform.to_world(touch.x, touch.y))
        screen: list[float] = []
        for index in range(0, len(points), 2):
            screen.extend(self._transform.to_screen(points[index], points[index + 1]))
        touch.ud["planner_line"].points = screen
        return True

    def on_touch_up(self, touch: object) -> bool:
        if "planner_points" in touch.ud:
            touch.ud.pop("planner_points")
            touch.ud.pop("planner_line", None)
            self._on_change()
            return True
        return super().on_touch_up(touch)

    def _redraw_strokes(self) -> None:
        for instruction in self._stroke_instructions:
            self.canvas.remove(instruction)
        self._stroke_instructions.clear()
        for points, color in self._strokes:
            screen: list[float] = []
            for index in range(0, len(points), 2):
                screen.extend(self._transform.to_screen(points[index], points[index + 1]))
            with self.canvas:
                color_instruction = Color(*hex_color(color))
                if len(screen) == 2:
                    line = Line(
                        circle=(screen[0], screen[1], max(1, self._transform.unit)), width=2
                    )
                else:
                    line = Line(points=screen, width=max(1, 2 * self._transform.zoom))
            self._stroke_instructions.extend((color_instruction, line))

    def clear_drawing(self, notify: bool = True) -> None:
        if notify and (self._strokes or self._elements):
            self._remember()
        self._strokes.clear()
        for instruction in self._stroke_instructions:
            self.canvas.remove(instruction)
        self._stroke_instructions.clear()
        self.clear_widgets()
        self._elements.clear()
        self._geometry.clear()
        self._selected_id = None
        self._on_selection_change(None)
        if notify:
            self._on_change()

    def load_document(
        self,
        document: WorkspaceDocument,
        image_resolver: Callable[[str], str] | None = None,
        reset_history: bool = True,
    ) -> None:
        self.clear_drawing(notify=False)
        if reset_history:
            self._history.reset()
        if image_resolver is not None:
            self._image_resolver = image_resolver
        legacy = document.version < 6
        unit = dp(1)
        for stroke in document.strokes:
            points = list(stroke.points)
            if legacy:
                points = [
                    (value - (self.x if index % 2 == 0 else self.y)) / unit
                    for index, value in enumerate(points)
                ]
            self._strokes.append((points, stroke.color))
        for shape in document.shapes:
            self.add_shape(
                shape.kind,
                element_id=shape.element_id,
                pos=(shape.x / unit, shape.y / unit) if legacy else (shape.x, shape.y),
                size=(shape.width / unit, shape.height / unit)
                if legacy
                else (shape.width, shape.height),
                rotation=shape.rotation,
                color=shape.color,
                notify=False,
            )
        for image in document.images:
            render_source = self._image_resolver(image.source) if self._image_resolver else None
            self.add_image(
                image.source,
                element_id=image.element_id,
                pos=(image.x / unit, image.y / unit) if legacy else (image.x, image.y),
                size=(image.width / unit, image.height / unit)
                if legacy
                else (image.width, image.height),
                rotation=image.rotation,
                notify=False,
                render_source=render_source,
            )
        for item in document.texts:
            self.add_text(
                item.text,
                element_id=item.element_id,
                pos=(item.x, item.y),
                size=(item.width, item.height),
                color=item.color,
                notify=False,
            )
        self._select_none()
        self._sync_view()

    def to_document(self) -> WorkspaceDocument:
        shapes: list[WorkspaceShape] = []
        images: list[WorkspaceImage] = []
        texts: list[WorkspaceText] = []
        for element_id, element in self._elements.items():
            x, y, width, height = self._geometry[element_id]
            if isinstance(element, ShapeWidget):
                shapes.append(
                    WorkspaceShape(
                        element_id,
                        element.kind,
                        x,
                        y,
                        width,
                        height,
                        element.rotation_degrees,
                        element.color_hex,
                    )
                )
            elif isinstance(element, DraggableImage):
                images.append(
                    WorkspaceImage(
                        element_id, element.source, x, y, width, height, element.rotation_degrees
                    )
                )
            else:
                texts.append(
                    WorkspaceText(element_id, element.text, x, y, width, height, element.color_hex)
                )
        return WorkspaceDocument(
            strokes=tuple(WorkspaceStroke(tuple(points), color) for points, color in self._strokes),
            shapes=tuple(shapes),
            images=tuple(images),
            texts=tuple(texts),
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
