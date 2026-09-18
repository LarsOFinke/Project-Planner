from pathlib import Path

import pytest

from project_planner.modules.assets.services.ImageAssetService import ImageAssetService


def test_imports_image_into_project_data_directory(tmp_path: Path) -> None:
    source = tmp_path / "cover.PNG"
    source.write_bytes(b"image bytes")
    service = ImageAssetService(tmp_path / "data")

    imported = service.import_image("project-1", source)

    assert imported.parent == tmp_path / "data" / "projects" / "project-1" / "images"
    assert imported.suffix == ".png"
    assert imported.read_bytes() == b"image bytes"


def test_rejects_unsupported_image_format(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not an image", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported image format"):
        ImageAssetService(tmp_path / "data").import_image("project-1", source)


def test_resolves_only_managed_project_images(tmp_path: Path) -> None:
    source = tmp_path / "cover.png"
    source.write_bytes(b"image bytes")
    service = ImageAssetService(tmp_path / "data")
    imported = service.import_image("project-1", source)

    assert service.get_image("project-1", imported.name) == imported
    with pytest.raises(LookupError, match="does not exist"):
        service.get_image("project-1", "../project-planner.sqlite3")
