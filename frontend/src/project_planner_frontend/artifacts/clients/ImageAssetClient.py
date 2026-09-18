from pathlib import Path

from pydantic import TypeAdapter

from project_planner.api.artifacts.dtos.ImageUploadResult import ImageUploadResult
from project_planner_frontend.api.ApiTransport import ApiTransport


class ImageAssetClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def import_image(self, project_id: str, source: str | Path) -> Path:
        return Path(self.upload_image(project_id, source).path)

    def upload_image(self, project_id: str, source: str | Path) -> ImageUploadResult:
        path = Path(source)
        with path.open("rb") as stream:
            payload = self._transport.request(
                "POST", f"/projects/{project_id}/images", files={"image": (path.name, stream)}
            )
        return TypeAdapter(ImageUploadResult).validate_python(payload)
