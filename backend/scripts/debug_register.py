import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.unified_auth_service import DatabasePool, auth_service, AuthConfig, AuthError

async def main():
    print("Testing registration for ia@satma.mx (should be duplicate)...")
    
    if not await DatabasePool.initialize():
        print("❌ Failed to initialize DB pool")
        return

    try:
        # Simulate registration logic directly through service
        # (This tests the SERVICE logic, but not the ROUTE exception handling entirely. 
        # But if this raises AuthError, we verify service behavior).
        user = await auth_service.create_user(
            email="ia@satma.mx",
            full_name="Pablo Santiago Álvarez Rincón",
            password="password123", # Password provided
            auth_method='password',
            company_name="SATMA",
            status='pending'
        )
        print("✅ User created (Unexpected if user exists!)")
        
    except AuthError as e:
        print(f"✅ AuthError Caught (Expected): {e.message} code={e.code} status={e.status_code}")
    except Exception as e:
        print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
