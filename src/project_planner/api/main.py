import argparse
import ipaddress

import uvicorn

from project_planner.api.http.app_factory import create_app
from project_planner.shared.settings.settings_loader import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Project Planner HTTP API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    settings = load_settings()
    try:
        loopback = ipaddress.ip_address(args.host).is_loopback
    except ValueError:
        loopback = args.host.lower() == "localhost"
    if not loopback and settings.api_token is None:
        parser.error("PROJECT_PLANNER_API_TOKEN is required for a non-loopback host")
    uvicorn.run(
        create_app(settings, cors_origins=settings.api_cors_origins),
        host=args.host,
        port=args.port,
    )
