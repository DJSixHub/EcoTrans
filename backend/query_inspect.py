import asyncio
from app.db.session import async_session
from app.db.models import Route
from sqlmodel import select

async def main():
    async with async_session() as session:
        result = await session.scalars(select(Route))
        print(type(result))
        data = result.all()
        print('all type', type(data))
        print('len', len(data))
        if data:
            print('item type', type(data[0]))
            print('repr', repr(data[0]))

asyncio.run(main())
