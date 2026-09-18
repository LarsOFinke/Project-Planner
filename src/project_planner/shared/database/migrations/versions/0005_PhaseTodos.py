import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("todos")}
    if "phase_id" not in columns:
        with op.batch_alter_table("todos") as batch:
            batch.add_column(sa.Column("phase_id", sa.String(), nullable=True))
            batch.create_foreign_key(
                "fk_todos_phase_id_phases",
                "phases",
                ["phase_id"],
                ["id"],
                ondelete="CASCADE",
            )
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("todos")}
    if "idx_todos_phase" not in indexes:
        op.create_index("idx_todos_phase", "todos", ["phase_id"])
    op.execute(sa.text("UPDATE todos SET module = 'general' WHERE module = 'overview'"))


def downgrade() -> None:
    op.drop_index("idx_todos_phase", table_name="todos")
    with op.batch_alter_table("todos") as batch:
        batch.drop_constraint("fk_todos_phase_id_phases", type_="foreignkey")
        batch.drop_column("phase_id")
