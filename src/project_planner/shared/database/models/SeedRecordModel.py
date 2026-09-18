from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base
from project_planner.shared.database.models.UTCDateTime import UTCDateTime


class SeedRecordModel(Base):
    __tablename__ = "seed_history"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
