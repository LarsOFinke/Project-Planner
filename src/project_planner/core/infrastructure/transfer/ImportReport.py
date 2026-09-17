from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImportReport:
    created: int
    updated: int
    dry_run: bool

    @property
    def total(self) -> int:
        return self.created + self.updated
