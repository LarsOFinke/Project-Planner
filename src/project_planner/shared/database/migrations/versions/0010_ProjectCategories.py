import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_categories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_project_categories_name"),
    )
    op.create_index(
        "idx_project_categories_position",
        "project_categories",
        ["position"],
    )
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            sa.text(
                "ALTER TABLE projects ADD COLUMN category_id VARCHAR "
                "REFERENCES project_categories(id) ON DELETE SET NULL"
            )
        )
    else:
        op.add_column(
            "projects",
            sa.Column(
                "category_id",
                sa.String(),
                sa.ForeignKey(
                    "project_categories.id",
                    name="fk_projects_category_id_categories",
                    ondelete="SET NULL",
                ),
                nullable=True,
            ),
        )
    op.create_index("idx_projects_category", "projects", ["category_id"])


def downgrade() -> None:
    op.drop_index("idx_projects_category", table_name="projects")
    op.drop_column("projects", "category_id")
    op.drop_table("project_categories")
