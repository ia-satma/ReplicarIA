
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def inspect_user():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        row = await conn.fetchrow("SELECT * FROM auth_users WHERE email = 'ia@satma.mx'")
        if row:
            print(f"User found: {dict(row)}")
        else:
            print("User NOT found")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_user())
