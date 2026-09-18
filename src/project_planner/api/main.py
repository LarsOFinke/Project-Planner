import argparse

import uvicorn

from project_planner.api.http.app_factory import create_app
from project_planner.shared.settings.settings_loader import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Project Planner HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    settings = load_settings()
    uvicorn.run(
        create_app(settings, cors_origins=settings.api_cors_origins),
        host=args.host,
        port=args.port,
    )
