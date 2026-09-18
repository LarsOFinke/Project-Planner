from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.Sprint import Sprint
from project_planner_frontend.api.ApiTransport import ApiTransport


class AgileClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def list_items(self, project_id: str, section_id: str | None = None) -> Sequence[BacklogItem]:
        return self._transport.model(
            list[BacklogItem],
            "GET",
            f"/projects/{project_id}/backlog-items",
            params={"section_id": section_id},
        )

    def add_item(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: BacklogPriority = BacklogPriority.MEDIUM,
        assignee: str = "",
        section_id: str | None = None,
    ) -> BacklogItem:
        return self._transport.model(
            BacklogItem,
            "POST",
            f"/projects/{project_id}/backlog-items",
            payload={
                "title": title,
                "description": description,
                "priority": priority,
                "assignee": assignee,
                "section_id": section_id,
            },
        )

    def update_item(
        self,
        item: BacklogItem,
        *,
        title: str,
        description: str,
        priority: BacklogPriority,
        status: BacklogStatus,
        assignee: str,
    ) -> BacklogItem:
        return self._transport.model(
            BacklogItem,
            "PUT",
            f"/projects/{item.project_id}/backlog-items/{item.id}",
            payload={
                "title": title,
                "description": description,
                "priority": priority,
                "status": status,
                "assignee": assignee,
                "section_id": item.section_id,
            },
        )

    def move_item(
        self, project_id: str, item_id: str, offset: int, section_id: str | None = None
    ) -> None:
        self._transport.request(
            "POST",
            f"/projects/{project_id}/backlog-items/{item_id}/move",
            payload={"offset": offset},
            params={"section_id": section_id},
        )

    def remove_item(self, item_id: str) -> None:
        self._transport.request("DELETE", f"/backlog-items/{item_id}")

    def list_sprints(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return self._sprints(project_id, section_id)

    def planned_sprints(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return self._sprints(project_id, section_id, "planned")

    def sprint_history(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return self._sprints(project_id, section_id, "completed")

    def _sprints(
        self, project_id: str, section_id: str | None, state: str | None = None
    ) -> Sequence[Sprint]:
        return self._transport.model(
            list[Sprint],
            "GET",
            f"/projects/{project_id}/sprints",
            params={"section_id": section_id, "state": state},
        )

    def list_sprint_items(
        self, project_id: str, sprint_id: str, section_id: str | None = None
    ) -> Sequence[BacklogItem]:
        return self._transport.model(
            list[BacklogItem],
            "GET",
            f"/projects/{project_id}/sprints/{sprint_id}/items",
            params={"section_id": section_id},
        )

    def add_sprint(
        self,
        project_id: str,
        name: str,
        start_date: date,
        end_date: date,
        goal: str,
        selected_item_ids: Sequence[str],
        section_id: str | None = None,
    ) -> Sprint:
        return self._transport.model(
            Sprint,
            "POST",
            f"/projects/{project_id}/sprints",
            payload={
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "goal": goal,
                "selected_item_ids": list(selected_item_ids),
                "section_id": section_id,
            },
        )

    def complete_sprint(
        self, project_id: str, sprint_id: str, section_id: str | None = None
    ) -> None:
        self._transport.request(
            "POST",
            f"/projects/{project_id}/sprints/{sprint_id}/complete",
            payload={"section_id": section_id},
        )
