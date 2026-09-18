import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

_NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade() -> None:
    _replace_project_foreign_key(ondelete="CASCADE")


def downgrade() -> None:
    _replace_project_foreign_key(ondelete=None)


def _replace_project_foreign_key(*, ondelete: str | None) -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "phases" not in tables:
        return
    if bind.dialect.name == "sqlite":
        backed_up_tables = _backup_phase_dependents(tables)
        _rebuild_sqlite_phase_foreign_key(ondelete)
        _restore_phase_dependents(backed_up_tables)
        return

    project_key = next(
        foreign_key
        for foreign_key in sa.inspect(bind).get_foreign_keys("phases")
        if foreign_key["constrained_columns"] == ["project_id"]
    )
    with op.batch_alter_table("phases") as batch:
        batch.drop_constraint(project_key["name"], type_="foreignkey")
        batch.create_foreign_key(
            "fk_phases_project_id_projects",
            "projects",
            ["project_id"],
            ["id"],
            ondelete=ondelete,
        )


def _rebuild_sqlite_phase_foreign_key(ondelete: str | None) -> None:
    with op.batch_alter_table(
        "phases",
        naming_convention=_NAMING_CONVENTION,
        recreate="always",
    ) as batch:
        batch.drop_constraint(
            "fk_phases_project_id_projects",
            type_="foreignkey",
        )
        batch.create_foreign_key(
            "fk_phases_project_id_projects",
            "projects",
            ["project_id"],
            ["id"],
            ondelete=ondelete,
        )


def _backup_phase_dependents(tables: set[str]) -> tuple[str, ...]:
    backed_up: list[str] = []
    if "todos" in tables:
        op.execute(sa.text("DROP TABLE IF EXISTS temp._migration_0011_todos"))
        op.execute(
            sa.text(
                "CREATE TEMPORARY TABLE _migration_0011_todos AS "
                "SELECT * FROM todos WHERE phase_id IS NOT NULL"
            )
        )
        backed_up.append("todos")
    if "waterfall_tasks" in tables:
        op.execute(sa.text("DROP TABLE IF EXISTS temp._migration_0011_tasks"))
        op.execute(
            sa.text("CREATE TEMPORARY TABLE _migration_0011_tasks AS SELECT * FROM waterfall_tasks")
        )
        backed_up.append("waterfall_tasks")
    return tuple(backed_up)


def _restore_phase_dependents(backed_up_tables: tuple[str, ...]) -> None:
    if "todos" in backed_up_tables:
        op.execute(sa.text("INSERT OR IGNORE INTO todos SELECT * FROM _migration_0011_todos"))
        op.execute(sa.text("DROP TABLE _migration_0011_todos"))
    if "waterfall_tasks" in backed_up_tables:
        op.execute(
            sa.text("INSERT OR IGNORE INTO waterfall_tasks SELECT * FROM _migration_0011_tasks")
        )
        op.execute(sa.text("DROP TABLE _migration_0011_tasks"))
