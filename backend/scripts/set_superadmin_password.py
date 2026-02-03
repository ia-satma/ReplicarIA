
import asyncio
import os
import sys
import bcrypt
import logging

# Ensure we can import from backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_password():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    # Clean connection string
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    if '?sslmode=' in db_url:
        import re
        db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)

    email = "santiago@satma.mx"
    raw_password = "SuperAdmin2026!"
    hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    print(f"🔌 Connecting to database...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # Check if user exists
        user = await conn.fetchrow("SELECT id, role, auth_method FROM auth_users WHERE LOWER(email) = LOWER($1)", email)
        
        if not user:
            print(f"❌ User {email} not found! Creating it...")
            await conn.execute("""
                INSERT INTO auth_users (email, full_name, password_hash, role, status, auth_method, company_name)
                VALUES ($1, 'Super Admin', $2, 'super_admin', 'active', 'password', 'SATMA')
            """, email, hashed)
            print("✅ User created.")
        else:
            print(f"👤 User found (Role: {user['role']}, Auth: {user['auth_method']}). Updating...")
            await conn.execute("""
                UPDATE auth_users 
                SET password_hash = $1, 
                    auth_method = 'password',
                    role = 'super_admin',
                    status = 'active',
                    updated_at = NOW()
                WHERE LOWER(email) = LOWER($2)
            """, hashed, email)
            print("✅ User updated.")
        
        await conn.close()
        
        print("\n" + "="*50)
        print(f"✅ CREDENTIALS SET FOR: {email}")
        print(f"🔑 Password: {raw_password}")
        print("="*50 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(set_password())
