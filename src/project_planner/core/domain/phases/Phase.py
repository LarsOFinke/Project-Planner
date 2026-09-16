from __future__ import annotations

from dataclasses import dataclass, field, replace
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Phase:
    project_id: str
    name: str
    position: int
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Phase name must not be empty")
        if self.position < 0:
            raise ValueError("Phase position must not be negative")

    def revise(self, **changes: object) -> Phase:
        return replace(self, **changes)
