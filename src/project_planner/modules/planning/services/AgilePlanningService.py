from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.Sprint import Sprint
from project_planner.modules.planning.entities.SprintStatus import SprintStatus
from project_planner.modules.planning.protocols.AgileRepository import AgileRepository


class AgilePlanningService:
    def __init__(self, repository: AgileRepository) -> None:
        self._repository = repository

    def list_items(self, project_id: str, section_id: str | None = None) -> Sequence[BacklogItem]:
        return self._repository.list_items(project_id, section_id)

    def add_item(
        self,
        project_id: str,
        title: str,
        description: str = "",
        priority: BacklogPriority = BacklogPriority.MEDIUM,
        assignee: str = "",
        section_id: str | None = None,
    ) -> BacklogItem:
        items = self.list_items(project_id, section_id)
        item = BacklogItem(
            project_id=project_id,
            section_id=section_id,
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            assignee=assignee.strip(),
            position=len(items),
        )
        self._repository.save_item(item)
        return item

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
        updated = item.revise(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            status=status,
            assignee=assignee.strip(),
        )
        self._repository.save_item(updated)
        return updated

    def move_item(
        self, project_id: str, item_id: str, offset: int, section_id: str | None = None
    ) -> None:
        items = list(self.list_items(project_id, section_id))
        index = next(index for index, item in enumerate(items) if item.id == item_id)
        target = max(0, min(len(items) - 1, index + offset))
        if target == index:
            return
        items[index], items[target] = items[target], items[index]
        for position, item in enumerate(items):
            self._repository.save_item(item.revise(position=position))

    def remove_item(self, item_id: str) -> None:
        self._repository.delete_item(item_id)

    def list_sprints(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return self._repository.list_sprints(project_id, section_id)

    def list_sprint_items(
        self,
        project_id: str,
        sprint_id: str,
        section_id: str | None = None,
    ) -> Sequence[BacklogItem]:
        return [
            item for item in self.list_items(project_id, section_id) if item.sprint_id == sprint_id
        ]

    def planned_sprints(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return [
            sprint
            for sprint in self.list_sprints(project_id, section_id)
            if sprint.status is not SprintStatus.COMPLETED
        ]

    def sprint_history(self, project_id: str, section_id: str | None = None) -> Sequence[Sprint]:
        return [
            sprint
            for sprint in self.list_sprints(project_id, section_id)
            if sprint.status is SprintStatus.COMPLETED
        ]

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
        sprint = Sprint(
            project_id,
            name.strip(),
            start_date,
            end_date,
            goal.strip(),
            section_id=section_id,
        )
        self._repository.save_sprint(sprint)
        selected = set(selected_item_ids)
        for item in self.list_items(project_id, section_id):
            if item.id in selected:
                self._repository.save_item(
                    item.revise(sprint_id=sprint.id, status=BacklogStatus.BACKLOG)
                )
        return sprint

    def complete_sprint(
        self, project_id: str, sprint_id: str, section_id: str | None = None
    ) -> None:
        sprint = next(
            (
                candidate
                for candidate in self.planned_sprints(project_id, section_id)
                if candidate.id == sprint_id
            ),
            None,
        )
        if sprint is None:
            raise LookupError(f"Sprint {sprint_id!r} does not exist in this context")
        for item in self.list_items(project_id, section_id):
            if item.sprint_id == sprint.id and item.status is not BacklogStatus.DONE:
                self._repository.save_item(
                    item.revise(sprint_id=None, status=BacklogStatus.BACKLOG)
                )
        self._repository.save_sprint(sprint.revise(status=SprintStatus.COMPLETED))
