from typing import Annotated

from fastapi import APIRouter, Body, Query

from project_planner.api.collaboration.dtos.ProjectLinkTarget import ProjectLinkTarget
from project_planner.api.collaboration.dtos.ResolvedProjectLink import ResolvedProjectLink
from project_planner.api.collaboration.queries.CollaborationQueryService import (
    CollaborationQueryService,
)
from project_planner.modules.links.entities.ProjectLink import ProjectLink
from project_planner.modules.links.services.ProjectLinkService import ProjectLinkService
from project_planner.modules.resources.entities.ResourceLink import ResourceLink
from project_planner.modules.resources.entities.ResourceLinkKind import ResourceLinkKind
from project_planner.modules.resources.services.ResourceLinkService import ResourceLinkService
from project_planner.modules.todos.entities.Todo import Todo
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner.modules.todos.entities.TodoStatus import TodoStatus
from project_planner.modules.todos.services.TodoService import TodoService


class CollaborationController:
    def __init__(
        self,
        links: ProjectLinkService,
        queries: CollaborationQueryService,
        resources: ResourceLinkService,
        todos: TodoService,
    ) -> None:
        self._links = links
        self._queries = queries
        self._resources = resources
        self._todos = todos
        self.router = APIRouter(tags=["collaboration"])
        self._register_routes()

    def _register_routes(self) -> None:
        self._register_todo_routes()
        self._register_project_link_routes()
        self._register_resource_routes()

    def _register_todo_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/todos",
            self.list_todos,
            methods=["GET"],
            response_model=list[Todo],
        )
        routes.add_api_route(
            "/projects/{project_id}/todos",
            self.add_todo,
            methods=["POST"],
            status_code=201,
            response_model=Todo,
        )
        routes.add_api_route(
            "/todos/{todo_id}", self.get_todo, methods=["GET"], response_model=Todo
        )
        routes.add_api_route(
            "/todos/{todo_id}", self.update_todo, methods=["PUT"], response_model=Todo
        )
        routes.add_api_route(
            "/todos/{todo_id}", self.remove_todo, methods=["DELETE"], status_code=204
        )

    def _register_project_link_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/project-links",
            self.list_project_links,
            methods=["GET"],
            response_model=list[ProjectLink] | list[ResolvedProjectLink],
        )
        routes.add_api_route(
            "/projects/{project_id}/project-link-targets",
            self.project_link_targets,
            methods=["GET"],
            response_model=list[ProjectLinkTarget],
        )
        routes.add_api_route(
            "/projects/{project_id}/project-links",
            self.add_project_link,
            methods=["POST"],
            status_code=201,
            response_model=ProjectLink,
        )
        routes.add_api_route(
            "/project-links",
            self.remove_project_link,
            methods=["DELETE"],
            status_code=204,
        )

    def _register_resource_routes(self) -> None:
        routes = self.router
        routes.add_api_route(
            "/projects/{project_id}/resources",
            self.list_resources,
            methods=["GET"],
            response_model=list[ResourceLink],
        )
        routes.add_api_route(
            "/projects/{project_id}/resources",
            self.add_resource,
            methods=["POST"],
            status_code=201,
            response_model=ResourceLink,
        )
        routes.add_api_route(
            "/resources/{link_id}",
            self.remove_resource,
            methods=["DELETE"],
            status_code=204,
        )

    def list_todos(
        self,
        project_id: str,
        module: Annotated[TodoModule | None, Query()] = None,
        phase_id: str | None = None,
    ):
        return (
            self._todos.list_for_project(project_id)
            if module is None
            else self._todos.list_for_context(project_id, module, phase_id)
        )

    def add_todo(
        self,
        project_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()] = "",
        module: Annotated[TodoModule, Body()] = TodoModule.GENERAL,
        status: Annotated[TodoStatus, Body()] = TodoStatus.OPEN,
        phase_id: Annotated[str | None, Body()] = None,
    ):
        return self._todos.add(project_id, title, description, module, status, phase_id)

    def get_todo(self, todo_id: str):
        return self._todos.require(todo_id)

    def update_todo(
        self,
        todo_id: str,
        title: Annotated[str, Body()],
        description: Annotated[str, Body()],
        module: Annotated[TodoModule, Body()],
        status: Annotated[TodoStatus, Body()],
    ):
        return self._todos.update(
            todo_id, title=title, description=description, module=module, status=status
        )

    def remove_todo(self, todo_id: str) -> None:
        self._todos.remove(todo_id)

    def list_project_links(self, project_id: str, resolved: bool = False):
        return (
            self._queries.list_resolved(project_id)
            if resolved
            else self._links.list_for_project(project_id)
        )

    def project_link_targets(self, project_id: str):
        return self._queries.available_targets(project_id)

    def add_project_link(
        self,
        project_id: str,
        target_id: Annotated[str, Body()],
        relation: Annotated[str, Body()] = "related",
        note: Annotated[str, Body()] = "",
    ):
        return self._links.add(project_id, target_id, relation, note)

    def remove_project_link(self, source_id: str, target_id: str, relation: str) -> None:
        self._links.remove(ProjectLink(source_id, target_id, relation))

    def list_resources(
        self,
        project_id: str,
        kind: Annotated[ResourceLinkKind | None, Query()] = None,
    ):
        return self._resources.list_for_project(project_id, kind)

    def add_resource(
        self,
        project_id: str,
        title: Annotated[str, Body()],
        target: Annotated[str, Body()],
        kind: Annotated[ResourceLinkKind, Body()],
    ):
        return self._resources.add(project_id, title, target, kind)

    def remove_resource(self, link_id: str) -> None:
        self._resources.remove(link_id)
