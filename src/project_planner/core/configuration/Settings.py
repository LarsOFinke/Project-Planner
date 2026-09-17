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
