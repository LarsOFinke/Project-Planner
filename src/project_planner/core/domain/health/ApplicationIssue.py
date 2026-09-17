from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class ApplicationIssue:
    source: str
    exception_type: str
    message: str
    traceback: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=utc_now)
