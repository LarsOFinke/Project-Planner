from collections.abc import Sequence

from project_planner.core.domain.todos.Todo import Todo
from project_planner.core.domain.todos.TodoModule import TodoModule
from project_planner.core.domain.todos.TodoStatus import TodoStatus
from project_planner.core.ports.TodoRepository import TodoRepository


class TodoService:
    def __init__(self, todos: TodoRepository) -> None:
        self._todos = todos

    def add(
        self,
        project_id: str,
        title: str,
        description: str = "",
        module: TodoModule = TodoModule.GENERAL,
        status: TodoStatus = TodoStatus.OPEN,
        phase_id: str | None = None,
    ) -> Todo:
        todo = Todo(
            project_id=project_id,
            title=title.strip(),
            description=description.strip(),
            module=module,
            status=status,
            phase_id=phase_id,
        )
        self._todos.save(todo)
        return todo

    def update(
        self,
        todo_id: str,
        *,
        title: str,
        description: str,
        module: TodoModule,
        status: TodoStatus,
    ) -> Todo:
        todo = self.require(todo_id).revise(
            title=title.strip(),
            description=description.strip(),
            module=module,
            status=status,
        )
        self._todos.save(todo)
        return todo

    def list_for_project(self, project_id: str) -> Sequence[Todo]:
        return self._todos.list_for_project(project_id)

    def list_for_context(
        self,
        project_id: str,
        module: TodoModule,
        phase_id: str | None = None,
    ) -> Sequence[Todo]:
        return self._todos.list_for_context(project_id, module, phase_id)

    def require(self, todo_id: str) -> Todo:
        todo = self._todos.get(todo_id)
        if todo is None:
            raise LookupError(f"To-do {todo_id!r} does not exist")
        return todo

    def remove(self, todo_id: str) -> None:
        self.require(todo_id)
        self._todos.delete(todo_id)
