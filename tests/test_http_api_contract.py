from pathlib import Path

import httpx
from project_planner_frontend.api.ApiTransport import ApiTransport
from project_planner_frontend.projects.clients.ProjectServiceClient import ProjectServiceClient

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
