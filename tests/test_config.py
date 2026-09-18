from pathlib import Path

import pytest

from project_planner.shared.settings import settings_loader
from project_planner.shared.settings.settings_loader import (
    load_settings,
    save_fullscreen,
    save_ui_scale,
)


@pytest.fixture(autouse=True)
def isolate_user_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings_loader, "_USER_CONFIG", tmp_path / "user.cfg")


def test_cfg_values_can_be_overridden_by_environment(monkeypatch, tmp_path: Path) -> None:
    config = tmp_path / "test.cfg"
    config.write_text(
        "[database]\npath = from-cfg.sqlite3\n"
        "[window]\nwidth = 900\nheight = 600\nfullscreen = false\n"
        "[editor]\nautosave_seconds = 30\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PROJECT_PLANNER_DB", str(tmp_path / "from-env.sqlite3"))
    monkeypatch.setenv("PROJECT_PLANNER_DB_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("PROJECT_PLANNER_WINDOW_WIDTH", "1440")
    monkeypatch.setenv("PROJECT_PLANNER_FULLSCREEN", "true")
    monkeypatch.setenv("PROJECT_PLANNER_UI_SCALE", "1.45")
    monkeypatch.setenv("PROJECT_PLANNER_DATA_DIR", str(tmp_path / "assets"))

    settings = load_settings(config)

    assert settings.database_path == tmp_path / "from-env.sqlite3"
    assert settings.database_url == "sqlite+pysqlite:///:memory:"
    assert settings.window_width == 1440
    assert settings.window_height == 600
    assert settings.fullscreen is True
    assert settings.autosave_seconds == 30
    assert settings.ui_scale == 1.45
    assert settings.data_directory == tmp_path / "assets"


def test_auto_scale_keeps_laptop_profile_readable(tmp_path: Path) -> None:
    config = tmp_path / "laptop.cfg"
    config.write_text("[window]\nwidth = 1280\nheight = 800\n", encoding="utf-8")

    assert load_settings(config).ui_scale == 2.0


def test_fullscreen_is_enabled_by_default_and_can_be_disabled(tmp_path: Path) -> None:
    assert load_settings().fullscreen is True
    config = tmp_path / "windowed.cfg"
    config.write_text("[window]\nfullscreen = false\n", encoding="utf-8")

    assert load_settings(config).fullscreen is False


def test_fullscreen_preference_is_persisted(tmp_path: Path) -> None:
    config = tmp_path / "preferences.cfg"

    save_fullscreen(False, config)
    assert load_settings(config).fullscreen is False
    save_fullscreen(True, config)
    assert load_settings(config).fullscreen is True


def test_auto_scale_uses_native_density_for_full_hd(tmp_path: Path) -> None:
    config = tmp_path / "full-hd.cfg"
    config.write_text("[window]\nwidth = 1920\nheight = 1080\n", encoding="utf-8")

    assert load_settings(config).ui_scale == 1.0


def test_ui_scale_preference_supports_five_to_five_hundred_percent(
    tmp_path: Path,
) -> None:
    config = tmp_path / "preferences.cfg"

    save_ui_scale(0.05, config)
    assert load_settings(config).ui_scale == 0.05
    save_ui_scale(5.0, config)
    assert load_settings(config).ui_scale == 5.0


@pytest.mark.parametrize("ui_scale", [0.04, 5.01])
def test_ui_scale_preference_rejects_values_outside_dropdown_range(
    tmp_path: Path, ui_scale: float
) -> None:
    with pytest.raises(ValueError, match="between 0.05 and 5.0"):
        save_ui_scale(ui_scale, tmp_path / "preferences.cfg")
