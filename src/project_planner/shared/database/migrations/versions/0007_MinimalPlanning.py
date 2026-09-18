import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("target_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("owner", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("assignee", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("notes", sa.Text(), nullable=False, server_default=""))

    op.create_table(
        "planning_sections",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("section_type", sa.String(24), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="not_started"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "section_type IN ('free', 'agile', 'waterfall')",
            name="ck_sections_type",
        ),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_sections_status",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
            name="ck_sections_dates",
        ),
        sa.UniqueConstraint("project_id", "position", name="uq_sections_project_position"),
    )
    op.create_index(
        "idx_sections_project_position", "planning_sections", ["project_id", "position"]
    )
    op.create_table(
        "sprints",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("section_id", sa.String(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["planning_sections.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('planned', 'current', 'completed')",
            name="ck_sprints_status",
        ),
        sa.CheckConstraint("end_date >= start_date", name="ck_sprints_dates"),
    )
    op.create_index(
        "idx_sprints_context_status",
        "sprints",
        ["project_id", "section_id", "status"],
    )
    op.create_table(
        "backlog_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("section_id", sa.String(), nullable=True),
        sa.Column("sprint_id", sa.String(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("assignee", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["section_id"], ["planning_sections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sprint_id"], ["sprints.id"], ondelete="SET NULL"),
        sa.CheckConstraint("priority IN ('high', 'medium', 'low')", name="ck_backlog_priority"),
        sa.CheckConstraint(
            "status IN ('backlog', 'in_progress', 'done')",
            name="ck_backlog_status",
        ),
    )
    op.create_index(
        "idx_backlog_context_position",
        "backlog_items",
        ["project_id", "section_id", "position"],
    )
    op.create_table(
        "section_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("section_id", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("assignee", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("item_date", sa.Date(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["section_id"], ["planning_sections.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_section_items_status",
        ),
        sa.UniqueConstraint("section_id", "position", name="uq_section_items_position"),
    )
    op.create_index("idx_section_items_position", "section_items", ["section_id", "position"])
    with op.batch_alter_table("phases") as batch:
        batch.add_column(sa.Column("start_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("end_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("section_id", sa.String(), nullable=True))
        batch.create_foreign_key(
            "fk_phases_section_id_sections",
            "planning_sections",
            ["section_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.create_check_constraint(
            "ck_phases_dates",
            "end_date IS NULL OR start_date IS NULL OR end_date >= start_date",
        )
    op.execute(
        sa.text(
            "UPDATE phases SET status = CASE "
            "WHEN status = 'completed' OR status = 'skipped' THEN 'completed' "
            "WHEN status = 'active' OR status = 'blocked' THEN 'in_progress' "
            "ELSE 'not_started' END"
        )
    )
    op.create_table(
        "waterfall_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("phase_id", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("assignee", sa.Text(), nullable=False, server_default=""),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["phase_id"], ["phases.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_waterfall_tasks_status",
        ),
        sa.CheckConstraint(
            "due_date IS NULL OR start_date IS NULL OR due_date >= start_date",
            name="ck_waterfall_tasks_dates",
        ),
        sa.UniqueConstraint("phase_id", "position", name="uq_waterfall_tasks_position"),
    )
    op.create_index(
        "idx_waterfall_tasks_phase_position",
        "waterfall_tasks",
        ["phase_id", "position"],
    )


def downgrade() -> None:
    op.drop_table("waterfall_tasks")
    with op.batch_alter_table("phases") as batch:
        batch.drop_constraint("ck_phases_dates", type_="check")
        batch.drop_constraint("fk_phases_section_id_sections", type_="foreignkey")
        batch.drop_column("section_id")
        batch.drop_column("end_date")
        batch.drop_column("start_date")
    op.drop_table("section_items")
    op.drop_table("backlog_items")
    op.drop_table("sprints")
    op.drop_table("planning_sections")
    with op.batch_alter_table("projects") as batch:
        batch.drop_column("notes")
        batch.drop_column("assignee")
        batch.drop_column("owner")
        batch.drop_column("target_date")
        batch.drop_column("start_date")
