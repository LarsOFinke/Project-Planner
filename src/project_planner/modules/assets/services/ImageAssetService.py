from pathlib import Path
from shutil import copy2
from uuid import uuid4


class ImageAssetService:
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

    def __init__(self, data_directory: Path) -> None:
        self._data_directory = data_directory

    def import_image(self, project_id: str, source: str | Path) -> Path:
        self._validate_project_id(project_id)
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise ValueError("Selected image does not exist")
        extension = source_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported image format. Supported: {supported}")
        detected = self._image_extension(source_path)
        normalized_extension = ".jpg" if extension == ".jpeg" else extension
        if detected != normalized_extension:
            raise ValueError("Selected file content does not match its image extension")
        destination_directory = self._data_directory / "projects" / project_id / "images"
        destination_directory.mkdir(parents=True, exist_ok=True)
        destination = destination_directory / f"{uuid4().hex}{extension}"
        copy2(source_path, destination)
        return destination

    @staticmethod
    def reference(filename: str) -> str:
        return f"managed://images/{Path(filename).name}"

    @staticmethod
    def reference_filename(reference: str) -> str:
        prefix = "managed://images/"
        if not reference.startswith(prefix):
            raise ValueError("Unsupported managed image reference")
        filename = reference.removeprefix(prefix)
        if not filename or Path(filename).name != filename:
            raise ValueError("Invalid managed image reference")
        return filename

    @staticmethod
    def _image_extension(path: Path) -> str | None:
        with path.open("rb") as image_file:
            header = image_file.read(16)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return ".png"
        if header.startswith(b"\xff\xd8\xff"):
            return ".jpg"
        if header.startswith((b"GIF87a", b"GIF89a")):
            return ".gif"
        if header.startswith(b"BM"):
            return ".bmp"
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return ".webp"
        return None

    def get_image(self, project_id: str, filename: str) -> Path:
        self._validate_project_id(project_id)
        directory = (self._data_directory / "projects" / project_id / "images").resolve()
        candidate = (directory / Path(filename).name).resolve()
        if candidate.parent != directory or not candidate.is_file():
            raise LookupError("Managed image does not exist")
        return candidate

    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        if not project_id or project_id in {".", ".."} or Path(project_id).name != project_id:
            raise ValueError("Invalid managed image project identifier")
