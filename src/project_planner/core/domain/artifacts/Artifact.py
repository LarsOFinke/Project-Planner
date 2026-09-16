from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from uuid import uuid4

from project_planner.core.domain.artifacts.ArtifactKind import ArtifactKind
from project_planner.core.domain.shared.clock import utc_now


@dataclass(frozen=True, slots=True)
class Artifact:
    project_id: str
    title: str
    kind: ArtifactKind
    content: str = "{}"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Artifact title must not be empty")

    def revise_content(self, content: str) -> Artifact:
        return replace(self, content=content, updated_at=utc_now())
