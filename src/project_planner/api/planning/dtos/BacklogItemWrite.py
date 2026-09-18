from pydantic import BaseModel, ConfigDict

from project_planner.modules.planning.entities.BacklogPriority import BacklogPriority
from project_planner.modules.planning.entities.BacklogStatus import BacklogStatus


class BacklogItemWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    priority: BacklogPriority = BacklogPriority.MEDIUM
    status: BacklogStatus = BacklogStatus.BACKLOG
    assignee: str = ""
    section_id: str | None = None
