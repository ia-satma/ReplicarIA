import asyncio
import os
import sys
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.unified_auth_service import DatabasePool, auth_service, AuthConfig

async def main():
    print(f"DATABASE_URL: {AuthConfig.DATABASE_URL[:20]}...")
    
    print("1. Initializing DatabasePool...")
    try:
        success = await DatabasePool.initialize()
        if success:
            print("✅ DatabasePool initialized")
        else:
            print("❌ DatabasePool initialization failed")
            return
    except Exception as e:
        print(f"❌ Exception initializing pool: {e}")
        return

    print("\n2. Checking auth_users table...")
    async with await DatabasePool.get_connection() as conn:
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'auth_users'
                )
            """)
            print(f"Table auth_users exists: {exists}")
            
            if not exists:
                print("❌ auth_users table MISSING!")
                return
                
            # Check for ia@satma.mx
            print("\n3. Checking for ia@satma.mx...")
            user = await conn.fetchrow("SELECT * FROM auth_users WHERE email = 'ia@satma.mx'")
            if user:
                print(f"✅ User found: {dict(user)}")
            else:
                print("ℹ️ User ia@satma.mx NOT found")

            # Check logging function
            print("\n4. Checking log_auth_event function...")
            func_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_proc WHERE proname = 'log_auth_event'
                )
            """)
            print(f"Function log_auth_event exists: {func_exists}")

        except Exception as e:
            print(f"❌ Error during DB checks: {e}")

    # Test dummy user creation if not exists
    print("\n5. Testing user creation (dummy)...")
    try:
        dummy_email = f"test_{int(datetime.now().timestamp())}@example.com"
        print(f"Creating user {dummy_email}...")
        
        # We use a timeout to detect hangs
        user = await asyncio.wait_for(
            auth_service.create_user(
                email=dummy_email,
                full_name="Test User",
                password="password123",
                company_name="Test Corp",
                status='pending'
            ),
            timeout=10.0
        )
        print(f"✅ User created successfully: {user.id}")
        
    except asyncio.TimeoutError:
        print("❌ CRITICAL: User creation TIMED OUT (Hang detected)")
    except Exception as e:
        print(f"❌ Error creating user: {e}")

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
