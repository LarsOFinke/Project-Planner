from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemHealth:
    app_version: str
    python_version: str
    database_backend: str
    database_location: str
    database_healthy: bool
    issue_count: int
