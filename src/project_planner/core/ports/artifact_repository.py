from typing import Protocol

from project_planner.core.domain.artifacts.artifact import Artifact
from project_planner.core.domain.artifacts.artifact_kind import ArtifactKind


class ArtifactRepository(Protocol):
    def save(self, artifact: Artifact) -> None: ...
    def get_for_project(
        self, project_id: str, kind: ArtifactKind
    ) -> Artifact | None: ...
