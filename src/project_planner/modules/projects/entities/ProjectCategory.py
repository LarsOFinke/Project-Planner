from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import uuid4

from project_planner.shared.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class ProjectCategory:
    name: str
    position: int
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Category name must not be empty")
        if self.position < 0:
            raise ValueError("Category position must not be negative")

    def revise(self, **changes: object) -> ProjectCategory:
        return replace(self, **changes, updated_at=utc_now())
