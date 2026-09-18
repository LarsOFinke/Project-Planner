from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from project_planner.api.artifacts.ArtifactController import ArtifactController
from project_planner.api.collaboration.CollaborationController import CollaborationController
from project_planner.api.controller_builder import build_controllers
from project_planner.api.planning.PlanningController import PlanningController
from project_planner.api.projects.ProjectController import ProjectController
from project_planner.api.system.SystemController import SystemController
from project_planner.shared.settings.Settings import Settings


def create_app(
    settings: Settings | None = None,
    *,
    controllers: tuple[
        ProjectController,
        PlanningController,
        CollaborationController,
        ArtifactController,
        SystemController,
    ]
    | None = None,
    cors_origins: tuple[str, ...] = (),
) -> FastAPI:
    application = FastAPI(
        title="Project Planner API",
        version="0.1.0",
        description="Versioned backend API for desktop and web Project Planner clients.",
    )
    feature_controllers = controllers or build_controllers(settings)
    (
        _projects_controller,
        _planning_controller,
        _collaboration_controller,
        _artifact_controller,
        system_controller,
    ) = feature_controllers
    if cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @application.exception_handler(LookupError)
    async def not_found(_request: Request, error: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @application.exception_handler(ValueError)
    async def invalid_value(_request: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})

    @application.exception_handler(Exception)
    async def unexpected(_request: Request, error: Exception) -> JSONResponse:
        system_controller.record_exception(error, "api")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    for controller in feature_controllers:
        application.include_router(controller.router, prefix="/api/v1")
    return application
