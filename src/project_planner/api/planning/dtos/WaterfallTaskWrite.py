from datetime import date

from pydantic import BaseModel, ConfigDict

from project_planner.modules.planning.entities.WaterfallTaskStatus import WaterfallTaskStatus


class WaterfallTaskWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    assignee: str = ""
    start_date: date | None = None
    due_date: date | None = None
    status: WaterfallTaskStatus = WaterfallTaskStatus.NOT_STARTED
