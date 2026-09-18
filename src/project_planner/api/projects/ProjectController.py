from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, Query
from fastapi import status as http_status

from project_planner.api.projects.dtos.ProjectChoice import ProjectChoice
from project_planner.api.projects.dtos.ProjectDirectorySection import ProjectDirectorySection
from project_planner.api.projects.dtos.ProjectOverview import ProjectOverview
from project_planner.api.projects.dtos.ProjectTreeItem import ProjectTreeItem
from project_planner.api.projects.queries.ProjectQueryService import ProjectQueryService
from project_planner.modules.projects.entities.PlanningMethod import PlanningMethod
from project_planner.modules.projects.entities.Project import Project
from project_planner.modules.projects.entities.ProjectCategory import ProjectCategory
from project_planner.modules.projects.entities.ProjectStatus import ProjectStatus
from project_planner.modules.projects.services.ProjectCategoryService import ProjectCategoryService
from project_planner.modules.projects.services.ProjectService import ProjectService
from project_planner.modules.projects.services.ProjectWorkflowService import ProjectWorkflowService


class ProjectController:
    def __init__(
        self,
        projects: ProjectService,
        categories: ProjectCategoryService,
        queries: ProjectQueryService,
        workflows: ProjectWorkflowService,
    ) -> None:
        self._projects = projects
        self._categories = categories
        self._queries = queries
        self._workflows = workflows
        self.router = APIRouter(tags=["projects"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_project_routes()
        self._register_project_query_routes()
        self._register_category_routes()

    def _register_project_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects", self.list_projects, methods=["GET"], response_model=list[Project]
        )
        routes.add_api_route(
            "/projects",
            self.create_project,
            methods=["POST"],
            status_code=http_status.HTTP_201_CREATED,
            response_model=Project,
        )
        routes.add_api_route(
            "/projects/{project_id}", self.get_project, methods=["GET"], response_model=Project
        )
        routes.add_api_route(
            "/projects/{project_id}", self.update_project, methods=["PUT"], response_model=Project
        )
        routes.add_api_route(
            "/projects/{project_id}",
            self.delete_project,
            methods=["DELETE"],
            status_code=http_status.HTTP_204_NO_CONTENT,
        )
        routes.add_api_route(
            "/projects/{project_id}/category",
            self.assign_category,
            methods=["PUT"],
            response_model=Project,
        )
        routes.add_api_route(
            "/projects/{project_id}/phase-plan/reset",
            self.reset_phase_plan,
            methods=["POST"],
            status_code=http_status.HTTP_204_NO_CONTENT,
        )

    def _register_project_query_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/overview",
            self.overview,
            methods=["GET"],
            response_model=ProjectOverview,
        )
        routes.add_api_route(
            "/project-choices", self.choices, methods=["GET"], response_model=list[ProjectChoice]
        )
        routes.add_api_route(
            "/project-tree", self.tree, methods=["GET"], response_model=list[ProjectTreeItem]
        )
        routes.add_api_route(
            "/project-directory",
            self.directory,
            methods=["GET"],
            response_model=list[ProjectDirectorySection],
        )

    def _register_category_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/project-categories",
            self.list_categories,
            methods=["GET"],
            response_model=list[ProjectCategory],
        )
        routes.add_api_route(
            "/project-categories",
            self.create_category,
            methods=["POST"],
            status_code=http_status.HTTP_201_CREATED,
            response_model=ProjectCategory,
        )
        routes.add_api_route(
            "/project-categories/{category_id}",
            self.get_category,
            methods=["GET"],
            response_model=ProjectCategory,
        )
        routes.add_api_route(
            "/project-categories/{category_id}",
            self.delete_category,
            methods=["DELETE"],
            status_code=http_status.HTTP_204_NO_CONTENT,
        )

    def list_projects(self):
        return self._projects.list_all()

    def get_project(self, project_id: str):
        return self._projects.require(project_id)

    def delete_project(self, project_id: str) -> None:
        self._projects.delete(project_id)

    def assign_category(
        self,
        project_id: str,
        category_id: Annotated[str | None, Body(embed=True)] = None,
    ):
        return self._projects.assign_category(project_id, category_id)

    def create_project(
        self,
        title: Annotated[str, Body()],
        *,
        description: Annotated[str, Body()] = "",
        status: Annotated[ProjectStatus, Body()] = ProjectStatus.IDEA,
        planning_method: Annotated[PlanningMethod, Body()] = PlanningMethod.CUSTOM,
        parent_id: Annotated[str | None, Body()] = None,
        category_id: Annotated[str | None, Body()] = None,
        start_date: Annotated[date | None, Body()] = None,
        target_date: Annotated[date | None, Body()] = None,
        owner: Annotated[str, Body()] = "",
        assignee: Annotated[str, Body()] = "",
        notes: Annotated[str, Body()] = "",
    ):
        return self._workflows.create_project(
            title,
            description=description,
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
            category_id=category_id,
            start_date=start_date,
            target_date=target_date,
            owner=owner,
            assignee=assignee,
            notes=notes,
        )

    def update_project(
        self,
        project_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()],
        status: Annotated[ProjectStatus, Body()],
        planning_method: Annotated[PlanningMethod, Body()],
        parent_id: Annotated[str | None, Body()] = None,
        start_date: Annotated[date | None, Body()] = None,
        target_date: Annotated[date | None, Body()] = None,
        owner: Annotated[str, Body()] = "",
        assignee: Annotated[str, Body()] = "",
        notes: Annotated[str, Body()] = "",
    ):
        return self._workflows.update_project(
            project_id,
            title=title,
            description=description,
            status=status,
            planning_method=planning_method,
            parent_id=parent_id,
            start_date=start_date,
            target_date=target_date,
            owner=owner,
            assignee=assignee,
            notes=notes,
        )

    def reset_phase_plan(self, project_id: str) -> None:
        self._workflows.reset_phase_plan(project_id)

    def overview(self, project_id: str):
        return self._queries.get_overview(project_id)

    def choices(self, exclude_id: Annotated[str | None, Query()] = None):
        return self._queries.list_choices(exclude_id=exclude_id)

    def tree(self):
        return self._queries.list_tree()

    def directory(self):
        return self._queries.list_directory()

    def list_categories(self):
        return self._categories.list_all()

    def create_category(self, name: Annotated[str, Body(embed=True)]):
        return self._categories.create(name)

    def get_category(self, category_id: str):
        return self._categories.require(category_id)

    def delete_category(self, category_id: str) -> None:
        self._categories.delete(category_id)
