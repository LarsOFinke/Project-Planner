import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "todos" not in inspector.get_table_names():
        op.create_table(
            "todos",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("project_id", sa.String(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("module", sa.String(32), nullable=False, server_default="general"),
            sa.Column("status", sa.String(32), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("length(trim(title)) > 0", name="ck_todos_title"),
            sa.CheckConstraint(
                "module IN ('general', 'overview', 'phases', 'diagram', 'workspace', 'links')",
                name="ck_todos_module",
            ),
            sa.CheckConstraint("status IN ('open', 'in_progress', 'done')", name="ck_todos_status"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        )
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("todos")}
    if "idx_todos_project_status" not in indexes:
        op.create_index("idx_todos_project_status", "todos", ["project_id", "status", "updated_at"])


def downgrade() -> None:
    op.drop_table("todos")
