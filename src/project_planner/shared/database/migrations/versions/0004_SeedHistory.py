import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "seed_history" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "seed_history",
            sa.Column("key", sa.String(128), primary_key=True),
            sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("seed_history")
