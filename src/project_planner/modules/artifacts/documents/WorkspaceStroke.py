from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkspaceStroke:
    points: tuple[float, ...]
    color: str = "#D7DDE5"
