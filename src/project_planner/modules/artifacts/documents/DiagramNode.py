from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagramNode:
    node_id: str
    label: str
    x: float
    y: float
    width: float = 150.0
    height: float = 64.0
