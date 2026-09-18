import os
from configparser import ConfigParser
from importlib.resources import files
from pathlib import Path

from project_planner.shared.settings.Settings import Settings

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
    database_url = (
        os.environ.get("PROJECT_PLANNER_DB_URL", parser["database"].get("url", "")).strip() or None
    )
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
    fullscreen = os.environ.get("PROJECT_PLANNER_FULLSCREEN", parser["window"]["fullscreen"])
    data_directory = os.environ.get("PROJECT_PLANNER_DATA_DIR", parser["storage"]["data_directory"])
    api_url = os.environ.get("PROJECT_PLANNER_API_URL", parser["api"].get("url", "")).strip()
    cors_origins = os.environ.get(
        "PROJECT_PLANNER_API_CORS_ORIGINS", parser["api"].get("cors_origins", "")
    )
    api_token = os.environ.get("PROJECT_PLANNER_API_TOKEN", parser["api"].get("token", "")).strip()
    max_image_bytes = os.environ.get(
        "PROJECT_PLANNER_MAX_IMAGE_BYTES", parser["storage"].get("max_image_bytes", "20971520")
    )
    return Settings(
        database_path=Path(database).expanduser(),
        window_width=width,
        window_height=height,
        autosave_seconds=_positive_int(autosave, "autosave interval"),
        ui_scale=_ui_scale(ui_scale, width, height),
        fullscreen=_boolean(fullscreen, "fullscreen"),
        data_directory=Path(data_directory).expanduser(),
        database_url=database_url,
        api_url=api_url or None,
        api_cors_origins=tuple(
            origin.strip() for origin in cors_origins.split(",") if origin.strip()
        ),
        api_token=api_token or None,
        max_image_bytes=_positive_int(max_image_bytes, "maximum image size"),
    )


def _positive_int(value: str, label: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"Invalid {label}: {value!r}") from error
    if parsed <= 0:
        raise ValueError(f"{label.capitalize()} must be positive")
    return parsed


def _boolean(value: str, label: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid {label}: {value!r}")


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


def save_fullscreen(fullscreen: bool, config_path: str | Path | None = None) -> None:
    path = Path(config_path).expanduser() if config_path is not None else _USER_CONFIG
    parser = ConfigParser()
    if path.is_file():
        parser.read(path)
    if not parser.has_section("window"):
        parser.add_section("window")
    parser["window"]["fullscreen"] = "true" if fullscreen else "false"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as config_file:
        parser.write(config_file)
