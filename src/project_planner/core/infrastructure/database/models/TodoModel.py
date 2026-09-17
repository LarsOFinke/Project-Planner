from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.core.infrastructure.database.models.Base import Base
from project_planner.core.infrastructure.database.models.UTCDateTime import UTCDateTime


class TodoModel(Base):
    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_todos_title"),
        CheckConstraint(
            "module IN ('general', 'overview', 'phases', 'diagram', 'workspace', 'links')",
            name="ck_todos_module",
        ),
        CheckConstraint("status IN ('open', 'in_progress', 'done')", name="ck_todos_status"),
        Index("idx_todos_project_status", "project_id", "status", "updated_at"),
        Index("idx_todos_phase", "phase_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    phase_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("phases.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    module: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
