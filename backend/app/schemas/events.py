from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DispatchEventBase(BaseModel):
    route_id: int
    terminal_id: int
    dispatch_datetime: datetime
    scheduled_minutes: int
    actual_minutes: int
    passengers_boarded: int
    planned_frequency_minutes: int
    vehicle_capacity: int
    service_level: str
    day_type: str
    peak_period: str
    weather_condition: Optional[str] = None


class DispatchEventCreate(DispatchEventBase):
    pass


class DispatchEventUpdate(BaseModel):
    route_id: Optional[int] = None
    terminal_id: Optional[int] = None
    dispatch_datetime: Optional[datetime] = None
    scheduled_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    passengers_boarded: Optional[int] = None
    planned_frequency_minutes: Optional[int] = None
    vehicle_capacity: Optional[int] = None
    service_level: Optional[str] = None
    day_type: Optional[str] = None
    peak_period: Optional[str] = None
    weather_condition: Optional[str] = None


class DispatchEventRead(DispatchEventBase):
    id: int
    route_code: str
    terminal_name: str
    delay_minutes: int
    on_time: bool

    class Config:
        orm_mode = True


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
