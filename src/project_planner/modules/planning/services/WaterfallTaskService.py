from collections.abc import Sequence
from datetime import date

from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner.modules.planning.protocols.WaterfallTaskRepository import (
    WaterfallTaskRepository,
)


class WaterfallTaskService:
    def __init__(self, repository: WaterfallTaskRepository) -> None:
        self._repository = repository

    def list_for_phase(self, phase_id: str) -> Sequence[WaterfallTask]:
        return self._repository.list_for_phase(phase_id)

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
        task = WaterfallTask(
            phase_id=phase_id,
            title=title.strip(),
            description=description.strip(),
            assignee=assignee.strip(),
            start_date=start_date,
            due_date=due_date,
            status=status,
            position=len(self.list_for_phase(phase_id)),
        )
        self._repository.save(task)
        return task

    def update(self, task_id: str, **changes: object) -> WaterfallTask:
        task = self.require(task_id).revise(**changes)
        self._repository.save(task)
        return task

    def require(self, task_id: str) -> WaterfallTask:
        task = self._repository.get(task_id)
        if task is None:
            raise LookupError(f"Task {task_id!r} does not exist")
        return task

    def remove(self, task_id: str) -> None:
        task = self.require(task_id)
        self._repository.delete(task_id)
        for position, remaining in enumerate(self.list_for_phase(task.phase_id)):
            if remaining.position != position:
                self._repository.save(remaining.revise(position=position))
