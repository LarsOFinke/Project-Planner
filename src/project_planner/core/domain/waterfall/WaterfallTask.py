from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.core.domain.shared.clock import utc_now
from project_planner.core.domain.waterfall.WaterfallTaskStatus import WaterfallTaskStatus


@dataclass(frozen=True, slots=True)
class WaterfallTask:
    phase_id: str
    title: str
    position: int
    description: str = ""
    assignee: str = ""
    start_date: date | None = None
    due_date: date | None = None
    status: WaterfallTaskStatus = WaterfallTaskStatus.NOT_STARTED
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Task title must not be empty")
        if self.position < 0:
            raise ValueError("Task position must not be negative")
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("Task due date must not be before its start date")

    def revise(self, **changes: object) -> WaterfallTask:
        return replace(self, **changes, updated_at=utc_now())
