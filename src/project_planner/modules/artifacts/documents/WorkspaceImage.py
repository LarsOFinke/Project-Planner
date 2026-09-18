from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceImage:
    element_id: str
    source: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
