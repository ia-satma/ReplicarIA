import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import exactly as the route does
from services.otp_auth_service import get_db_connection

async def main():
    email = "santiago@satma.mx"
    print(f"Checking auth method for: {email}")
    
    try:
        conn = await get_db_connection()
        if not conn:
            print("❌ No database connection available")
            return

        print("✅ Database connection established")
        
        try:
             # Check auth_users table for password users
            row = await conn.fetchrow('''
                SELECT email, auth_method, role, status FROM auth_users
                WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            ''', email)

            print(f"Query result: {dict(row) if row else 'No row found'}")
            
            if row:
                if row['auth_method'] == 'password':
                    print("✅ CORRECT: Identified as PASSWORD user")
                else:
                    print(f"❌ INCORRECT: Identified as {row['auth_method']}")
            else:
                print("❌ User not found in auth_users via this connection")
                
        except Exception as e:
            print(f"❌ Query Error: {e}")
        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
