import asyncio
import os
import asyncpg
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FixLogin")

# Load env manually since we are running as script
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Try to read from .env file
    try:
        with open("../.env", "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    DATABASE_URL = line.strip().split("=", 1)[1]
                    break
    except Exception:
        pass

# Fallback for script location
if not DATABASE_URL:
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    DATABASE_URL = line.strip().split("=", 1)[1]
                    break
    except Exception:
        pass

if not DATABASE_URL:
    print("❌ Error: Could not find DATABASE_URL in environment or .env file")
    exit(1)

SQL_SETUP = """
-- 1. TABLA DE USUARIOS AUTORIZADOS
CREATE TABLE IF NOT EXISTS usuarios_autorizados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    empresa VARCHAR(255),
    rol VARCHAR(50) DEFAULT 'user',
    activo BOOLEAN DEFAULT true,
    empresa_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. TABLA DE CÓDIGOS OTP
CREATE TABLE IF NOT EXISTS codigos_otp (
    id VARCHAR(50) PRIMARY KEY,
    usuario_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    codigo VARCHAR(6) NOT NULL,
    usado BOOLEAN DEFAULT false,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_expiracion TIMESTAMPTZ NOT NULL,
    intentos INTEGER DEFAULT 0
);

-- 3. TABLA DE SESIONES OTP
CREATE TABLE IF NOT EXISTS sesiones_otp (
    id VARCHAR(50) PRIMARY KEY,
    usuario_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_expiracion TIMESTAMPTZ NOT NULL
);

-- 4. INSERT AUTHORIZED USERS
INSERT INTO usuarios_autorizados (email, nombre, empresa, rol, activo)
VALUES
    ('ia@satma.mx', 'Administrador SATMA', 'SATMA', 'super_admin', true)
ON CONFLICT (email) DO UPDATE SET
    activo = true,
    rol = 'super_admin';
"""

async def fix_login():
    print(f"🔌 Connecting to Database...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected!")
        
        print("🛠️  Running schema setup and user insertion...")
        await conn.execute(SQL_SETUP)
        print("✅ Schema and User applied successfully!")
        
        # Verify user
        row = await conn.fetchrow("SELECT * FROM usuarios_autorizados WHERE email = 'ia@satma.mx'")
        print(f"👤 Verified User: {row['email']} (Active: {row['activo']})")
        
        await conn.close()
        print("✨ Done. Please restart the backend server.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_login())
