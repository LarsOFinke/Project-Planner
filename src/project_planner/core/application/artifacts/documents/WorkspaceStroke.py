from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceStroke:
    points: tuple[float, ...]
    color: str = "#D5DAE2"
