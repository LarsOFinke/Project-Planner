from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.core.infrastructure.database.models.Base import Base
from project_planner.core.infrastructure.database.models.UTCDateTime import UTCDateTime


class SprintModel(Base):
    __tablename__ = "sprints"
    __table_args__ = (
        Index("idx_sprints_context_status", "project_id", "section_id", "status"),
        CheckConstraint(
            "status IN ('planned', 'current', 'completed')",
            name="ck_sprints_status",
        ),
        CheckConstraint("end_date >= start_date", name="ck_sprints_dates"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("planning_sections.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
