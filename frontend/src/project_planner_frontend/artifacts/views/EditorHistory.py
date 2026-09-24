from typing import Generic, TypeVar

T = TypeVar("T")


class EditorHistory(Generic[T]):
    def __init__(self, limit: int = 50) -> None:
        self._limit = limit
        self._undo: list[T] = []
        self._redo: list[T] = []

    def reset(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def remember(self, current: T) -> None:
        self._undo.append(current)
        del self._undo[: -self._limit]
        self._redo.clear()

    def undo(self, current: T) -> T | None:
        if not self._undo:
            return None
        self._redo.append(current)
        return self._undo.pop()

    def redo(self, current: T) -> T | None:
        if not self._redo:
            return None
        self._undo.append(current)
        return self._redo.pop()
