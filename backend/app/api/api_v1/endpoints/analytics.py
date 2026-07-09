from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import case, func, Float, Integer, literal_column
from sqlmodel import select
from fastapi import APIRouter, Query
from app.db.models import DispatchEvent, Route, Terminal, WeatherObservation
from app.db.session import async_session
from app.schemas.analytics import (
    AnalyticsResponse,
    CalendarEntry,
    PeriodOptionsResponse,
    RainCorrelationResponse,
    RouteAnalytics,
    SummaryResponse,
    TerminalAnalytics,
    TerminalGeoResponse,
    TimeSeriesPoint,
    TimeSeriesResponse,
)

router = APIRouter()

PEAK_HOURS = list(range(6, 10)) + list(range(17, 21))
RAIN_THRESHOLD = 10.0


def build_filters(
    year: Optional[int],
    month: Optional[int],
    period: str,
    selected_date: Optional[date] = None,
):
    filters = []
    if year is not None:
        filters.append(func.date_part(literal_column("'year'"), DispatchEvent.dispatch_datetime) == year)
    if month is not None:
        filters.append(func.date_part(literal_column("'month'"), DispatchEvent.dispatch_datetime) == month)
    if selected_date is not None:
        filters.append(func.date(DispatchEvent.dispatch_datetime) == selected_date)
    if period == "peak":
        filters.append(func.date_part(literal_column("'hour'"), DispatchEvent.dispatch_datetime).in_(PEAK_HOURS))
    elif period == "offpeak":
        filters.append(~func.date_part(literal_column("'hour'"), DispatchEvent.dispatch_datetime).in_(PEAK_HOURS))
    return filters


async def query_terminal_metrics(
    year: Optional[int],
    month: Optional[int],
    period: str,
    selected_date: Optional[date] = None,
) -> List[TerminalAnalytics]:
    async with async_session() as session:
        filters = build_filters(year, month, period, selected_date)
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
        {
            "id": terminal.id,
            "name": terminal.name,
            "zone": terminal.zone,
            "latitude": terminal.latitude,
            "longitude": terminal.longitude,
        }
        for terminal in terminals
    ]


@router.get("/metadata/routes")
async def metadata_routes():
    async with async_session() as session:
        routes = (await session.scalars(select(Route).order_by(Route.code))).all()
    return [
        {
            "id": route.id,
            "code": route.code,
            "origin": route.origin,
            "destination": route.destination,
            "route_type": route.route_type,
        }
        for route in routes
    ]


@router.get("/analytics/periods", response_model=PeriodOptionsResponse)
async def analytics_periods():
    async with async_session() as session:
        year_expr = func.cast(func.date_part("year", DispatchEvent.dispatch_datetime), Integer)
        month_expr = func.cast(func.date_part("month", DispatchEvent.dispatch_datetime), Integer)
        subquery = (
            select(year_expr.label("year"), month_expr.label("month"))
            .subquery()
        )
        query = (
            select(subquery.c.year, subquery.c.month)
            .distinct()
            .order_by(subquery.c.year, subquery.c.month)
        )
        rows = (await session.exec(query)).all()
    years = []
    months_set = set()
    year_months = {}
    for row in rows:
        year = int(row.year)
        month = int(row.month)
        months_set.add(month)
        if year not in year_months:
            year_months[year] = []
        year_months[year].append(month)
    years = sorted(year_months.keys())
    months = sorted(months_set)
    for year, month_list in year_months.items():
        year_months[year] = sorted(set(month_list))
    return {"years": years, "months": months, "year_months": year_months}


@router.get("/analytics/calendar", response_model=List[CalendarEntry])
async def analytics_calendar(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    filters = build_filters(year, month, "all")
    async with async_session() as session:
        query = (
            select(
                func.date(DispatchEvent.dispatch_datetime).label("date"),
                func.count(DispatchEvent.id).label("event_count"),
            )
            .where(*filters)
            .group_by(func.date(DispatchEvent.dispatch_datetime))
            .order_by(func.date(DispatchEvent.dispatch_datetime))
        )
        rows = (await session.exec(query)).all()
    return [
        CalendarEntry(date=row.date.isoformat(), event_count=int(row.event_count or 0))
        for row in rows
    ]


@router.get("/analytics/timeseries", response_model=TimeSeriesResponse)
async def analytics_timeseries(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
    frequency: str = Query("day", regex="^(day|month)$"),
    selected_date: Optional[date] = Query(None),
):
    filters = build_filters(year, month, period, selected_date)
    if frequency == "day":
        period_expr = func.date(DispatchEvent.dispatch_datetime)
    else:
        period_expr = func.date_trunc(literal_column("'month'"), DispatchEvent.dispatch_datetime)
    period_label = period_expr.label("period")
    async with async_session() as session:
        stmt = (
            select(
                period_label,
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
                ).label("average_delay"),
                func.sum(DispatchEvent.passengers_boarded).label("total_passengers"),
                func.count(DispatchEvent.id).label("sample_count"),
            )
            .where(*filters)
            .group_by(period_expr)
            .order_by(period_expr)
        )
        rows = (await session.exec(stmt)).all()
    return TimeSeriesResponse(
        period=frequency,
        points=[
            TimeSeriesPoint(
                date=(
                    row.period.isoformat()
                    if isinstance(row.period, date)
                    else row.period.strftime("%Y-%m")
                )
                if frequency == "month"
                else (
                    row.period.isoformat()
                    if isinstance(row.period, date)
                    else row.period.date().isoformat()
                ),
                compliance_rate=float(row.compliance_rate or 0),
                average_delay=float(row.average_delay or 0),
                total_passengers=int(row.total_passengers or 0),
                sample_count=int(row.sample_count or 0),
            )
            for row in rows
        ],
    )


