import asyncio
from services.database_pg import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check():
    try:
        async with get_connection() as conn:
            # check if table exists
            tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            table_names = [t['table_name'] for t in tables]
            print(f"Tables found: {table_names}")
            
            if 'deliberations' in table_names:
                count = await conn.fetchval('SELECT count(*) FROM deliberations')
                print(f"Deliberations Count: {count}")
                
                # If count is > 0, let's see a sample
                if count > 0:
                    sample = await conn.fetchrow('SELECT * FROM deliberations LIMIT 1')
                    print(f"Sample: {dict(sample)}")
            else:
                print("TABLE_NOT_FOUND: deliberations")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
