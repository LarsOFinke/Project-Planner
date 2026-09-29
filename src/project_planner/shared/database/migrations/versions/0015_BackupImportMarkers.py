import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("backup_imports", sa.Column("id", sa.String(), primary_key=True))


def downgrade() -> None:
    op.drop_table("backup_imports")
