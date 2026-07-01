from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()
engine: AsyncEngine = create_async_engine(settings.database_url, echo=False, future=True)


class EcoTransAsyncSession(AsyncSession):
    async def exec(self, statement, params=None, execution_options=None, bind_arguments=None, **kw):
        return await super().execute(
            statement,
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            **kw,
        )


async_session = sessionmaker(engine, class_=EcoTransAsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
