from project_planner_frontend.artifacts.views.CanvasTransform import CanvasTransform
from project_planner_frontend.artifacts.views.EditorHistory import EditorHistory

from project_planner.modules.artifacts.documents.WorkspaceText import WorkspaceText
from project_planner.modules.artifacts.services.codecs.WorkspaceDocumentCodec import (
    WorkspaceDocumentCodec,
)


def test_transform_roundtrip_across_scale_zoom_and_pan() -> None:
    for density in (1, 2):
        transform = CanvasTransform(140, 70, density, 1.5, -32, 48)
        screen = transform.to_screen(123.5, -77.25)
        assert transform.to_world(*screen) == (123.5, -77.25)


def test_editor_history_discards_redo_after_new_change() -> None:
    history: EditorHistory[int] = EditorHistory()
    history.remember(1)
    history.remember(2)
    assert history.undo(3) == 2
    history.remember(9)
    assert history.redo(10) is None
    assert history.undo(10) == 9


def test_workspace_text_roundtrips_with_logical_coordinates() -> None:
    codec = WorkspaceDocumentCodec()
    raw = {
        "version": 6,
        "texts": [
            {
                "id": "note",
                "text": "Planning note",
                "x": 80,
                "y": 120,
                "width": 240,
                "height": 100,
                "color": "#D7DDE5",
            }
        ],
    }
    document = codec.decode(raw)
    assert document.texts == (WorkspaceText("note", "Planning note", 80, 120, 240, 100),)
    assert codec.decode(codec.encode(document)).texts == document.texts
