import os
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from project_planner.api.artifacts.dtos.ImageUploadResult import ImageUploadResult
from project_planner_frontend.api.ApiTransport import ApiTransport


class ImageAssetClient:
    def __init__(self, transport: ApiTransport, cache_directory: Path | None = None) -> None:
        self._transport = transport
        self._cache_directory = cache_directory or (
            Path.home() / ".cache" / "project_planner" / "images"
        )

    def import_image(self, project_id: str, source: str | Path) -> Path:
        uploaded = self.upload_image(project_id, source)
        return self.materialize(project_id, uploaded.reference)

    def upload_image(self, project_id: str, source: str | Path) -> ImageUploadResult:
        path = Path(source)
        with path.open("rb") as stream:
            payload = self._transport.request(
                "POST", f"/projects/{project_id}/images", files={"image": (path.name, stream)}
            )
        return TypeAdapter(ImageUploadResult).validate_python(payload)

    def materialize(self, project_id: str, reference: str) -> Path:
        prefix = "managed://images/"
        if not reference.startswith(prefix):
            return Path(reference)
        filename = reference.removeprefix(prefix)
        if not filename or Path(filename).name != filename:
            raise ValueError("Invalid managed image reference")
        if not project_id or project_id in {".", ".."} or Path(project_id).name != project_id:
            raise ValueError("Invalid project image cache identifier")
        cache = self._cache_directory / project_id
        cache.mkdir(parents=True, exist_ok=True)
        destination = cache / filename
        if destination.is_file():
            return destination
        content = self._transport.request_bytes(f"/projects/{project_id}/images/{filename}")
        handle, temporary_name = tempfile.mkstemp(prefix=f".{filename}.", dir=cache)
        try:
            with os.fdopen(handle, "wb") as temporary:
                temporary.write(content)
            os.replace(temporary_name, destination)
        except Exception:
            Path(temporary_name).unlink(missing_ok=True)
            raise
        return destination
