from datetime import date

from pydantic import BaseModel, ConfigDict

from project_planner.modules.planning.entities.SectionStatus import SectionStatus
from project_planner.modules.planning.entities.SectionType import SectionType


class SectionWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    section_type: SectionType
    description: str = ""
    status: SectionStatus = SectionStatus.NOT_STARTED
    start_date: date | None = None
    end_date: date | None = None
