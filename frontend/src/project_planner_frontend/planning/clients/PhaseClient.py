from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner_frontend.api.ApiTransport import ApiTransport


class PhaseClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def list_for_project(self, project_id: str) -> Sequence[Phase]:
        return self.list_for_context(project_id)

    def list_for_context(self, project_id: str, section_id: str | None = None) -> Sequence[Phase]:
        return self._transport.model(
            list[Phase], "GET", f"/projects/{project_id}/phases", params={"section_id": section_id}
        )

    def initialize_waterfall(
        self, project_id: str, section_id: str | None = None
    ) -> Sequence[Phase]:
        return self._transport.model(
            list[Phase],
            "POST",
            f"/projects/{project_id}/waterfall-template",
            payload={"section_id": section_id},
        )

    def reset_waterfall(self, project_id: str, section_id: str | None = None) -> Sequence[Phase]:
        return self._transport.model(
            list[Phase],
            "PUT",
            f"/projects/{project_id}/waterfall-template",
            payload={"section_id": section_id},
        )

    def add(
        self,
        project_id: str,
        name: str,
        description: str = "",
        status: PhaseStatus = PhaseStatus.NOT_STARTED,
        start_date: date | None = None,
        end_date: date | None = None,
        section_id: str | None = None,
    ) -> Phase:
        return self._transport.model(
            Phase,
            "POST",
            f"/projects/{project_id}/phases",
            payload={
                "name": name,
                "description": description,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
                "section_id": section_id,
            },
        )

    def update(
        self,
        phase_id: str,
        project_id: str,
        name: str,
        description: str,
        status: PhaseStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Phase:
        return self._transport.model(
            Phase,
            "PUT",
            f"/projects/{project_id}/phases/{phase_id}",
            payload={
                "name": name,
                "description": description,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def remove(self, project_id: str, phase_id: str) -> None:
        self._transport.request("DELETE", f"/projects/{project_id}/phases/{phase_id}")

    def move(self, project_id: str, phase_id: str, offset: int) -> None:
        self._transport.request(
            "POST", f"/projects/{project_id}/phases/{phase_id}/move", payload={"offset": offset}
        )
