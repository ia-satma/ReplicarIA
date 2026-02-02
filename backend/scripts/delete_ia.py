
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def delete_user():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        # Delete user if exists
        await conn.execute("DELETE FROM auth_users WHERE email = 'ia@satma.mx'")
        print("User 'ia@satma.mx' DELETED successfully.")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(delete_user())
