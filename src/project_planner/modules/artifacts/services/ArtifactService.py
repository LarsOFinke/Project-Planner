import json

from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.entities.ArtifactRevision import ArtifactRevision
from project_planner.modules.artifacts.protocols.ArtifactRepository import ArtifactRepository


class ArtifactService:
    def __init__(self, artifacts: ArtifactRepository) -> None:
        self._artifacts = artifacts

    def get_or_create(self, project_id: str, kind: ArtifactKind) -> Artifact:
        artifact = self._artifacts.get_for_project(project_id, kind)
        if artifact is not None:
            return artifact
        title = "Project diagram" if kind is ArtifactKind.DIAGRAM else "Free workspace"
        artifact = Artifact(project_id=project_id, title=title, kind=kind)
        return self._artifacts.create_if_absent(artifact)

    def save_json(self, artifact: Artifact, content: object) -> Artifact:
        serialized = json.dumps(content, separators=(",", ":"), sort_keys=True)
        updated = artifact.revise_content(serialized)
        self._artifacts.save(updated)
        return updated

    def list_revisions(self, artifact: Artifact) -> tuple[ArtifactRevision, ...]:
        return self._artifacts.list_revisions(artifact.id)

    def restore_revision(self, artifact: Artifact, revision_id: str) -> Artifact:
        revision = self._artifacts.get_revision(artifact.id, revision_id)
        if revision is None:
            raise LookupError("Artifact revision not found")
        return self.save_json(artifact, json.loads(revision.content))

    @staticmethod
    def read_json(artifact: Artifact) -> object:
        try:
            return json.loads(artifact.content)
        except json.JSONDecodeError as error:
            raise ValueError("Artifact content is not valid JSON") from error
