from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner_frontend.api.ApiTransport import ApiTransport


class WaterfallTaskClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def list_for_phase(self, phase_id: str) -> Sequence[WaterfallTask]:
        return self._transport.model(list[WaterfallTask], "GET", f"/phases/{phase_id}/tasks")

    def add(
        self,
        phase_id: str,
        title: str,
        description: str = "",
        assignee: str = "",
        start_date: date | None = None,
        due_date: date | None = None,
        status: WaterfallTaskStatus = WaterfallTaskStatus.NOT_STARTED,
    ) -> WaterfallTask:
        return self._transport.model(
            WaterfallTask,
            "POST",
            f"/phases/{phase_id}/tasks",
            payload={
                "title": title,
                "description": description,
                "assignee": assignee,
                "start_date": start_date,
                "due_date": due_date,
                "status": status,
            },
        )

    def update(self, task_id: str, **changes: object) -> WaterfallTask:
        return self._transport.model(WaterfallTask, "PATCH", f"/tasks/{task_id}", payload=changes)

    def require(self, task_id: str) -> WaterfallTask:
        return self._transport.model(WaterfallTask, "GET", f"/tasks/{task_id}")

    def remove(self, task_id: str) -> None:
        self._transport.request("DELETE", f"/tasks/{task_id}")
