from typing import List
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


class RainCorrelationResponse(BaseModel):
    rainy_average_delay: float
    dry_average_delay: float
    rainy_event_count: int
    dry_event_count: int
    rainy_days: int
    dry_days: int
