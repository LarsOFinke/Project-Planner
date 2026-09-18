from project_planner.modules.health.entities.SystemHealth import SystemHealth
from project_planner_frontend.api.ApiTransport import ApiTransport


class HealthClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def snapshot(self) -> SystemHealth:
        return self._transport.model(SystemHealth, "GET", "/health")
