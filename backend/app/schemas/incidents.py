from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IncidentBase(BaseModel):
    route_id: Optional[int] = None
    terminal_id: Optional[int] = None
    type: str
    description: str


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None


class IncidentRead(IncidentBase):
    id: int
    report_time: datetime
    status: str
    reported_by: str
    route_code: Optional[str] = None
    terminal_name: Optional[str] = None

    class Config:
        orm_mode = True
