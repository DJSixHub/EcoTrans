from typing import List, Optional
from datetime import datetime
from sqlalchemy import case, func, literal, Float
from sqlmodel import select
from fastapi import APIRouter, Depends, Query
from app.db.models import DispatchEvent, Route, Terminal, WeatherObservation
from app.db.session import async_session
from app.schemas.analytics import AnalyticsResponse, SummaryResponse, RainCorrelationResponse, TerminalAnalytics

router = APIRouter()

PEAK_HOURS = list(range(6, 10)) + list(range(17, 21))
RAIN_THRESHOLD = 10.0


def build_filters(year: Optional[int], month: Optional[int], period: str):
    filters = []
    if year is not None:
        filters.append(func.date_part("year", DispatchEvent.dispatch_datetime) == year)
    if month is not None:
        filters.append(func.date_part("month", DispatchEvent.dispatch_datetime) == month)
    if period == "peak":
        filters.append(func.date_part("hour", DispatchEvent.dispatch_datetime).in_(PEAK_HOURS))
    elif period == "offpeak":
        filters.append(~func.date_part("hour", DispatchEvent.dispatch_datetime).in_(PEAK_HOURS))
    return filters


async def query_terminal_metrics(year: Optional[int], month: Optional[int], period: str) -> List[TerminalAnalytics]:
    async with async_session() as session:
        filters = build_filters(year, month, period)
        stmt = (
            select(
                Terminal.name.label("terminal_name"),
                func.count(DispatchEvent.id).label("sample_count"),
                (
                    func.sum(case((DispatchEvent.on_time == True, 1), else_=0)).cast(Float)
                    / func.nullif(func.count(DispatchEvent.id), 0) * 100
                ).label("compliance_rate"),
                func.avg(
                    case(
                        (DispatchEvent.actual_minutes > DispatchEvent.scheduled_minutes,
                         DispatchEvent.actual_minutes - DispatchEvent.scheduled_minutes),
                        else_=0,
                    )
                ).label("average_wait_minutes"),
            )
            .join(Terminal, Terminal.id == DispatchEvent.terminal_id)
            .where(*filters)
            .group_by(Terminal.name)
            .order_by(Terminal.name)
        )
        result = await session.exec(stmt)
        rows = result.all()

    analytics = []
    for row in rows:
        analytics.append(
            TerminalAnalytics(
                terminal_name=row.terminal_name,
                compliance_rate=float(row.compliance_rate or 0),
                average_wait_minutes=float(row.average_wait_minutes or 0),
                sample_count=int(row.sample_count or 0),
            )
        )
    return analytics


@router.get("/metadata/terminals")
async def metadata_terminals():
    async with async_session() as session:
        terminals = (await session.scalars(select(Terminal).order_by(Terminal.name))).all()
    return [
        {"id": terminal.id, "name": terminal.name, "zone": terminal.zone}
        for terminal in terminals
    ]


@router.get("/metadata/routes")
async def metadata_routes():
    async with async_session() as session:
        routes = (await session.scalars(select(Route).order_by(Route.code))).all()
    return [
        {"id": route.id, "code": route.code, "origin": route.origin, "destination": route.destination}
        for route in routes
    ]


@router.get("/analytics/rain-correlation", response_model=RainCorrelationResponse)
async def rain_correlation(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    delay_expr = case(
        (DispatchEvent.actual_minutes > DispatchEvent.scheduled_minutes,
         DispatchEvent.actual_minutes - DispatchEvent.scheduled_minutes),
        else_=0,
    )
    filters = []
    if year is not None:
        filters.append(func.date_part("year", DispatchEvent.dispatch_datetime) == year)
    if month is not None:
        filters.append(func.date_part("month", DispatchEvent.dispatch_datetime) == month)

    async with async_session() as session:
        rainy_stmt = (
            select(
                func.avg(delay_expr).label("average_delay"),
                func.count(DispatchEvent.id).label("event_count"),
                func.count(func.distinct(WeatherObservation.observed_date)).label("day_count"),
            )
            .join(WeatherObservation, func.date(DispatchEvent.dispatch_datetime) == WeatherObservation.observed_date)
            .where(WeatherObservation.precipitation_mm >= RAIN_THRESHOLD, *filters)
        )
        dry_stmt = (
            select(
                func.avg(delay_expr).label("average_delay"),
                func.count(DispatchEvent.id).label("event_count"),
                func.count(func.distinct(WeatherObservation.observed_date)).label("day_count"),
            )
            .join(WeatherObservation, func.date(DispatchEvent.dispatch_datetime) == WeatherObservation.observed_date)
            .where(WeatherObservation.precipitation_mm < RAIN_THRESHOLD, *filters)
        )
        rainy = await session.exec(rainy_stmt)
        dry = await session.exec(dry_stmt)
        rainy_row = rainy.one()
        dry_row = dry.one()

    return RainCorrelationResponse(
        rainy_average_delay=float(rainy_row.average_delay or 0),
        dry_average_delay=float(dry_row.average_delay or 0),
        rainy_event_count=int(rainy_row.event_count or 0),
        dry_event_count=int(dry_row.event_count or 0),
        rainy_days=int(rainy_row.day_count or 0),
        dry_days=int(dry_row.day_count or 0),
    )


@router.get("/analytics/summary", response_model=SummaryResponse)
async def analytics_summary(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
):
    terminals = await query_terminal_metrics(year, month, period)
    return SummaryResponse(year=year, month=month, period=period, terminals=terminals)


@router.get("/analytics/terminals", response_model=AnalyticsResponse)
async def analytics_terminals(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
):
    terminals = await query_terminal_metrics(year, month, period)
    return AnalyticsResponse(terminals=terminals)
