from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base


class ProjectLinkModel(Base):
    __tablename__ = "project_links"
    __table_args__ = (CheckConstraint("source_id <> target_id", name="ck_project_links_distinct"),)

    source_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    target_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    relation: Mapped[str] = mapped_column(String(64), primary_key=True, default="related")
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
