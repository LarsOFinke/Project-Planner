from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.core.domain.agile.SprintStatus import SprintStatus
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class Sprint:
    project_id: str
    name: str
    start_date: date
    end_date: date
    goal: str = ""
    status: SprintStatus = SprintStatus.PLANNED
    section_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Sprint name must not be empty")
        if self.end_date < self.start_date:
            raise ValueError("Sprint end date must not be before its start date")

    def revise(self, **changes: object) -> Sprint:
        return replace(self, **changes, updated_at=utc_now())
