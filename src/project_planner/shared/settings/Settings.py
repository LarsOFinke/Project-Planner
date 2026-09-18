from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    window_width: int
    window_height: int
    autosave_seconds: int
    ui_scale: float = 2.00
    fullscreen: bool = True
    data_directory: Path = field(default_factory=lambda: Path.home() / ".project_planner" / "data")
    database_url: str | None = None
    api_url: str | None = None
    api_cors_origins: tuple[str, ...] = ()
    api_token: str | None = None
    max_image_bytes: int = 20 * 1024 * 1024
