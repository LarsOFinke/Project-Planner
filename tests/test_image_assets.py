from pathlib import Path

import httpx
import pytest
from project_planner_frontend.api.ApiTransport import ApiTransport
from project_planner_frontend.artifacts.clients.ImageAssetClient import ImageAssetClient

from project_planner.modules.assets.services.ImageAssetService import ImageAssetService


def test_imports_image_into_project_data_directory(tmp_path: Path) -> None:
    source = tmp_path / "cover.PNG"
    source.write_bytes(b"\x89PNG\r\n\x1a\nimage bytes")
    service = ImageAssetService(tmp_path / "data")

    imported = service.import_image("project-1", source)

    assert imported.parent == tmp_path / "data" / "projects" / "project-1" / "images"
    assert imported.suffix == ".png"
    assert imported.read_bytes() == b"\x89PNG\r\n\x1a\nimage bytes"


def test_rejects_unsupported_image_format(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("not an image", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported image format"):
        ImageAssetService(tmp_path / "data").import_image("project-1", source)


def test_resolves_only_managed_project_images(tmp_path: Path) -> None:
    source = tmp_path / "cover.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\nimage bytes")
    service = ImageAssetService(tmp_path / "data")
    imported = service.import_image("project-1", source)

    assert service.get_image("project-1", imported.name) == imported
    with pytest.raises(LookupError, match="does not exist"):
        service.get_image("project-1", "../project-planner.sqlite3")


def test_rejects_extension_only_image_and_builds_portable_reference(tmp_path: Path) -> None:
    fake = tmp_path / "fake.png"
    fake.write_bytes(b"not really an image")
    service = ImageAssetService(tmp_path / "data")

    with pytest.raises(ValueError, match="does not match"):
        service.import_image("project-1", fake)

    assert service.reference("image.png") == "managed://images/image.png"
    assert service.reference_filename("managed://images/image.png") == "image.png"
    with pytest.raises(ValueError, match="project identifier"):
        service.import_image("..", fake)


def test_client_materializes_managed_image_in_local_cache(tmp_path: Path) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/projects/project-1/images/image.png"
        return httpx.Response(200, content=b"\x89PNG\r\n\x1a\ncontent")

    transport = ApiTransport("http://test/api/v1", transport=httpx.MockTransport(respond))
    try:
        client = ImageAssetClient(transport, tmp_path / "cache")
        materialized = client.materialize("project-1", "managed://images/image.png")
    finally:
        transport.close()

    assert materialized == tmp_path / "cache" / "project-1" / "image.png"
    assert materialized.read_bytes() == b"\x89PNG\r\n\x1a\ncontent"
