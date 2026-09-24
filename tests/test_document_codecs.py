from pathlib import Path

import pytest

from project_planner.modules.artifacts.documents.WorkspaceDocument import (
    WorkspaceDocument,
)
from project_planner.modules.artifacts.documents.WorkspaceShape import (
    WorkspaceShape,
)
from project_planner.modules.artifacts.documents.WorkspaceStroke import (
    WorkspaceStroke,
)
from project_planner.modules.artifacts.services.codecs.DiagramDocumentCodec import (
    DiagramDocumentCodec,
)
from project_planner.modules.artifacts.services.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
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
                {"id": "infinite", "x": float("inf"), "y": 0},
            ],
            "edges": [
                ["one", "two"],
                ["two", "one"],
                ["one", "one"],
                ["one", "missing"],
            ],
        }
    )

    assert [node.node_id for node in document.nodes] == ["one", "two"]
    assert document.edges == (("one", "two"),)
    assert codec.encode(document)["version"] == 2
    assert codec.decode(codec.encode(document)).nodes[0].width == 150
    assert codec.decode(codec.encode(document)).nodes[0].height == 64
    with pytest.raises(ValueError, match="Unsupported diagram"):
        codec.decode({"version": 3})


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
    assert document.strokes[0].color == "#D7DDE5"
    assert len(document.shapes) == 1
    assert document.shapes[0].color == "#D7DDE5"
    assert [entry.element_id for entry in document.images] == ["kept"]
    assert codec.encode(document)["version"] == 6
    with pytest.raises(ValueError, match="Unsupported workspace"):
        codec.decode({"version": 7})


def test_workspace_codec_preserves_portable_managed_image_references() -> None:
    codec = WorkspaceDocumentCodec()

    document = codec.decode(
        {
            "version": 5,
            "images": [{"id": "managed", "source": "managed://images/image.png"}],
        }
    )

    assert document.images[0].source == "managed://images/image.png"
    assert codec.encode(document)["images"][0]["source"] == "managed://images/image.png"


def test_workspace_codec_round_trips_stroke_and_shape_colors() -> None:
    codec = WorkspaceDocumentCodec()
    document = WorkspaceDocument(
        strokes=(WorkspaceStroke((1, 2, 3, 4), "#C84B4B"),),
        shapes=(WorkspaceShape("shape", "ellipse", 10, 20, 100, 80, 15, "#4C78A8"),),
    )

    restored = codec.decode(codec.encode(document))

    assert restored.strokes[0].color == "#C84B4B"
    assert restored.shapes[0].color == "#4C78A8"


def test_workspace_codec_filters_unsafe_geometry() -> None:
    codec = WorkspaceDocumentCodec()
    document = codec.decode(
        {
            "version": 4,
            "strokes": [
                {"points": [1, 2, 3], "color": "#C84B4B"},
                {"points": [1, 2, float("nan"), 4], "color": "#C84B4B"},
            ],
            "shapes": [
                {
                    "id": "negative",
                    "kind": "rectangle",
                    "width": -10,
                    "height": 20,
                },
                {
                    "id": "infinite",
                    "kind": "ellipse",
                    "x": float("inf"),
                    "width": 20,
                    "height": 20,
                },
            ],
        }
    )

    assert document.strokes == ()
    assert document.shapes == ()
