from datetime import date

from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner_frontend.api.ApiTransport import ApiTransport


class ProjectWorkflowClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def create_project(
        self,
        title: str,
        *,
        description: str = "",
        status: ProjectStatus = ProjectStatus.IDEA,
        planning_method: PlanningMethod = PlanningMethod.CUSTOM,
        parent_id: str | None = None,
        category_id: str | None = None,
        start_date: date | None = None,
        target_date: date | None = None,
        owner: str = "",
        assignee: str = "",
        notes: str = "",
    ) -> Project:
        payload = {
            "title": title,
            "description": description,
            "status": status,
            "planning_method": planning_method,
            "parent_id": parent_id,
            "category_id": category_id,
            "start_date": start_date,
            "target_date": target_date,
            "owner": owner,
            "assignee": assignee,
            "notes": notes,
        }
        return self._transport.model(Project, "POST", "/projects", payload=payload)

    def update_project(self, project_id: str, **changes: object) -> Project:
        return self._transport.model(Project, "PUT", f"/projects/{project_id}", payload=changes)

    def reset_phase_plan(self, project_id: str) -> None:
        self._transport.request("POST", f"/projects/{project_id}/phase-plan/reset")
