from datetime import date

from pydantic import BaseModel, ConfigDict


class SprintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    start_date: date
    end_date: date
    goal: str
    selected_item_ids: list[str]
    section_id: str | None = None
