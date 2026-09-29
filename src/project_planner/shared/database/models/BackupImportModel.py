from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from project_planner.shared.database.models.Base import Base


class BackupImportModel(Base):
    __tablename__ = "backup_imports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
