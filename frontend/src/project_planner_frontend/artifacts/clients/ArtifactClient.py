from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.entities.ArtifactRevision import ArtifactRevision
from project_planner_frontend.api.ApiTransport import ApiTransport


class ArtifactClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def get_or_create(self, project_id: str, kind: ArtifactKind) -> Artifact:
        return self._transport.model(
            Artifact, "GET", f"/projects/{project_id}/artifacts/{kind.value}"
        )

    def save_json(self, artifact: Artifact, content: object) -> Artifact:
        return self._transport.model(
            Artifact,
            "PUT",
            f"/projects/{artifact.project_id}/artifacts/{artifact.kind.value}",
            payload={"content": content},
        )

    def read_json(self, artifact: Artifact) -> object:
        return self._transport.request(
            "GET", f"/projects/{artifact.project_id}/artifacts/{artifact.kind.value}/content"
        )

    def list_revisions(self, artifact: Artifact) -> tuple[ArtifactRevision, ...]:
        return self._transport.model(
            tuple[ArtifactRevision, ...],
            "GET",
            f"/projects/{artifact.project_id}/artifacts/{artifact.kind.value}/revisions",
        )

    def restore_revision(self, artifact: Artifact, revision_id: str) -> Artifact:
        return self._transport.model(
            Artifact,
            "POST",
            f"/projects/{artifact.project_id}/artifacts/{artifact.kind.value}/"
            f"revisions/{revision_id}/restore",
        )
