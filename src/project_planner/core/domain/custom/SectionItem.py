from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.core.domain.custom.SectionStatus import SectionStatus
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class SectionItem:
    section_id: str
    title: str
    position: int
    description: str = ""
    assignee: str = ""
    status: SectionStatus = SectionStatus.NOT_STARTED
    item_date: date | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Section item title must not be empty")
        if self.position < 0:
            raise ValueError("Section item position must not be negative")

    def revise(self, **changes: object) -> SectionItem:
        return replace(self, **changes, updated_at=utc_now())
