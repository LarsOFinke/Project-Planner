from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("phases")}
    timestamp = datetime.now(UTC).isoformat()
    with op.batch_alter_table("phases") as batch:
        if "status" not in columns:
            batch.add_column(
                sa.Column("status", sa.String(32), nullable=False, server_default="planned")
            )
        if "created_at" not in columns:
            batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
        if "updated_at" not in columns:
            batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    fill_created_at = sa.text(
        "UPDATE phases SET created_at = :stamp WHERE created_at IS NULL"
    ).bindparams(stamp=timestamp)
    op.execute(fill_created_at)
    op.execute(sa.text("UPDATE phases SET updated_at = created_at WHERE updated_at IS NULL"))
    with op.batch_alter_table("phases") as batch:
        batch.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False)
        batch.alter_column("updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("phases") as batch:
        batch.drop_column("updated_at")
        batch.drop_column("created_at")
        batch.drop_column("status")
