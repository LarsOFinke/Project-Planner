import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "phases" in sa.inspect(bind).get_table_names():
        op.add_column("phases", sa.Column("parallel_group", sa.String(length=80), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    if "phases" in sa.inspect(bind).get_table_names():
        op.drop_column("phases", "parallel_group")
