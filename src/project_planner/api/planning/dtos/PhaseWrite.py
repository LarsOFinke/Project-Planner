from datetime import date

from pydantic import BaseModel, ConfigDict

from project_planner.modules.planning.entities.PhaseStatus import PhaseStatus


class PhaseWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    start_date: date | None = None
    end_date: date | None = None
    section_id: str | None = None
