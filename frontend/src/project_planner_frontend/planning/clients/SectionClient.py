from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.PlanningSection import PlanningSection
from project_planner.modules.planning.entities.SectionItem import SectionItem
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner_frontend.api.ApiTransport import ApiTransport


class SectionClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def list_for_project(self, project_id: str) -> Sequence[PlanningSection]:
        return self._transport.model(
            list[PlanningSection], "GET", f"/projects/{project_id}/sections"
        )

    def add(
        self,
        project_id: str,
        name: str,
        section_type: SectionType,
        description: str = "",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> PlanningSection:
        return self._transport.model(
            PlanningSection,
            "POST",
            f"/projects/{project_id}/sections",
            payload={
                "name": name,
                "section_type": section_type,
                "description": description,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def require(self, section_id: str) -> PlanningSection:
        return self._transport.model(PlanningSection, "GET", f"/sections/{section_id}")

    def update(
        self,
        section_id: str,
        *,
        name: str,
        description: str,
        section_type: SectionType,
        start_date: date | None,
        end_date: date | None,
        status: SectionStatus,
    ) -> PlanningSection:
        return self._transport.model(
            PlanningSection,
            "PUT",
            f"/sections/{section_id}",
            payload={
                "name": name,
                "description": description,
                "section_type": section_type,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
            },
        )

    def move(self, project_id: str, section_id: str, offset: int) -> None:
        self._transport.request(
            "POST", f"/projects/{project_id}/sections/{section_id}/move", payload={"offset": offset}
        )

    def move_to(self, project_id: str, section_id: str, target_id: str) -> None:
        self._transport.request(
            "POST",
            f"/projects/{project_id}/sections/{section_id}/move-to",
            payload={"target_id": target_id},
        )

    def remove(self, section_id: str) -> None:
        self._transport.request("DELETE", f"/sections/{section_id}")

    def list_items(self, section_id: str) -> Sequence[SectionItem]:
        return self._transport.model(list[SectionItem], "GET", f"/sections/{section_id}/items")

    def add_item(
        self,
        section_id: str,
        title: str,
        description: str = "",
        assignee: str = "",
        status: SectionStatus = SectionStatus.NOT_STARTED,
        item_date: date | None = None,
    ) -> SectionItem:
        return self._transport.model(
            SectionItem,
            "POST",
            f"/sections/{section_id}/items",
            payload={
                "title": title,
                "description": description,
                "assignee": assignee,
                "status": status,
                "item_date": item_date,
            },
        )

    def update_item(
        self,
        item: SectionItem,
        *,
        title: str,
        description: str,
        assignee: str,
        status: SectionStatus,
        item_date: date | None,
    ) -> SectionItem:
        return self._transport.model(
            SectionItem,
            "PUT",
            f"/sections/{item.section_id}/items/{item.id}",
            payload={
                "title": title,
                "description": description,
                "assignee": assignee,
                "status": status,
                "item_date": item_date,
            },
        )

    def move_item(self, section_id: str, item_id: str, offset: int) -> None:
        self._transport.request(
            "POST", f"/sections/{section_id}/items/{item_id}/move", payload={"offset": offset}
        )

    def move_item_to(self, section_id: str, item_id: str, target_id: str) -> None:
        self._transport.request(
            "POST",
            f"/sections/{section_id}/items/{item_id}/move-to",
            payload={"target_id": target_id},
        )

    def remove_item(self, item_id: str) -> None:
        self._transport.request("DELETE", f"/section-items/{item_id}")
