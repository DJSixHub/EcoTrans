from datetime import date, datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Terminal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    zone: str

    dispatch_events: List["DispatchEvent"] = Relationship(back_populates="terminal")
    incidents: List["Incident"] = Relationship(back_populates="terminal")


class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    origin: str
    destination: str

    dispatch_events: List["DispatchEvent"] = Relationship(back_populates="route")
    incidents: List["Incident"] = Relationship(back_populates="route")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="analyst")
    is_active: bool = Field(default=True)

    incidents: List["Incident"] = Relationship(back_populates="reported_by")


class WeatherObservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    observed_date: date = Field(index=True)
    precipitation_mm: float
    condition: str
    severe: bool = Field(default=False)


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_time: datetime = Field(default_factory=datetime.utcnow, index=True)
    route_id: Optional[int] = Field(default=None, foreign_key="route.id", index=True)
    terminal_id: Optional[int] = Field(default=None, foreign_key="terminal.id", index=True)
    type: str
    description: str
    status: str = Field(default="open")
    reported_by_id: int = Field(foreign_key="user.id", index=True)

    route: Optional[Route] = Relationship(back_populates="incidents")
    terminal: Optional[Terminal] = Relationship(back_populates="incidents")
    reported_by: User = Relationship(back_populates="incidents")


class DispatchEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(foreign_key="route.id", index=True)
    terminal_id: int = Field(foreign_key="terminal.id", index=True)
    dispatch_datetime: datetime = Field(index=True)
    scheduled_minutes: int
    actual_minutes: int
    passengers_boarded: int
    on_time: bool = Field(index=True)

    route: Route = Relationship(back_populates="dispatch_events")
    terminal: Terminal = Relationship(back_populates="dispatch_events")
