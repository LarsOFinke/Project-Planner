from collections.abc import Sequence

from sqlalchemy import case, delete, select

from project_planner.modules.todos.entities.Todo import Todo
from project_planner.modules.todos.entities.TodoModule import TodoModule
from project_planner.modules.todos.entities.TodoStatus import TodoStatus
from project_planner.shared.database.Database import Database
from project_planner.shared.database.models.TodoModel import TodoModel


class SQLAlchemyTodoRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def save(self, todo: Todo) -> None:
        with self._database.session() as session:
            session.merge(self._to_model(todo))

    def get(self, todo_id: str) -> Todo | None:
        with self._database.session() as session:
            model = session.get(TodoModel, todo_id)
            return self._to_domain(model) if model else None

    def list_for_project(self, project_id: str) -> Sequence[Todo]:
        return self._list(TodoModel.project_id == project_id)

    def list_for_context(
        self, project_id: str, module: TodoModule, phase_id: str | None = None
    ) -> Sequence[Todo]:
        return self._list(
            TodoModel.project_id == project_id,
            TodoModel.module == module.value,
            TodoModel.phase_id == phase_id,
        )

    def _list(self, *criteria: object) -> Sequence[Todo]:
        status_order = case(
            (TodoModel.status == TodoStatus.IN_PROGRESS.value, 0),
            (TodoModel.status == TodoStatus.OPEN.value, 1),
            else_=2,
        )
        statement = (
            select(TodoModel).where(*criteria).order_by(status_order, TodoModel.updated_at.desc())
        )
        with self._database.session() as session:
            return [self._to_domain(model) for model in session.scalars(statement)]

    def delete(self, todo_id: str) -> None:
        with self._database.session() as session:
            session.execute(delete(TodoModel).where(TodoModel.id == todo_id))

    @staticmethod
    def _to_model(todo: Todo) -> TodoModel:
        return TodoModel(
            id=todo.id,
            project_id=todo.project_id,
            title=todo.title,
            description=todo.description,
            module=todo.module.value,
            status=todo.status.value,
            phase_id=todo.phase_id,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
        )

    @staticmethod
    def _to_domain(model: TodoModel) -> Todo:
        return Todo(
            id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            module=TodoModule(model.module),
            status=TodoStatus(model.status),
            phase_id=model.phase_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
