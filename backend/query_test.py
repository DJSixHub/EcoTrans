import asyncio
from app.db.session import async_session
from app.db.models import Route
from sqlmodel import select

async def main():
    async with async_session() as session:
        routes = (await session.scalars(select(Route))).all()
        print('routes type', type(routes), len(routes))
        for route in routes:
            print('item type', type(route), repr(route))
            try:
                print('id', route.id)
            except Exception as e:
                print('id error', type(e).__name__, e)

asyncio.run(main())
