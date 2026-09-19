from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.shared.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class Phase:
    project_id: str
    name: str
    position: int
    description: str = ""
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    start_date: date | None = None
    end_date: date | None = None
    section_id: str | None = None
    parallel_group: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Phase name must not be empty")
        if self.position < 0:
            raise ValueError("Phase position must not be negative")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Phase end date must not be before its start date")
        if self.parallel_group is not None:
            if not self.parallel_group.strip():
                raise ValueError("Phase parallel group must not be blank")
            if len(self.parallel_group) > 80:
                raise ValueError("Phase parallel group must be 80 characters or fewer")

    def revise(self, **changes: object) -> Phase:
        return replace(self, **changes, updated_at=utc_now())
