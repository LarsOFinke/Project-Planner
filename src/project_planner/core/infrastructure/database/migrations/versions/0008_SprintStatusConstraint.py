from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

_SPRINT_STATUSES = "status IN ('planned', 'current', 'completed')"


def upgrade() -> None:
    _replace_sprint_status_constraint()


def downgrade() -> None:
    # Canonical revision 0007 uses the same vocabulary. Recreating it keeps a
    # downgraded database aligned with that immutable schema definition.
    _replace_sprint_status_constraint()


def _replace_sprint_status_constraint() -> None:
    with op.batch_alter_table("sprints") as batch:
        batch.drop_constraint("ck_sprints_status", type_="check")
        batch.create_check_constraint("ck_sprints_status", _SPRINT_STATUSES)
