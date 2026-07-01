from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.api.api_v1.endpoints.auth import get_current_user
from app.db.models import DispatchEvent, Route, Terminal, User
from app.db.session import async_session
from app.schemas.events import DispatchEventSearchResult

router = APIRouter()


@router.get("/search/events", response_model=List[DispatchEventSearchResult])
async def search_events(
    route_code: Optional[str] = Query(None),
    terminal_name: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    on_time: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
):
    conditions = []
    if route_code:
        conditions.append(Route.code == route_code)
    if terminal_name:
        conditions.append(Terminal.name == terminal_name)
    if from_date:
        conditions.append(DispatchEvent.dispatch_datetime >= from_date)
    if to_date:
        conditions.append(DispatchEvent.dispatch_datetime <= to_date)
    if on_time is not None:
        conditions.append(DispatchEvent.on_time == on_time)

    async with async_session() as session:
        stmt = (
            select(DispatchEvent, Route, Terminal)
            .join(Route, Route.id == DispatchEvent.route_id)
            .join(Terminal, Terminal.id == DispatchEvent.terminal_id)
            .order_by(DispatchEvent.dispatch_datetime.desc())
            .limit(100)
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await session.exec(stmt)
        rows = result.all()

    return [
        DispatchEventSearchResult(
            id=dispatch.id,
            route_code=route.code,
            terminal_name=terminal.name,
            dispatch_datetime=dispatch.dispatch_datetime,
            delay_minutes=max(0, dispatch.actual_minutes - dispatch.scheduled_minutes),
            scheduled_minutes=dispatch.scheduled_minutes,
            actual_minutes=dispatch.actual_minutes,
            passengers_boarded=dispatch.passengers_boarded,
            on_time=dispatch.on_time,
        )
        for dispatch, route, terminal in rows
    ]
