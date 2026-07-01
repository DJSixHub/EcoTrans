from sqlalchemy import select, func
from typing import Optional
from app.core.security import get_password_hash
from app.db.models import User
from app.db.session import async_session


async def get_user_by_username(username: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.exec(select(User).where(User.username == username))
        return result.scalar_one_or_none()


async def get_user_by_email(email: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.exec(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def create_user(username: str, email: str, password: str, role: str = "analyst") -> User:
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password, role=role)
    async with async_session() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def create_default_users() -> None:
    async with async_session() as session:
        total = await session.scalar(select(func.count()).select_from(User))
        if total and total > 0:
            return
        default_users = [
            {"username": "admin", "email": "admin@ecotrans.local", "password": "Admin123!", "role": "admin"},
            {"username": "inspector", "email": "inspector@ecotrans.local", "password": "Inspect123!", "role": "inspector"},
            {"username": "analyst", "email": "analyst@ecotrans.local", "password": "Analyst123!", "role": "analyst"},
        ]
        for user_data in default_users:
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                role=user_data["role"],
            )
            session.add(user)
        await session.commit()
