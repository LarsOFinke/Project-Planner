from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportReport:
    created: int
    updated: int
    dry_run: bool
    unchanged: int = 0
    files_created: int = 0
    files_unchanged: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged
