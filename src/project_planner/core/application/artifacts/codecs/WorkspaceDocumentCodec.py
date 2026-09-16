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


class WorkspaceDocumentCodec:
    CURRENT_VERSION = 3
    SHAPE_KINDS = {"rectangle", "ellipse", "line", "arrow"}

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
            "strokes": [list(stroke) for stroke in document.strokes],
            "shapes": [self._element_data(shape, kind=shape.kind) for shape in document.shapes],
            "images": [self._element_data(image, source=image.source) for image in document.images],
        }

    def _decode_strokes(self, value: object) -> tuple[tuple[float, ...], ...]:
        if not isinstance(value, list):
            return ()
        strokes: list[tuple[float, ...]] = []
        for entry in value:
            if not isinstance(entry, list) or len(entry) < 4:
                continue
            try:
                strokes.append(tuple(float(point) for point in entry))
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
                shapes.append(
                    WorkspaceShape(
                        element_id=str(entry.get("id") or uuid4()),
                        kind=kind,
                        x=float(entry.get("x", 30)),
                        y=float(entry.get("y", 30)),
                        width=float(entry.get("width", 130)),
                        height=float(entry.get("height", 86)),
                        rotation=float(entry.get("rotation", 0)),
                    )
                )
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
                images.append(
                    WorkspaceImage(
                        element_id=str(entry.get("id") or uuid4()),
                        source=source,
                        x=float(entry.get("x", 40)),
                        y=float(entry.get("y", 40)),
                        width=float(entry.get("width", 180)),
                        height=float(entry.get("height", 120)),
                        rotation=float(entry.get("rotation", 0)),
                    )
                )
            except (TypeError, ValueError):
                continue
        return tuple(images)

    @staticmethod
    def _element_data(element: object, **specific: object) -> dict[str, object]:
        return {
            "id": element.element_id,
            "x": element.x,
            "y": element.y,
            "width": element.width,
            "height": element.height,
            "rotation": element.rotation,
            **specific,
        }

    def _version(self, value: object) -> int:
        try:
            version = int(value)
        except (TypeError, ValueError):
            version = 1
        if version > self.CURRENT_VERSION:
            raise ValueError(f"Unsupported workspace document version: {version}")
        return max(1, version)
