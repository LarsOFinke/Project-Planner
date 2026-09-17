from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from uuid import uuid4

from project_planner.core.domain.projects.PlanningMethod import PlanningMethod
from project_planner.core.domain.projects.ProjectStatus import ProjectStatus
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class Project:
    title: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.IDEA
    planning_method: PlanningMethod = PlanningMethod.CUSTOM
    parent_id: str | None = None
    start_date: date | None = None
    target_date: date | None = None
    owner: str = ""
    assignee: str = ""
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Project title must not be empty")
        if self.parent_id == self.id:
            raise ValueError("A project cannot be its own parent")
        if self.start_date and self.target_date and self.target_date < self.start_date:
            raise ValueError("Target date must not be before start date")

    def revise(self, **changes: object) -> Project:
        return replace(self, **changes, updated_at=utc_now())
