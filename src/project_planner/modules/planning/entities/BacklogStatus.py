from enum import StrEnum


class BacklogStatus(StrEnum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    DONE = "done"
