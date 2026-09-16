import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from project_planner.core.infrastructure.database.schema import SCHEMA, migrate_schema


class SQLiteDatabase:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._memory_connection: sqlite3.Connection | None = None
        if self.path == Path(":memory:"):
            self._memory_connection = self._new_connection()
        with self.connection() as connection:
            connection.executescript(SCHEMA)
            migrate_schema(connection)

    def _new_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._memory_connection or self._new_connection()
        try:
            with connection:
                yield connection
        finally:
            if self._memory_connection is None:
                connection.close()
