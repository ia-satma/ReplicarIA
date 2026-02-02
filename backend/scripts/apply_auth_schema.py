import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.unified_auth_service import DatabasePool, AuthConfig

async def main():
    print(f"DATABASE_URL: {AuthConfig.DATABASE_URL[:20]}...")
    
    # Initialize DB
    if not await DatabasePool.initialize():
        print("❌ Failed to initialize DB pool")
        return

    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'auth_schema.sql')
    print(f"Reading schema from: {schema_path}")
    
    with open(schema_path, 'r') as f:
        sql_content = f.read()

    print("Executing schema...")
    try:
        async with await DatabasePool.get_connection() as conn:
            # Execute the full script
            await conn.execute(sql_content)
            print("✅ Schema applied successfully")
            
            # Verify function exists
            func_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_proc WHERE proname = 'log_auth_event'
                )
            """)
            print(f"Function log_auth_event exists: {func_exists}")
            
            # Verify user migration
            user = await conn.fetchrow("SELECT * FROM auth_users WHERE email = 'ia@satma.mx'")
            if user:
                print(f"✅ User ia@satma.mx migrated/found: {dict(user)}")
            else:
                print("ℹ️ User ia@satma.mx NOT found (migration might have skipped if source empty)")
                
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
    
    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
