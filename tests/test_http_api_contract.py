import asyncio
import json
from dataclasses import replace
from pathlib import Path

import httpx
from project_planner_frontend.api.ApiTransport import ApiTransport
from project_planner_frontend.projects.clients.ProjectServiceClient import ProjectServiceClient
from project_planner_frontend.system.clients.DatabaseTransferClient import DatabaseTransferClient

from project_planner.api.controller_builder import build_controllers
from project_planner.api.http.app_factory import create_app
from project_planner.modules.projects.entities.Project import Project
from project_planner.shared.settings.Settings import Settings


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "planner.sqlite3",
        data_directory=tmp_path / "data",
        window_width=1280,
        window_height=800,
        autosave_seconds=20,
    )


def test_openapi_exposes_versioned_typed_resources(tmp_path: Path) -> None:
    application = create_app(_settings(tmp_path))
    schema = application.openapi()

    assert "/api/v1/projects" in schema["paths"]
    assert "/api/v1/projects/{project_id}/sprints" in schema["paths"]
    assert "/api/v1/projects/{project_id}/artifacts/{kind}" in schema["paths"]
    assert "put" in schema["paths"]["/api/v1/project-categories/{category_id}"]
    assert "post" in schema["paths"]["/api/v1/projects/{project_id}/archive"]
    assert "put" in schema["paths"]["/api/v1/projects/{project_id}/move"]
    assert "get" in schema["paths"]["/api/v1/database/export"]
    assert "post" in schema["paths"]["/api/v1/database/import"]
    assert "post" in schema["paths"]["/api/v1/database/import/dry-run"]
    assert "Project" in schema["components"]["schemas"]
    assert "Sprint" in schema["components"]["schemas"]


def test_api_routes_are_owned_directly_by_feature_controllers(tmp_path: Path) -> None:
    controllers = build_controllers(_settings(tmp_path))
    create_app(controllers=controllers)
    endpoints = [route.endpoint for controller in controllers for route in controller.router.routes]

    assert endpoints
    assert all(
        endpoint.__self__.__class__.__name__.endswith("Controller") for endpoint in endpoints
    )


def test_project_client_uses_http_contract_and_decodes_project() -> None:
    project = Project("HTTP project")

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/projects/{project.id}"
        return httpx.Response(
            200,
            json={
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "status": project.status.value,
                "planning_method": project.planning_method.value,
                "parent_id": project.parent_id,
                "category_id": project.category_id,
                "start_date": project.start_date,
                "target_date": project.target_date,
                "owner": project.owner,
                "assignee": project.assignee,
                "notes": project.notes,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
        )

    transport = ApiTransport("http://test/api/v1", transport=httpx.MockTransport(respond))
    try:
        result = ProjectServiceClient(transport).require(project.id)
    finally:
        transport.close()

    assert result == project


def test_database_transfer_client_reads_and_writes_local_json(tmp_path: Path) -> None:
    document = {
        "format": "project-planner-database-export",
        "version": 5,
        "exported_at": "2026-09-19T12:00:00+00:00",
        "tables": {},
    }

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == "/api/v1/database/export"
            return httpx.Response(200, json=document)
        assert request.method == "POST"
        assert json.loads(request.content) == document
        dry_run = request.url.path.endswith("/dry-run")
        expected_path = "/api/v1/database/import/dry-run" if dry_run else "/api/v1/database/import"
        assert request.url.path == expected_path
        return httpx.Response(
            200,
            json={"created": 2, "updated": 3, "dry_run": dry_run},
        )

    transport = ApiTransport("http://test/api/v1", transport=httpx.MockTransport(respond))
    client = DatabaseTransferClient(transport)
    try:
        destination = client.export_to(tmp_path / "backup")
        dry_run = client.dry_run_import(destination)
        report = client.import_from(destination)
    finally:
        transport.close()

    assert destination == tmp_path / "backup.json"
    assert json.loads(destination.read_text(encoding="utf-8")) == document
    assert dry_run.dry_run is True
    assert report.created == 2
    assert report.updated == 3
    assert report.dry_run is False


def test_asgi_project_and_managed_image_round_trip(tmp_path: Path) -> None:
    application = create_app(_settings(tmp_path))

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post("/api/v1/projects", json={"title": "Integrated"})
            assert created.status_code == 201
            project_id = created.json()["id"]
            parent = await client.post("/api/v1/projects", json={"title": "Parent"})
            moved = await client.put(
                f"/api/v1/projects/{project_id}/move",
                json={"parent_id": parent.json()["id"], "category_id": None},
            )
            assert moved.status_code == 200
            assert moved.json()["parent_id"] == parent.json()["id"]

            phase = await client.post(
                f"/api/v1/projects/{project_id}/phases",
                json={
                    "name": "Delivery",
                    "status": "in_progress",
                    "parallel_group": "Delivery lane",
                },
            )
            assert phase.status_code == 201
            assert phase.json()["name"] == "Delivery"
            assert phase.json()["parallel_group"] == "Delivery lane"

            uploaded = await client.post(
                f"/api/v1/projects/{project_id}/images",
                files={"image": ("pixel.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
            )
            assert uploaded.status_code == 201
            reference = uploaded.json()["reference"]
            assert reference.startswith("managed://images/")

            filename = reference.removeprefix("managed://images/")
            downloaded = await client.get(f"/api/v1/projects/{project_id}/images/{filename}")
            assert downloaded.status_code == 200
            assert downloaded.content == b"\x89PNG\r\n\x1a\ncontent"

    asyncio.run(scenario())


def test_asgi_database_export_dry_run_and_import(tmp_path: Path) -> None:
    application = create_app(_settings(tmp_path))

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post("/api/v1/projects", json={"title": "Before import"})
            project_id = created.json()["id"]
            exported = await client.get("/api/v1/database/export")
            assert exported.status_code == 200
            document = exported.json()
            project_row = next(
                row for row in document["tables"]["projects"] if row["id"] == project_id
            )
            project_row["title"] = "After import"

            dry_run = await client.post(
                "/api/v1/database/import/dry-run",
                json=document,
            )
            assert dry_run.status_code == 200
            assert dry_run.json() == {"created": 0, "updated": 1, "dry_run": True}
            unchanged = await client.get(f"/api/v1/projects/{project_id}")
            assert unchanged.json()["title"] == "Before import"

            applied = await client.post(
                "/api/v1/database/import",
                json=document,
            )
            assert applied.status_code == 200
            assert applied.json() == {"created": 0, "updated": 1, "dry_run": False}
            updated = await client.get(f"/api/v1/projects/{project_id}")
            assert updated.json()["title"] == "After import"

    asyncio.run(scenario())


def test_asgi_authentication_upload_limits_and_project_ownership(tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), api_token="secret", max_image_bytes=12)

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=create_app(settings))
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/api/v1/projects")).status_code == 401
            headers = {"Authorization": "Bearer secret"}
            created = await client.post(
                "/api/v1/projects", json={"title": "Secured"}, headers=headers
            )
            assert created.status_code == 201
            project_id = created.json()["id"]

            oversized = await client.post(
                f"/api/v1/projects/{project_id}/images",
                files={"image": ("large.png", b"\x89PNG\r\n\x1a\n12345", "image/png")},
                headers=headers,
            )
            assert oversized.status_code == 413

            missing = await client.post(
                "/api/v1/projects/missing/images",
                files={"image": ("pixel.png", b"\x89PNG\r\n\x1a\n", "image/png")},
                headers=headers,
            )
            assert missing.status_code == 404

    asyncio.run(scenario())
