from datetime import datetime

from sqlalchemy import CheckConstraint, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base
from project_planner.shared.database.models.UTCDateTime import UTCDateTime


class ProjectCategoryModel(Base):
    __tablename__ = "project_categories"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_project_categories_name"),
        Index("idx_project_categories_position", "position"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
