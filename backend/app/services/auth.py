from datetime import timedelta
from typing import Optional
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import get_settings
from app.core.security import verify_password, create_access_token
from app.db.models import User
from app.db.session import async_session

settings = get_settings()


async def get_user_by_username(username: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.exec(select(User).where(User.username == username))
        return result.scalar_one_or_none()


async def authenticate_user(username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_access_token_for_user(user: User) -> str:
    return create_access_token(subject=user.username, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))
