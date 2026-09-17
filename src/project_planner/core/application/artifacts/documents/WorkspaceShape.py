from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceShape:
    element_id: str
    kind: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0.0
    color: str = "#D7DDE5"
