import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.unified_auth_service import DatabasePool, AuthConfig

async def main():
    if not await DatabasePool.initialize():
        print("❌ Failed to initialize DB pool")
        return

    email = "santiago@satma.mx"
    print(f"Checking for user: {email}")
    
    async with await DatabasePool.get_connection() as conn:
        user = await conn.fetchrow("SELECT * FROM auth_users WHERE email = $1", email)
        if user:
            print(f"✅ User found: {dict(user)}")
        else:
            print(f"❌ User {email} NOT found in auth_users")
            
            # Check legacy table just in case
            legacy = await conn.fetchrow("SELECT * FROM usuarios_autorizados WHERE email = $1", email)
            if legacy:
                print(f"⚠️  User found in LEGACY 'usuarios_autorizados' but not 'auth_users'. Migration needed.")
                print(f"Legacy data: {dict(legacy)}")

                # Attempt migration
                print("Attempting single user migration...")
                await conn.execute("""
                    INSERT INTO auth_users (
                        email, email_verified, full_name, company_name, role, status, auth_method, created_at
                    ) VALUES ($1, $2, $3, $4, $5, 'active', 'otp', NOW())
                    ON CONFLICT (email) DO NOTHING
                """, legacy['email'], True, legacy['nombre'] or legacy['email'], legacy['empresa'], legacy['rol'] or 'user')
                print("✅ Migration executed. Try logging in again.")
                
            else:
                print("❌ User not found in legacy table either.")
                
                # Auto-create for convenience if it's the specific user asking
                print("Creating user...")
                await conn.execute("""
                    INSERT INTO auth_users (
                        email, full_name, role, status, auth_method, company_name, approval_required, created_at
                    ) VALUES ($1, 'Santiago', 'admin', 'active', 'otp', 'SATMA', false, NOW())
                """, email)
                print("✅ User santiago@satma.mx created manually.")

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
