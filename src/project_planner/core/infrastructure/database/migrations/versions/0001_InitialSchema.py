import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("planning_method", sa.String(32), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_projects_title"),
        sa.ForeignKeyConstraint(["parent_id"], ["projects.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_projects_parent", "projects", ["parent_id"])
    op.create_index("idx_projects_status", "projects", ["status"])
    op.create_table(
        "phases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "position", name="uq_phases_project_position"),
    )
    op.create_table(
        "project_links",
        sa.Column("source_id", sa.String(), primary_key=True),
        sa.Column("target_id", sa.String(), primary_key=True),
        sa.Column("relation", sa.String(64), primary_key=True, server_default="related"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.CheckConstraint("source_id <> target_id", name="ck_project_links_distinct"),
        sa.ForeignKeyConstraint(["source_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('diagram', 'workspace')", name="ck_artifacts_kind"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "kind", name="uq_artifacts_project_kind"),
    )


def downgrade() -> None:
    op.drop_table("artifacts")
    op.drop_table("project_links")
    op.drop_table("phases")
    op.drop_index("idx_projects_status", table_name="projects")
    op.drop_index("idx_projects_parent", table_name="projects")
    op.drop_table("projects")
