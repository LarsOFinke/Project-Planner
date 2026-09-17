from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import uuid4

from project_planner.core.domain.shared.clock import utc_now
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.core.domain.todos.TodoStatus import TodoStatus


@dataclass(frozen=True, slots=True)
class Todo:
    project_id: str
    title: str
    description: str = ""
    module: TodoModule = TodoModule.GENERAL
    status: TodoStatus = TodoStatus.OPEN
    phase_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("To-do title must not be empty")
        if self.phase_id is not None and self.module is not TodoModule.PHASES:
            raise ValueError("Only phase To-Dos can reference a phase")

    def revise(self, **changes: object) -> Todo:
        return replace(self, **changes, updated_at=utc_now())
