from enum import StrEnum


class ProjectStatus(StrEnum):
    IDEA = "idea"
    PLANNED = "planned"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"
