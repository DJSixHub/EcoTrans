from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.api_v1.endpoints.auth import get_current_user
from app.db.models import DispatchEvent, Route, Terminal, User
from app.db.session import async_session
from app.schemas.events import (
    DispatchEventCreate,
    DispatchEventRead,
    DispatchEventSearchResult,
    DispatchEventUpdate,
)

router = APIRouter()


async def get_event_or_404(event_id: int, session: AsyncSession) -> DispatchEvent:
    result = await session.exec(
        select(DispatchEvent)
        .options(selectinload(DispatchEvent.route), selectinload(DispatchEvent.terminal))
        .where(DispatchEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento no encontrado")
    return event


def marshal_event(dispatch: DispatchEvent, route: Route, terminal: Terminal) -> DispatchEventRead:
    return DispatchEventRead(
        id=dispatch.id,
        route_id=dispatch.route_id,
        terminal_id=dispatch.terminal_id,
        route_code=route.code,
        terminal_name=terminal.name,
        dispatch_datetime=dispatch.dispatch_datetime,
        delay_minutes=max(0, dispatch.actual_minutes - dispatch.scheduled_minutes),
        scheduled_minutes=dispatch.scheduled_minutes,
        actual_minutes=dispatch.actual_minutes,
        passengers_boarded=dispatch.passengers_boarded,
        on_time=dispatch.on_time,
        planned_frequency_minutes=dispatch.planned_frequency_minutes,
        vehicle_capacity=dispatch.vehicle_capacity,
        service_level=dispatch.service_level,
        day_type=dispatch.day_type,
        peak_period=dispatch.peak_period,
        weather_condition=dispatch.weather_condition,
    )


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


@router.post("/events", response_model=DispatchEventRead)
async def create_event(
    event_in: DispatchEventCreate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "inspector", "analyst"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    async with async_session() as session:
        route = await session.get(Route, event_in.route_id)
        terminal = await session.get(Terminal, event_in.terminal_id)
        if not route or not terminal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta o terminal no válida")

        event = DispatchEvent(
            route_id=route.id,
            terminal_id=terminal.id,
            dispatch_datetime=event_in.dispatch_datetime,
            scheduled_minutes=event_in.scheduled_minutes,
            actual_minutes=event_in.actual_minutes,
            passengers_boarded=event_in.passengers_boarded,
            planned_frequency_minutes=event_in.planned_frequency_minutes,
            vehicle_capacity=event_in.vehicle_capacity,
            service_level=event_in.service_level,
            day_type=event_in.day_type,
            peak_period=event_in.peak_period,
            weather_condition=event_in.weather_condition,
            route_type=route.route_type,
            on_time=(event_in.actual_minutes - event_in.scheduled_minutes) <= 5,
            passenger_load_factor=min(100.0, max(0.0, round(event_in.passengers_boarded / max(1, event_in.vehicle_capacity) * 100, 1))),
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)

    return marshal_event(event, route, terminal)


@router.put("/events/{event_id}", response_model=DispatchEventRead)
async def update_event(
    event_id: int,
    event_in: DispatchEventUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"admin", "inspector"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    async with async_session() as session:
        event = await get_event_or_404(event_id, session)
        if event_in.route_id is not None:
            route = await session.get(Route, event_in.route_id)
            if not route:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no válida")
            event.route_id = route.id
            event.route_type = route.route_type
        else:
            route = await session.get(Route, event.route_id)
        if event_in.terminal_id is not None:
            terminal = await session.get(Terminal, event_in.terminal_id)
            if not terminal:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal no válida")
            event.terminal_id = terminal.id
        else:
            terminal = await session.get(Terminal, event.terminal_id)

        if event_in.dispatch_datetime is not None:
            event.dispatch_datetime = event_in.dispatch_datetime
        if event_in.scheduled_minutes is not None:
            event.scheduled_minutes = event_in.scheduled_minutes
        if event_in.actual_minutes is not None:
            event.actual_minutes = event_in.actual_minutes
        if event_in.passengers_boarded is not None:
            event.passengers_boarded = event_in.passengers_boarded
        if event_in.planned_frequency_minutes is not None:
            event.planned_frequency_minutes = event_in.planned_frequency_minutes
        if event_in.vehicle_capacity is not None:
            event.vehicle_capacity = event_in.vehicle_capacity
        if event_in.service_level is not None:
            event.service_level = event_in.service_level
        if event_in.day_type is not None:
            event.day_type = event_in.day_type
        if event_in.peak_period is not None:
            event.peak_period = event_in.peak_period
        if event_in.weather_condition is not None:
            event.weather_condition = event_in.weather_condition

        event.on_time = (event.actual_minutes - event.scheduled_minutes) <= 5
        event.passenger_load_factor = min(100.0, max(0.0, round(event.passengers_boarded / max(1, event.vehicle_capacity) * 100, 1)))

        session.add(event)
        await session.commit()
        await session.refresh(event)

    return marshal_event(event, route, terminal)


@router.delete("/events/{event_id}")
async def delete_event(event_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role not in {"admin", "inspector"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")

    async with async_session() as session:
        event = await get_event_or_404(event_id, session)
        await session.delete(event)
        await session.commit()

    return {"detail": "Evento eliminado"}
