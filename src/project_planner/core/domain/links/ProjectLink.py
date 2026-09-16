from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectLink:
    source_id: str
    target_id: str
    relation: str = "related"
    note: str = ""

    def __post_init__(self) -> None:
        if self.source_id == self.target_id:
            raise ValueError("A project cannot link to itself")
        if not self.relation.strip():
            raise ValueError("A link relation must not be empty")
