from datetime import datetime

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.core.infrastructure.database.models.Base import Base
from project_planner.core.infrastructure.database.models.UTCDateTime import UTCDateTime


class ApplicationIssueModel(Base):
    __tablename__ = "application_issues"
    __table_args__ = (Index("idx_application_issues_occurred", "occurred_at"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    exception_type: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
