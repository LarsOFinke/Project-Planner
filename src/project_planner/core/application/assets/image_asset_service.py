from pathlib import Path
from shutil import copy2
from uuid import uuid4


class ImageAssetService:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

    def __init__(self, data_directory: Path) -> None:
        self._data_directory = data_directory

    def import_image(self, project_id: str, source: str | Path) -> Path:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise ValueError("Selected image does not exist")
        extension = source_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported image format. Supported: {supported}")
        destination_directory = self._data_directory / "projects" / project_id / "images"
        destination_directory.mkdir(parents=True, exist_ok=True)
        destination = destination_directory / f"{uuid4().hex}{extension}"
        copy2(source_path, destination)
        return destination
