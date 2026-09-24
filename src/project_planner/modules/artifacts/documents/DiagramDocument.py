from dataclasses import dataclass

from project_planner.modules.artifacts.documents.DiagramNode import DiagramNode


@dataclass(frozen=True, slots=True)
class DiagramDocument:
    nodes: tuple[DiagramNode, ...] = ()
    edges: tuple[tuple[str, str], ...] = ()
    version: int = 2
