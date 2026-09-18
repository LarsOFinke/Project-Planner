from dataclasses import dataclass

from project_planner.modules.artifacts.documents.WorkspaceImage import (
    WorkspaceImage,
)
from project_planner.modules.artifacts.documents.WorkspaceShape import (
    WorkspaceShape,
)
from project_planner.modules.artifacts.documents.WorkspaceStroke import (
    WorkspaceStroke,
)


@dataclass(frozen=True, slots=True)
class WorkspaceDocument:
    strokes: tuple[WorkspaceStroke, ...] = ()
    shapes: tuple[WorkspaceShape, ...] = ()
    images: tuple[WorkspaceImage, ...] = ()
    version: int = 4
