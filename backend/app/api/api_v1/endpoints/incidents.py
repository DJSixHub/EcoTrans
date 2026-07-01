from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.api_v1.endpoints.auth import get_current_user
from app.db.models import Incident, Route, Terminal, User
from app.db.session import async_session
from app.schemas.incidents import IncidentCreate, IncidentRead, IncidentUpdate
from app.schemas.users import UserRead

router = APIRouter()


def require_role(user: User, roles: List[str]) -> None:
    if user.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")


async def get_incident_or_404(incident_id: int, session: AsyncSession) -> Incident:
    result = await session.exec(
        select(Incident)
        .options(selectinload(Incident.route), selectinload(Incident.terminal), selectinload(Incident.reported_by))
        .where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incidencia no encontrada")
    return incident


async def marshal_incident(incident: Incident) -> IncidentRead:
    return IncidentRead(
        id=incident.id,
        route_id=incident.route_id,
        terminal_id=incident.terminal_id,
        type=incident.type,
        description=incident.description,
        status=incident.status,
        report_time=incident.report_time,
        reported_by=incident.reported_by.username if incident.reported_by else "unknown",
        route_code=incident.route.code if incident.route else None,
        terminal_name=incident.terminal.name if incident.terminal else None,
    )


@router.post("/incidents", response_model=IncidentRead)
async def create_incident(incident_in: IncidentCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in {"admin", "inspector", "analyst"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    incident = Incident(
        route_id=incident_in.route_id,
        terminal_id=incident_in.terminal_id,
        type=incident_in.type,
        description=incident_in.description,
        status="open",
        reported_by_id=current_user.id,
        report_time=datetime.utcnow(),
    )
    async with async_session() as session:
        session.add(incident)
        await session.commit()
        await session.refresh(incident)
        incident = await get_incident_or_404(incident.id, session)
    return await marshal_incident(incident)


@router.get("/incidents", response_model=List[IncidentRead])
async def list_incidents(status: Optional[str] = Query(None), current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        query = select(Incident).options(selectinload(Incident.route), selectinload(Incident.terminal), selectinload(Incident.reported_by))
        if status:
            query = query.where(Incident.status == status)
        incidents = (await session.scalars(query.order_by(Incident.report_time.desc()))).all()
    return [await marshal_incident(i) for i in incidents]


@router.get("/incidents/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: int, current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        incident = await get_incident_or_404(incident_id, session)
    return await marshal_incident(incident)


@router.put("/incidents/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: int,
    incident_in: IncidentUpdate,
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, ["admin", "inspector"])
    async with async_session() as session:
        incident = await get_incident_or_404(incident_id, session)
        if incident_in.status is not None:
            incident.status = incident_in.status
        if incident_in.type is not None:
            incident.type = incident_in.type
        if incident_in.description is not None:
            incident.description = incident_in.description
        session.add(incident)
        await session.commit()
        await session.refresh(incident)
    return await marshal_incident(incident)


@router.delete("/incidents/{incident_id}")
async def delete_incident(incident_id: int, current_user: User = Depends(get_current_user)):
    require_role(current_user, ["admin"])
    async with async_session() as session:
        incident = await get_incident_or_404(incident_id, session)
        await session.delete(incident)
        await session.commit()
    return {"detail": "Incidencia eliminada"}
