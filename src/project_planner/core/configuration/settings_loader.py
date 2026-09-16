import os
from configparser import ConfigParser
from importlib.resources import files
from pathlib import Path

from project_planner.core.configuration.Settings import Settings

_USER_CONFIG = Path.home() / ".config" / "project_planner" / "config.cfg"


def load_settings(config_path: str | Path | None = None) -> Settings:
    parser = ConfigParser()
    default = files("project_planner").joinpath("config/default.cfg")
    parser.read_string(default.read_text(encoding="utf-8"))
    candidates = [
        Path.cwd() / "project_planner.cfg",
        _USER_CONFIG,
    ]
    if config_path is not None:
        candidates.append(Path(config_path))
    parser.read([str(path) for path in candidates if path.is_file()])

    database = os.environ.get("PROJECT_PLANNER_DB", parser["database"]["path"])
    width = _positive_int(
        os.environ.get("PROJECT_PLANNER_WINDOW_WIDTH", parser["window"]["width"]),
        "window width",
    )
    height = _positive_int(
        os.environ.get("PROJECT_PLANNER_WINDOW_HEIGHT", parser["window"]["height"]),
        "window height",
    )
    autosave = os.environ.get(
        "PROJECT_PLANNER_AUTOSAVE_SECONDS", parser["editor"]["autosave_seconds"]
    )
    ui_scale = os.environ.get("PROJECT_PLANNER_UI_SCALE", parser["ui"]["scale"])
    data_directory = os.environ.get(
        "PROJECT_PLANNER_DATA_DIR", parser["storage"]["data_directory"]
    )
    return Settings(
        database_path=Path(database).expanduser(),
        window_width=width,
        window_height=height,
        autosave_seconds=_positive_int(autosave, "autosave interval"),
        ui_scale=_ui_scale(ui_scale, width, height),
        data_directory=Path(data_directory).expanduser(),
    )


def _positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"Invalid {label}: {value!r}") from error
    if parsed <= 0:
        raise ValueError(f"{label.capitalize()} must be positive")
    return parsed


def _ui_scale(value: str, width: int, height: int) -> float:
    if value.strip().lower() == "auto":
        return 1.0 if width >= 1920 and height >= 1080 else 2.0
    try:
        parsed = float(value)
    except ValueError as error:
        raise ValueError(f"Invalid UI scale: {value!r}") from error
    if not 0.05 <= parsed <= 5.0:
        raise ValueError("UI scale must be between 0.05 and 5.0")
    return parsed


def save_ui_scale(ui_scale: float, config_path: str | Path | None = None) -> None:
    validated = _ui_scale(str(ui_scale), 1, 1)
    path = Path(config_path).expanduser() if config_path is not None else _USER_CONFIG
    parser = ConfigParser()
    if path.is_file():
        parser.read(path)
    if not parser.has_section("ui"):
        parser.add_section("ui")
    parser["ui"]["scale"] = f"{validated:.2f}"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)
