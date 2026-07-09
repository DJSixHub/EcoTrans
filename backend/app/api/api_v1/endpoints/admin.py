from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from app.api.api_v1.endpoints.auth import get_current_user
from app.db.models import User, DispatchEvent, Incident, WeatherObservation, Terminal, Route
from app.db.session import async_session
from app.schemas.users import UserRead

router = APIRouter()


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo administradores")
    return user


@router.get("/users", response_model=List[UserRead])
async def list_users(current_user: User = Depends(require_admin)):
    async with async_session() as session:
        users = (await session.scalars(select(User))).all()
    return users


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(require_admin)):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        await session.delete(user)
        await session.commit()
    return {"detail": "Usuario eliminado"}


@router.get("/admin/stats")
async def admin_stats(current_user: User = Depends(require_admin)):
    async with async_session() as session:
        total_users = (await session.scalar(select(func.count()).select_from(User))) or 0
        total_events = (await session.scalar(select(func.count()).select_from(DispatchEvent))) or 0
        total_incidents = (await session.scalar(select(func.count()).select_from(Incident))) or 0
        total_weather = (await session.scalar(select(func.count()).select_from(WeatherObservation))) or 0
        total_terminals = (await session.scalar(select(func.count()).select_from(Terminal))) or 0
        total_routes = (await session.scalar(select(func.count()).select_from(Route))) or 0
    return {
        "total_users": total_users,
        "total_events": total_events,
        "total_incidents": total_incidents,
        "total_weather": total_weather,
        "total_terminals": total_terminals,
        "total_routes": total_routes,
    }