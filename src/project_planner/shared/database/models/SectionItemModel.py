from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base
from project_planner.shared.database.models.UTCDateTime import UTCDateTime


class SectionItemModel(Base):
    __tablename__ = "section_items"
    __table_args__ = (
        Index("idx_section_items_position", "section_id", "position"),
        UniqueConstraint("section_id", "position", name="uq_section_items_position"),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_section_items_status",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    section_id: Mapped[str] = mapped_column(
        String, ForeignKey("planning_sections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assignee: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    item_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
