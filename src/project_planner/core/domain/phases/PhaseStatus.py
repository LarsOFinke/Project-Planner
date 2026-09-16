from enum import StrEnum


class PhaseStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    SKIPPED = "skipped"
