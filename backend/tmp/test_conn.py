import asyncio
import asyncpg
import os

async def main():
    user = os.getenv('POSTGRES_USER') or os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    db = os.getenv('POSTGRES_DB')
    host = 'database'
    port = int(os.getenv('DATABASE_PORT', 5432))
    print('ENV', user, db, host, port)
    try:
        conn = await asyncpg.connect(user=user, password=password, database=db, host=host, port=port)
        print('CONNECTED')
        await conn.close()
    except Exception as e:
        print('ERROR', type(e), e)

asyncio.run(main())
