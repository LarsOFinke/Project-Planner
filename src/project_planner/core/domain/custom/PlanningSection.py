from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.core.domain.custom.SectionStatus import SectionStatus
from project_planner.core.domain.custom.SectionType import SectionType
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class PlanningSection:
    project_id: str
    name: str
    section_type: SectionType
    position: int
    description: str = ""
    start_date: date | None = None
    end_date: date | None = None
    status: SectionStatus = SectionStatus.NOT_STARTED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Section name must not be empty")
        if self.position < 0:
            raise ValueError("Section position must not be negative")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Section end date must not be before its start date")

    def revise(self, **changes: object) -> PlanningSection:
        return replace(self, **changes, updated_at=utc_now())
