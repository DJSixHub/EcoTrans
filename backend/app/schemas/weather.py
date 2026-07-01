from datetime import date
from pydantic import BaseModel


class WeatherRead(BaseModel):
    observed_date: date
    precipitation_mm: float
    condition: str
    severe: bool

    class Config:
        orm_mode = True


class RainCorrelationResponse(BaseModel):
    rainy_average_delay: float
    dry_average_delay: float
    rainy_event_count: int
    dry_event_count: int
    rainy_days: int
    dry_days: int
