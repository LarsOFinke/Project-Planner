import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_issues",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("exception_type", sa.String(160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_application_issues_occurred",
        "application_issues",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("application_issues")
