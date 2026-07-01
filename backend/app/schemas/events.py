from datetime import datetime
from pydantic import BaseModel


class DispatchEventSearchResult(BaseModel):
    id: int
    route_code: str
    terminal_name: str
    dispatch_datetime: datetime
    delay_minutes: int
    scheduled_minutes: int
    actual_minutes: int
    passengers_boarded: int
    on_time: bool

    class Config:
        orm_mode = True
