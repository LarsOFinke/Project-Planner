from datetime import date

from pydantic import BaseModel, ConfigDict

from project_planner.modules.planning.entities.SectionStatus import SectionStatus


class SectionItemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    assignee: str = ""
    status: SectionStatus = SectionStatus.NOT_STARTED
    item_date: date | None = None
