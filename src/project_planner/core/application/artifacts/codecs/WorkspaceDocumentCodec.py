from math import isfinite
from pathlib import Path
from uuid import uuid4

from project_planner.core.application.artifacts.documents.WorkspaceDocument import (
    WorkspaceDocument,
)
from project_planner.core.application.artifacts.documents.WorkspaceImage import (
    WorkspaceImage,
)
from project_planner.core.application.artifacts.documents.WorkspaceShape import (
    WorkspaceShape,
)
from project_planner.core.application.artifacts.documents.WorkspaceStroke import (
    WorkspaceStroke,
)


class WorkspaceDocumentCodec:
    CURRENT_VERSION = 4
    SHAPE_KINDS = {"rectangle", "ellipse", "line", "arrow"}
    DEFAULT_COLOR = "#D5DAE2"

    def decode(self, data: object) -> WorkspaceDocument:
        if not isinstance(data, dict):
            return WorkspaceDocument()
        version = self._version(data.get("version", 1))
        return WorkspaceDocument(
            strokes=self._decode_strokes(data.get("strokes", [])),
            shapes=self._decode_shapes(data.get("shapes", [])),
            images=self._decode_images(data.get("images", [])),
            version=version,
        )

    def encode(self, document: WorkspaceDocument) -> dict[str, object]:
        return {
            "version": self.CURRENT_VERSION,
            "strokes": [
                {"points": list(stroke.points), "color": stroke.color}
                for stroke in document.strokes
            ],
            "shapes": [self._element_data(shape, kind=shape.kind) for shape in document.shapes],
            "images": [self._element_data(image, source=image.source) for image in document.images],
        }

    def _decode_strokes(self, value: object) -> tuple[WorkspaceStroke, ...]:
        if not isinstance(value, list):
            return ()
        strokes: list[WorkspaceStroke] = []
        for entry in value:
            points = entry.get("points") if isinstance(entry, dict) else entry
            if not isinstance(points, list) or len(points) < 4 or len(points) % 2 != 0:
                continue
            try:
                parsed_points = tuple(self._finite_float(point) for point in points)
                strokes.append(
                    WorkspaceStroke(
                        parsed_points,
                        self._color(entry.get("color") if isinstance(entry, dict) else None),
                    )
                )
            except (TypeError, ValueError):
                continue
        return tuple(strokes)

    def _decode_shapes(self, value: object) -> tuple[WorkspaceShape, ...]:
        if not isinstance(value, list):
            return ()
        shapes: list[WorkspaceShape] = []
        for entry in value:
            if not isinstance(entry, dict):
                continue
            kind = str(entry.get("kind", "rectangle"))
            if kind not in self.SHAPE_KINDS:
                continue
            try:
                width = self._positive_float(entry.get("width", 130))
                height = self._positive_float(entry.get("height", 86))
                shape = WorkspaceShape(
                    element_id=str(entry.get("id") or uuid4()),
                    kind=kind,
                    x=self._finite_float(entry.get("x", 30)),
                    y=self._finite_float(entry.get("y", 30)),
                    width=width,
                    height=height,
                    rotation=self._finite_float(entry.get("rotation", 0)),
                    color=self._color(entry.get("color")),
                )
                shapes.append(shape)
            except (TypeError, ValueError):
                continue
        return tuple(shapes)

    def _decode_images(self, value: object) -> tuple[WorkspaceImage, ...]:
        if not isinstance(value, list):
            return ()
        images: list[WorkspaceImage] = []
        for entry in value:
            if not isinstance(entry, dict):
                continue
            source = str(entry.get("source", ""))
            if not Path(source).is_file():
                continue
            try:
                image = WorkspaceImage(
                    element_id=str(entry.get("id") or uuid4()),
                    source=source,
                    x=self._finite_float(entry.get("x", 40)),
                    y=self._finite_float(entry.get("y", 40)),
                    width=self._positive_float(entry.get("width", 180)),
                    height=self._positive_float(entry.get("height", 120)),
                    rotation=self._finite_float(entry.get("rotation", 0)),
                )
                images.append(image)
            except (TypeError, ValueError):
                continue
        return tuple(images)

    @staticmethod
    def _element_data(element: object, **specific: object) -> dict[str, object]:
        data = {
            "id": element.element_id,
            "x": element.x,
            "y": element.y,
            "width": element.width,
            "height": element.height,
            "rotation": element.rotation,
            **specific,
        }
        color = getattr(element, "color", None)
        if color is not None:
            data["color"] = color
        return data

    def _color(self, value: object) -> str:
        color = str(value or self.DEFAULT_COLOR).upper()
        if len(color) != 7 or color[0] != "#":
            return self.DEFAULT_COLOR
        try:
            int(color[1:], 16)
        except ValueError:
            return self.DEFAULT_COLOR
        return color

    @staticmethod
    def _finite_float(value: object) -> float:
        parsed = float(value)
        if not isfinite(parsed):
            raise ValueError("A workspace coordinate must be finite")
        return parsed

    def _positive_float(self, value: object) -> float:
        parsed = self._finite_float(value)
        if parsed <= 0:
            raise ValueError("A workspace size must be positive")
        return parsed

    def _version(self, value: object) -> int:
        try:
            version = int(value)
        except (TypeError, ValueError):
            version = 1
        if version > self.CURRENT_VERSION:
            raise ValueError(f"Unsupported workspace document version: {version}")
        return max(1, version)
