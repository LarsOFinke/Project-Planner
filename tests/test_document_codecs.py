from pathlib import Path

import pytest

from project_planner.core.application.artifacts.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.core.application.artifacts.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)
from project_planner.core.application.artifacts.documents.WorkspaceDocument import (
    WorkspaceDocument,
)
from project_planner.core.application.artifacts.documents.WorkspaceShape import (
    WorkspaceShape,
)
from project_planner.core.application.artifacts.documents.WorkspaceStroke import (
    WorkspaceStroke,
)


def test_diagram_codec_validates_nodes_edges_and_future_versions() -> None:
    codec = DiagramDocumentCodec()
    document = codec.decode(
        {
            "version": 1,
            "nodes": [
                {"id": "one", "label": "One", "x": 10, "y": 20},
                {"id": "two", "label": "Two", "x": 30, "y": 40},
                {"id": "broken", "x": "not-a-number"},
            ],
            "edges": [["one", "two"], ["one", "missing"]],
        }
    )

    assert [node.node_id for node in document.nodes] == ["one", "two"]
    assert document.edges == (("one", "two"),)
    assert codec.encode(document)["version"] == 1
    with pytest.raises(ValueError, match="Unsupported diagram"):
        codec.decode({"version": 2})


def test_workspace_codec_migrates_legacy_data_and_filters_missing_images(
    tmp_path: Path,
) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    codec = WorkspaceDocumentCodec()
    document = codec.decode(
        {
            "strokes": [[1, 2, 3, 4]],
            "shapes": [
                {
                    "id": "shape",
                    "kind": "rectangle",
                    "x": 10,
                    "y": 20,
                    "width": 100,
                    "height": 80,
                }
            ],
            "images": [
                {"id": "kept", "source": str(image)},
                {"id": "missing", "source": str(tmp_path / "missing.png")},
            ],
        }
    )

    assert document.version == 1
    assert document.strokes[0].points == (1.0, 2.0, 3.0, 4.0)
    assert document.strokes[0].color == "#D5DAE2"
    assert len(document.shapes) == 1
    assert document.shapes[0].color == "#D5DAE2"
    assert [entry.element_id for entry in document.images] == ["kept"]
    assert codec.encode(document)["version"] == 4
    with pytest.raises(ValueError, match="Unsupported workspace"):
        codec.decode({"version": 5})


def test_workspace_codec_round_trips_stroke_and_shape_colors() -> None:
    codec = WorkspaceDocumentCodec()
    document = WorkspaceDocument(
        strokes=(WorkspaceStroke((1, 2, 3, 4), "#C84B4B"),),
        shapes=(
            WorkspaceShape("shape", "ellipse", 10, 20, 100, 80, 15, "#4C78A8"),
        ),
    )

    restored = codec.decode(codec.encode(document))

    assert restored.strokes[0].color == "#C84B4B"
    assert restored.shapes[0].color == "#4C78A8"
