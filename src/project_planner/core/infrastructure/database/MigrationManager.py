from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, inspect


class MigrationManager:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def upgrade(self, connection: Connection) -> None:
        config = self._config(connection)
        tables = set(inspect(connection).get_table_names())
        if "projects" in tables and "alembic_version" not in tables:
            command.stamp(config, "0001")
        command.upgrade(config, "head")

    def _config(self, connection: Connection) -> Config:
        migrations = Path(__file__).parent / "migrations"
        config = Config()
        config.set_main_option("script_location", str(migrations))
        config.set_main_option("sqlalchemy.url", self._database_url.replace("%", "%%"))
        config.attributes["connection"] = connection
        return config
