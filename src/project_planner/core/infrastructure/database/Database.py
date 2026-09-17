from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from project_planner.core.infrastructure.database.MigrationManager import MigrationManager


class Database:
    def __init__(self, path: str | Path, database_url: str | None = None) -> None:
        self.path = Path(path)
        if database_url is None and self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        url = database_url or self._sqlite_url(self.path)
        parsed_url = make_url(url)
        options: dict[str, object] = {}
        if parsed_url.get_backend_name() == "sqlite":
            options["connect_args"] = {"check_same_thread": False}
            if parsed_url.database in (None, "", ":memory:"):
                options["poolclass"] = StaticPool
        self.engine: Engine = create_engine(url, **options)
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)
        self._session_factory = sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=Session
        )
        with self.engine.begin() as connection:
            MigrationManager(str(self.engine.url)).upgrade(connection)

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.new_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def new_session(self) -> Session:
        return self._session_factory()

    @staticmethod
    def _sqlite_url(path: Path) -> str:
        if path == Path(":memory:"):
            return "sqlite+pysqlite:///:memory:"
        return str(URL.create("sqlite+pysqlite", database=str(path.resolve())))

    @staticmethod
    def _enable_sqlite_foreign_keys(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
