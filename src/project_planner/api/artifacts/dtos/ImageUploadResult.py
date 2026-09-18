from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageUploadResult:
    reference: str
    path: str
    url: str
