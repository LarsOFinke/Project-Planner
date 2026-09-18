from collections.abc import Sequence
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, Query, Response

from project_planner.modules.planning.entities.BacklogItem import BacklogItem
from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus
from project_planner.modules.planning.entities.Phase import Phase
from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus
from project_planner.modules.planning.entities.PlanningSection import PlanningSection
from project_planner.modules.planning.entities.SectionItem import SectionItem
from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType
from project_planner.modules.planning.entities.Sprint import Sprint
from project_planner.modules.planning.entities.WaterfallTask import WaterfallTask
from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus
from project_planner.modules.planning.services.AgilePlanningService import AgilePlanningService
from project_planner.modules.planning.services.PhaseService import PhaseService
from project_planner.modules.planning.services.SectionService import SectionService
from project_planner.modules.planning.services.WaterfallTaskService import WaterfallTaskService


class PlanningController:
    def __init__(
        self,
        agile: AgilePlanningService,
        phases: PhaseService,
        sections: SectionService,
        tasks: WaterfallTaskService,
    ) -> None:
        self._agile = agile
        self._phases = phases
        self._sections = sections
        self._tasks = tasks
        self.router = APIRouter(tags=["planning"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_backlog_routes()
        self._register_sprint_routes()
        self._register_phase_routes()
        self._register_section_routes()
        self._register_section_item_routes()
        self._register_task_routes()

    def _register_backlog_routes(self) -> None:
        route_definitions = (
            (
                "/projects/{project_id}/backlog-items",
                self.list_backlog_items,
                ["GET"],
                None,
                list[BacklogItem],
            ),
            (
                "/projects/{project_id}/backlog-items",
                self.add_backlog_item,
                ["POST"],
                201,
                BacklogItem,
            ),
            (
                "/projects/{project_id}/backlog-items/{item_id}",
                self.update_backlog_item,
                ["PUT"],
                None,
                BacklogItem,
            ),
            (
                "/projects/{project_id}/backlog-items/{item_id}/move",
                self.move_backlog_item,
                ["POST"],
                204,
                None,
            ),
            ("/backlog-items/{item_id}", self.remove_backlog_item, ["DELETE"], 204, None),
        )
        self._register_route_group(route_definitions)

    def _register_sprint_routes(self) -> None:
        route_definitions = (
            ("/projects/{project_id}/sprints", self.list_sprints, ["GET"], None, list[Sprint]),
            (
                "/projects/{project_id}/sprints/{sprint_id}/items",
                self.list_sprint_items,
                ["GET"],
                None,
                list[BacklogItem],
            ),
            ("/projects/{project_id}/sprints", self.add_sprint, ["POST"], 201, Sprint),
            (
                "/projects/{project_id}/sprints/{sprint_id}/complete",
                self.complete_sprint,
                ["POST"],
                204,
                None,
            ),
        )
        self._register_route_group(route_definitions)

    def _register_phase_routes(self) -> None:
        route_definitions = (
            ("/projects/{project_id}/phases", self.list_phases, ["GET"], None, list[Phase]),
            ("/projects/{project_id}/phases", self.add_phase, ["POST"], 201, Phase),
            ("/projects/{project_id}/phases/{phase_id}", self.update_phase, ["PUT"], None, Phase),
            ("/projects/{project_id}/phases/{phase_id}/move", self.move_phase, ["POST"], 204, None),
            ("/projects/{project_id}/phases/{phase_id}", self.remove_phase, ["DELETE"], 204, None),
            (
                "/projects/{project_id}/waterfall-template",
                self.initialize_waterfall,
                ["POST"],
                None,
                list[Phase],
            ),
            (
                "/projects/{project_id}/waterfall-template",
                self.reset_waterfall,
                ["PUT"],
                None,
                list[Phase],
            ),
        )
        self._register_route_group(route_definitions)

    def _register_section_routes(self) -> None:
        route_definitions = (
            (
                "/projects/{project_id}/sections",
                self.list_sections,
                ["GET"],
                None,
                list[PlanningSection],
            ),
            ("/projects/{project_id}/sections", self.add_section, ["POST"], 201, PlanningSection),
            ("/sections/{section_id}", self.get_section, ["GET"], None, PlanningSection),
            ("/sections/{section_id}", self.update_section, ["PUT"], None, PlanningSection),
            (
                "/projects/{project_id}/sections/{section_id}/move",
                self.move_section,
                ["POST"],
                204,
                None,
            ),
            ("/sections/{section_id}", self.remove_section, ["DELETE"], 204, None),
        )
        self._register_route_group(route_definitions)

    def _register_section_item_routes(self) -> None:
        route_definitions = (
            (
                "/sections/{section_id}/items",
                self.list_section_items,
                ["GET"],
                None,
                list[SectionItem],
            ),
            ("/sections/{section_id}/items", self.add_section_item, ["POST"], 201, SectionItem),
            (
                "/sections/{section_id}/items/{item_id}",
                self.update_section_item,
                ["PUT"],
                None,
                SectionItem,
            ),
            (
                "/sections/{section_id}/items/{item_id}/move",
                self.move_section_item,
                ["POST"],
                204,
                None,
            ),
            ("/section-items/{item_id}", self.remove_section_item, ["DELETE"], 204, None),
        )
        self._register_route_group(route_definitions)

    def _register_task_routes(self) -> None:
        route_definitions = (
            ("/phases/{phase_id}/tasks", self.list_tasks, ["GET"], None, list[WaterfallTask]),
            ("/phases/{phase_id}/tasks", self.add_task, ["POST"], 201, WaterfallTask),
            ("/tasks/{task_id}", self.get_task, ["GET"], None, WaterfallTask),
            ("/tasks/{task_id}", self.update_task, ["PATCH"], None, WaterfallTask),
            ("/tasks/{task_id}", self.remove_task, ["DELETE"], 204, None),
        )
        self._register_route_group(route_definitions)

    def _register_route_group(self, route_definitions: tuple[tuple[object, ...], ...]) -> None:
        for path, endpoint, methods, status_code, response_model in route_definitions:
            options = {"methods": methods}
            if status_code is not None:
                options["status_code"] = status_code
            if response_model is not None:
                options["response_model"] = response_model
            self.router.add_api_route(path, endpoint, **options)

    def list_backlog_items(self, project_id: str, section_id: str | None = None):
        return self._agile.list_items(project_id, section_id)

    def add_backlog_item(
        self,
        project_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()] = "",
        priority: Annotated[BacklogPriority, Body()] = BacklogPriority.MEDIUM,
        assignee: Annotated[str, Body()] = "",
        section_id: Annotated[str | None, Body()] = None,
    ):
        return self._agile.add_item(project_id, title, description, priority, assignee, section_id)

    def update_backlog_item(
        self,
        project_id: str,
        item_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()],
        priority: Annotated[BacklogPriority, Body()],
        item_status: Annotated[BacklogStatus, Body(alias="status")],
        assignee: Annotated[str, Body()],
        section_id: Annotated[str | None, Body()] = None,
    ):
        item = self._find(self._agile.list_items(project_id, section_id), item_id, "Backlog item")
        return self._agile.update_item(
            item,
            title=title,
            description=description,
            priority=priority,
            status=item_status,
            assignee=assignee,
        )

    def move_backlog_item(
        self,
        project_id: str,
        item_id: str,
        offset: Annotated[int, Body(embed=True)],
        section_id: Annotated[str | None, Query()] = None,
    ) -> Response:
        self._agile.move_item(project_id, item_id, offset, section_id)
        return Response(status_code=204)

    def remove_backlog_item(self, item_id: str) -> Response:
        self._agile.remove_item(item_id)
        return Response(status_code=204)

    def list_sprints(
        self,
        project_id: str,
        section_id: str | None = None,
        state: Annotated[str | None, Query(pattern="^(planned|completed)?$")] = None,
    ):
        if state == "planned":
            return self._agile.planned_sprints(project_id, section_id)
        if state == "completed":
            return self._agile.sprint_history(project_id, section_id)
        return self._agile.list_sprints(project_id, section_id)

    def list_sprint_items(self, project_id: str, sprint_id: str, section_id: str | None = None):
        return self._agile.list_sprint_items(project_id, sprint_id, section_id)

    def add_sprint(
        self,
        project_id: str,
        name: Annotated[str, Body()],
        start_date: Annotated[date, Body()],
        end_date: Annotated[date, Body()],
        goal: Annotated[str, Body()],
        selected_item_ids: Annotated[list[str], Body()],
        section_id: Annotated[str | None, Body()] = None,
    ):
        return self._agile.add_sprint(
            project_id, name, start_date, end_date, goal, selected_item_ids, section_id
        )

    def complete_sprint(
        self,
        project_id: str,
        sprint_id: str,
        section_id: Annotated[str | None, Body(embed=True)] = None,
    ) -> Response:
        self._agile.complete_sprint(project_id, sprint_id, section_id)
        return Response(status_code=204)

    def list_phases(self, project_id: str, section_id: str | None = None):
        return self._phases.list_for_context(project_id, section_id)

    def add_phase(
        self,
        project_id: str,
        name: Annotated[str, Body()],
        description: Annotated[str, Body()] = "",
        phase_status: Annotated[PhaseStatus, Body(alias="status")] = PhaseStatus.NOT_STARTED,
        start_date: Annotated[date | None, Body()] = None,
        end_date: Annotated[date | None, Body()] = None,
        section_id: Annotated[str | None, Body()] = None,
    ):
        return self._phases.add(
            project_id, name, description, phase_status, start_date, end_date, section_id
        )

    def update_phase(
        self,
        project_id: str,
        phase_id: str,
        name: Annotated[str, Body()],
        description: Annotated[str, Body()],
        phase_status: Annotated[PhaseStatus | None, Body(alias="status")] = None,
        start_date: Annotated[date | None, Body()] = None,
        end_date: Annotated[date | None, Body()] = None,
    ):
        return self._phases.update(
            phase_id, project_id, name, description, phase_status, start_date, end_date
        )

    def move_phase(
        self,
        project_id: str,
        phase_id: str,
        offset: Annotated[int, Body(embed=True)],
    ) -> Response:
        self._phases.move(project_id, phase_id, offset)
        return Response(status_code=204)

    def remove_phase(self, project_id: str, phase_id: str) -> Response:
        self._phases.remove(project_id, phase_id)
        return Response(status_code=204)

    def initialize_waterfall(
        self, project_id: str, section_id: Annotated[str | None, Body(embed=True)] = None
    ):
        return self._phases.initialize_waterfall(project_id, section_id)

    def reset_waterfall(
        self, project_id: str, section_id: Annotated[str | None, Body(embed=True)] = None
    ):
        return self._phases.reset_waterfall(project_id, section_id)

    def list_sections(self, project_id: str):
        return self._sections.list_for_project(project_id)

    def add_section(
        self,
        project_id: str,
        name: Annotated[str, Body()],
        section_type: Annotated[SectionType, Body()],
        description: Annotated[str, Body()] = "",
        start_date: Annotated[date | None, Body()] = None,
        end_date: Annotated[date | None, Body()] = None,
    ):
        return self._sections.add(project_id, name, section_type, description, start_date, end_date)

    def get_section(self, section_id: str):
        return self._sections.require(section_id)

    def update_section(
        self,
        section_id: str,
        name: Annotated[str, Body()],
        description: Annotated[str, Body()],
        section_type: Annotated[SectionType, Body()],
        section_status: Annotated[SectionStatus, Body(alias="status")] = SectionStatus.NOT_STARTED,
        start_date: Annotated[date | None, Body()] = None,
        end_date: Annotated[date | None, Body()] = None,
    ):
        return self._sections.update(
            section_id,
            name=name,
            description=description,
            section_type=section_type,
            start_date=start_date,
            end_date=end_date,
            status=section_status,
        )

    def move_section(
        self,
        project_id: str,
        section_id: str,
        offset: Annotated[int, Body(embed=True)],
    ) -> Response:
        self._sections.move(project_id, section_id, offset)
        return Response(status_code=204)

    def remove_section(self, section_id: str) -> Response:
        self._sections.remove(section_id)
        return Response(status_code=204)

    def list_section_items(self, section_id: str):
        return self._sections.list_items(section_id)

    def add_section_item(
        self,
        section_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()] = "",
        assignee: Annotated[str, Body()] = "",
        item_status: Annotated[SectionStatus, Body(alias="status")] = SectionStatus.NOT_STARTED,
        item_date: Annotated[date | None, Body()] = None,
    ):
        return self._sections.add_item(
            section_id, title, description, assignee, item_status, item_date
        )

    def update_section_item(
        self,
        section_id: str,
        item_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()],
        assignee: Annotated[str, Body()],
        item_status: Annotated[SectionStatus, Body(alias="status")],
        item_date: Annotated[date | None, Body()] = None,
    ):
        item = self._find(self._sections.list_items(section_id), item_id, "Section item")
        return self._sections.update_item(
            item,
            title=title,
            description=description,
            assignee=assignee,
            status=item_status,
            item_date=item_date,
        )

    def move_section_item(
        self,
        section_id: str,
        item_id: str,
        offset: Annotated[int, Body(embed=True)],
    ) -> Response:
        self._sections.move_item(section_id, item_id, offset)
        return Response(status_code=204)

    def remove_section_item(self, item_id: str) -> Response:
        self._sections.remove_item(item_id)
        return Response(status_code=204)

    def list_tasks(self, phase_id: str):
        return self._tasks.list_for_phase(phase_id)

    def add_task(
        self,
        phase_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()] = "",
        assignee: Annotated[str, Body()] = "",
        start_date: Annotated[date | None, Body()] = None,
        due_date: Annotated[date | None, Body()] = None,
        task_status: Annotated[
            WaterfallTaskStatus, Body(alias="status")
        ] = WaterfallTaskStatus.NOT_STARTED,
    ):
        return self._tasks.add(
            phase_id, title, description, assignee, start_date, due_date, task_status
        )

    def get_task(self, task_id: str):
        return self._tasks.require(task_id)

    def update_task(
        self,
        task_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()],
        assignee: Annotated[str, Body()],
        task_status: Annotated[
            WaterfallTaskStatus, Body(alias="status")
        ] = WaterfallTaskStatus.NOT_STARTED,
        start_date: Annotated[date | None, Body()] = None,
        due_date: Annotated[date | None, Body()] = None,
    ):
        return self._tasks.update(
            task_id,
            title=title,
            description=description,
            assignee=assignee,
            start_date=start_date,
            due_date=due_date,
            status=task_status,
        )

    def remove_task(self, task_id: str) -> Response:
        self._tasks.remove(task_id)
        return Response(status_code=204)

    @staticmethod
    def _find(values: Sequence[BacklogItem] | Sequence[SectionItem], value_id: str, label: str):
        match = next((value for value in values if value.id == value_id), None)
        if match is None:
            raise LookupError(f"{label} {value_id!r} does not exist")
        return match
