from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import uuid4

from project_planner.core.domain.phases.PhaseStatus import PhaseStatus
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class Phase:
    project_id: str
    name: str
    position: int
    description: str = ""
    status: PhaseStatus = PhaseStatus.PLANNED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Phase name must not be empty")
        if self.position < 0:
            raise ValueError("Phase position must not be negative")

    def revise(self, **changes: object) -> Phase:
        return replace(self, **changes, updated_at=utc_now())
