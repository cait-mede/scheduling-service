from pydantic import BaseModel, Field
from typing import List


class ScheduleCreate(BaseModel):
    app_id: str
    entity_id: str
    slots: List[str]
    created_by: str
    book: str = ''


class Availability(BaseModel):
    user_id: str
    available_slots: List[int]


class ConfirmSlot(BaseModel):
    slot_index: int = Field(ge=0)
