from typing import Dict, List
from pydantic import BaseModel


class TerminalAnalytics(BaseModel):
    terminal_name: str
    compliance_rate: float
    average_wait_minutes: float
    sample_count: int


class AnalyticsResponse(BaseModel):
    terminals: List[TerminalAnalytics]


class SummaryResponse(BaseModel):
    year: int | None
    month: int | None
    period: str
    terminals: List[TerminalAnalytics]


class PeriodOptionsResponse(BaseModel):
    years: List[int]
    months: List[int]
    year_months: Dict[int, List[int]]


class RainCorrelationResponse(BaseModel):
    rainy_average_delay: float
    dry_average_delay: float
    rainy_event_count: int
    dry_event_count: int
    rainy_days: int
    dry_days: int


class CalendarEntry(BaseModel):
    date: str
    event_count: int


class TimeSeriesPoint(BaseModel):
    date: str
    compliance_rate: float
    average_delay: float
    total_passengers: int
    sample_count: int


class TimeSeriesResponse(BaseModel):
    period: str
    points: List[TimeSeriesPoint]


class TerminalGeoResponse(BaseModel):
    terminal_name: str
    latitude: float
    longitude: float
    zone: str
    compliance_rate: float
    average_wait_minutes: float
    sample_count: int


class RouteAnalytics(BaseModel):
    route_code: str
    route_type: str
    compliance_rate: float
    average_delay: float
    sample_count: int
    average_load_factor: float
