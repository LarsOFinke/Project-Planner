from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Body, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from project_planner.api.artifacts.dtos.ImageUploadResult import ImageUploadResult
from project_planner.modules.artifacts.entities.Artifact import Artifact
from project_planner.modules.artifacts.entities.ArtifactKind import ArtifactKind
from project_planner.modules.artifacts.entities.ArtifactRevision import ArtifactRevision
from project_planner.modules.artifacts.services.ArtifactService import ArtifactService
from project_planner.modules.assets.services.ImageAssetService import ImageAssetService
from project_planner.modules.projects.services.ProjectService import ProjectService


class ArtifactController:
    def __init__(
        self,
        artifacts: ArtifactService,
        images: ImageAssetService,
        projects: ProjectService,
        max_image_bytes: int,
    ) -> None:
        self._artifacts = artifacts
        self._images = images
        self._projects = projects
        self._max_image_bytes = max_image_bytes
        self.router = APIRouter(tags=["artifacts"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_artifact_routes()
        self._register_image_routes()

    def _register_artifact_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/artifacts/{kind}",
            self.get_artifact,
            methods=["GET"],
            response_model=Artifact,
        )
        routes.add_api_route(
            "/projects/{project_id}/artifacts/{kind}",
            self.save_artifact,
            methods=["PUT"],
            response_model=Artifact,
        )
        routes.add_api_route(
            "/projects/{project_id}/artifacts/{kind}/content",
            self.read_artifact,
            methods=["GET"],
        )
        routes.add_api_route(
            "/projects/{project_id}/artifacts/{kind}/revisions",
            self.list_revisions,
            methods=["GET"],
            response_model=tuple[ArtifactRevision, ...],
        )
        routes.add_api_route(
            "/projects/{project_id}/artifacts/{kind}/revisions/{revision_id}/restore",
            self.restore_revision,
            methods=["POST"],
            response_model=Artifact,
        )

    def _register_image_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/images",
            self.import_image,
            methods=["POST"],
            status_code=201,
            response_model=ImageUploadResult,
        )
        routes.add_api_route(
            "/projects/{project_id}/images/{filename}",
            self.get_managed_image,
            methods=["GET"],
            name="get_managed_image",
            response_class=FileResponse,
        )

    def get_artifact(self, project_id: str, kind: ArtifactKind):
        self._projects.require(project_id)
        return self._artifacts.get_or_create(project_id, kind)

    def save_artifact(
        self,
        project_id: str,
        kind: ArtifactKind,
        content: Annotated[object, Body(embed=True)],
    ):
        self._projects.require(project_id)
        artifact = self._artifacts.get_or_create(project_id, kind)
        return self._artifacts.save_json(artifact, content)

    def read_artifact(self, project_id: str, kind: ArtifactKind) -> object:
        self._projects.require(project_id)
        artifact = self._artifacts.get_or_create(project_id, kind)
        return self._artifacts.read_json(artifact)

    def list_revisions(self, project_id: str, kind: ArtifactKind):
        self._projects.require(project_id)
        artifact = self._artifacts.get_or_create(project_id, kind)
        return self._artifacts.list_revisions(artifact)

    def restore_revision(self, project_id: str, kind: ArtifactKind, revision_id: str):
        self._projects.require(project_id)
        artifact = self._artifacts.get_or_create(project_id, kind)
        return self._artifacts.restore_revision(artifact, revision_id)

    def import_image(
        self,
        project_id: str,
        request: Request,
        image: Annotated[UploadFile, File()],
    ) -> ImageUploadResult:
        self._projects.require(project_id)
        suffix = Path(image.filename or "image").suffix
        with NamedTemporaryFile(suffix=suffix) as temporary:
            size = 0
            while chunk := image.file.read(1024 * 1024):
                size += len(chunk)
                if size > self._max_image_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Image exceeds the {self._max_image_bytes}-byte upload limit",
                    )
                temporary.write(chunk)
            temporary.flush()
            imported = self._images.import_image(project_id, temporary.name)
        reference = self._images.reference(imported.name)
        return ImageUploadResult(
            reference=reference,
            path=reference,
            url=str(
                request.url_for("get_managed_image", project_id=project_id, filename=imported.name)
            ),
        )

    def get_managed_image(self, project_id: str, filename: str) -> FileResponse:
        self._projects.require(project_id)
        return FileResponse(self._images.get_image(project_id, filename))
