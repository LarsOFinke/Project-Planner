from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import uuid4

from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.shared.utils.clock import utc_now


@dataclass(frozen=True, slots=True)
class BacklogItem:
    project_id: str
    title: str
    position: int
    description: str = ""
    priority: BacklogPriority = BacklogPriority.MEDIUM
    status: BacklogStatus = BacklogStatus.BACKLOG
    assignee: str = ""
    section_id: str | None = None
    sprint_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Backlog item title must not be empty")
        if self.position < 0:
            raise ValueError("Backlog position must not be negative")

    def revise(self, **changes: object) -> BacklogItem:
        return replace(self, **changes, updated_at=utc_now())