@router.get("/analytics/geo-terminals", response_model=List[TerminalGeoResponse])
async def analytics_geo_terminals(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
    selected_date: Optional[date] = Query(None),
):
    filters = build_filters(year, month, period, selected_date)
    async with async_session() as session:
        stmt = (
            select(
                Terminal.name.label("terminal_name"),
                Terminal.latitude,
                Terminal.longitude,
                Terminal.zone,
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
            .group_by(Terminal.id)
            .order_by(Terminal.name)
        )
        rows = (await session.exec(stmt)).all()
    return [
        TerminalGeoResponse(
            terminal_name=row.terminal_name,
            latitude=float(row.latitude or 0),
            longitude=float(row.longitude or 0),
            zone=row.zone,
            compliance_rate=float(row.compliance_rate or 0),
            average_wait_minutes=float(row.average_wait_minutes or 0),
            sample_count=int(row.sample_count or 0),
        )
        for row in rows
    ]


@router.get("/analytics/rain-correlation", response_model=RainCorrelationResponse)
async def analytics_rain_correlation(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    async with async_session() as session:
        filters = build_filters(year, month, "all")
        stmt = (
            select(
                func.count(func.distinct(DispatchEvent.id)).label("total_events"),
                func.sum(case((WeatherObservation.precipitation_mm >= RAIN_THRESHOLD, 1), else_=0)).label("rainy_days"),
                func.avg(
                    case(
                        (WeatherObservation.precipitation_mm >= RAIN_THRESHOLD,
                         DispatchEvent.actual_minutes - DispatchEvent.scheduled_minutes),
                        else_=None,
                    )
                ).label("rainy_avg_delay"),
                func.avg(
                    case(
                        (WeatherObservation.precipitation_mm < RAIN_THRESHOLD,
                         DispatchEvent.actual_minutes - DispatchEvent.scheduled_minutes),
                        else_=None,
                    )
                ).label("dry_avg_delay"),
            )
            .outerjoin(
                WeatherObservation,
                func.date(DispatchEvent.dispatch_datetime) == WeatherObservation.observed_date,
            )
            .where(*filters)
        )
        result = await session.exec(stmt)
        row = result.one()

        rainy_days = int(row.rainy_days or 0)
        total_events = int(row.total_events or 0)
        dry_days = max(0, total_events - rainy_days)
        rainy_avg = float(row.rainy_avg_delay or 0)
        dry_avg = float(row.dry_avg_delay or 0)

    return RainCorrelationResponse(
        rainy_days=rainy_days,
        dry_days=dry_days,
        rainy_event_count=rainy_days,
        dry_event_count=dry_days,
        rainy_average_delay=rainy_avg,
        dry_average_delay=dry_avg,
    )


@router.get("/analytics/routes", response_model=List[RouteAnalytics])
async def analytics_routes(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
    selected_date: Optional[date] = Query(None),
):
    filters = build_filters(year, month, period, selected_date)
    async with async_session() as session:
        stmt = (
            select(
                Route.code.label("route_code"),
                Route.route_type,
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
                ).label("average_delay"),
                func.avg(DispatchEvent.passenger_load_factor).label("average_load_factor"),
            )
            .join(Route, Route.id == DispatchEvent.route_id)
            .where(*filters)
            .group_by(Route.code, Route.route_type)
            .order_by(Route.code)
        )
        rows = (await session.exec(stmt)).all()
    return [
        RouteAnalytics(
            route_code=row.route_code,
            route_type=row.route_type,
            compliance_rate=float(row.compliance_rate or 0),
            average_delay=float(row.average_delay or 0),
            sample_count=int(row.sample_count or 0),
            average_load_factor=float(row.average_load_factor or 0),
        )
        for row in rows
    ]


@router.get("/analytics/summary", response_model=SummaryResponse)
async def analytics_summary(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
    selected_date: Optional[date] = Query(None),
):
    terminals = await query_terminal_metrics(year, month, period, selected_date)
    return SummaryResponse(year=year, month=month, period=period, terminals=terminals)


@router.get("/analytics/terminals", response_model=AnalyticsResponse)
async def analytics_terminals(
    year: Optional[int] = Query(None, ge=2014, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    period: str = Query("all", regex="^(all|peak|offpeak)$"),
    selected_date: Optional[date] = Query(None),
):
    terminals = await query_terminal_metrics(year, month, period, selected_date)
    return AnalyticsResponse(terminals=terminals)
