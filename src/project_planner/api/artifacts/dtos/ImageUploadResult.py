from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageUploadResult:
    path: str
    url: str
