from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base
from project_planner.shared.database.models.UTCDateTime import UTCDateTime


class ResourceLinkModel(Base):
    __tablename__ = "resource_links"
    __table_args__ = (
        CheckConstraint("kind IN ('web', 'file')", name="ck_resource_links_kind"),
        CheckConstraint("length(trim(title)) > 0", name="ck_resource_links_title"),
        Index("idx_resource_links_project", "project_id", "kind", "title"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
