from collections.abc import Sequence

from project_planner.modules.todos.entities.Todo import Todo
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner.modules.todos.entities.TodoStatus import TodoStatus
from project_planner_frontend.api.ApiTransport import ApiTransport


class TodoClient:
    def __init__(self, transport: ApiTransport) -> None:
        self._transport = transport

    def add(
        self,
        project_id: str,
        title: str,
        description: str = "",
        module: TodoModule = TodoModule.GENERAL,
        status: TodoStatus = TodoStatus.OPEN,
        phase_id: str | None = None,
    ) -> Todo:
        return self._transport.model(
            Todo,
            "POST",
            f"/projects/{project_id}/todos",
            payload={
                "title": title,
                "description": description,
                "module": module,
                "status": status,
                "phase_id": phase_id,
            },
        )

    def update(
        self, todo_id: str, *, title: str, description: str, module: TodoModule, status: TodoStatus
    ) -> Todo:
        return self._transport.model(
            Todo,
            "PUT",
            f"/todos/{todo_id}",
            payload={
                "title": title,
                "description": description,
                "module": module,
                "status": status,
            },
        )

    def list_for_project(self, project_id: str) -> Sequence[Todo]:
        return self._transport.model(list[Todo], "GET", f"/projects/{project_id}/todos")

    def list_for_context(
        self, project_id: str, module: TodoModule, phase_id: str | None = None
    ) -> Sequence[Todo]:
        return self._transport.model(
            list[Todo],
            "GET",
            f"/projects/{project_id}/todos",
            params={"module": module.value, "phase_id": phase_id},
        )

    def require(self, todo_id: str) -> Todo:
        return self._transport.model(Todo, "GET", f"/todos/{todo_id}")

    def remove(self, todo_id: str) -> None:
        self._transport.request("DELETE", f"/todos/{todo_id}")
