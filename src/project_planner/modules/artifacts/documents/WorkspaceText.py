from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceText:
    element_id: str
    text: str
    x: float
    y: float
    width: float = 180.0
    height: float = 80.0
    color: str = "#D7DDE5"
