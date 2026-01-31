#!/usr/bin/env python3
"""
Script standalone para ejecutar migraciones de base de datos.
Puede ejecutarse directamente: python scripts/run_migrations.py
"""

import asyncio
import asyncpg
import os
import sys
import re
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def get_clean_db_url() -> str:
    """Limpia y normaliza la URL de PostgreSQL."""
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        return ''
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)
    return url


async def run_migrations():
    """Ejecuta todas las migraciones necesarias."""
    db_url = get_clean_db_url()
    if not db_url:
        print("❌ DATABASE_URL not configured")
        return False

    results = {"created": [], "errors": [], "skipped": []}

    try:
        print(f"🔌 Connecting to database...")
        conn = await asyncpg.connect(db_url, ssl='require')
        print("✅ Connected to PostgreSQL")
        print("🔧 Running database migrations...")

        # ===== 1. Crear tabla clientes =====
        print("\n📋 Creating 'clientes' table...")
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    cliente_uuid UUID NOT NULL DEFAULT gen_random_uuid(),
                    nombre VARCHAR(255) NOT NULL,
                    rfc VARCHAR(20),
                    razon_social VARCHAR(255),
                    direccion TEXT,
                    email VARCHAR(255),
                    telefono VARCHAR(50),
                    giro VARCHAR(255),
                    sitio_web VARCHAR(255),
                    regimen_fiscal VARCHAR(100),
                    tipo_persona VARCHAR(20) DEFAULT 'moral',
                    actividad_economica VARCHAR(255),
                    estado VARCHAR(50) DEFAULT 'pendiente',
                    origen VARCHAR(50) DEFAULT 'manual',
                    empresa_id UUID,
                    usuario_responsable_id UUID,
                    activo BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by UUID
                )
            ''')
            results["created"].append("clientes")
            print("   ✅ Table 'clientes' created/verified")
        except Exception as e:
            results["errors"].append({"table": "clientes", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 2. Crear índices para clientes =====
        print("\n📋 Creating indexes for 'clientes'...")
        try:
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_empresa_id ON clientes(empresa_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_rfc ON clientes(rfc)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado)')
            results["created"].append("clientes_indexes")
            print("   ✅ Indexes created")
        except Exception as e:
            results["errors"].append({"item": "clientes_indexes", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 3. Crear tabla planes =====
        print("\n📋 Creating 'planes' table...")
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS planes (
                    id VARCHAR(50) PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    precio_mensual_mxn INTEGER DEFAULT 0,
                    requests_per_day INTEGER DEFAULT 50,
                    tokens_per_day INTEGER DEFAULT 100000,
                    documentos_max INTEGER DEFAULT 50,
                    usuarios_max INTEGER DEFAULT 3,
                    proyectos_max INTEGER DEFAULT 10,
                    features JSONB DEFAULT '[]',
                    activo BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            results["created"].append("planes")
            print("   ✅ Table 'planes' created/verified")
        except Exception as e:
            results["errors"].append({"table": "planes", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 4. Insertar planes por defecto =====
        print("\n📋 Inserting default plans...")
        try:
            await conn.execute('''
                INSERT INTO planes (id, nombre, descripcion, precio_mensual_mxn, requests_per_day, tokens_per_day, documentos_max, usuarios_max, proyectos_max)
                VALUES
                    ('free', 'Plan Gratuito', 'Para pruebas y evaluación', 0, 20, 50000, 10, 1, 3),
                    ('basico', 'Plan Básico', 'Ideal para pequeñas empresas', 2990, 50, 100000, 50, 3, 10),
                    ('profesional', 'Plan Profesional', 'Para empresas medianas', 7990, 200, 500000, 500, 10, 50),
                    ('enterprise', 'Plan Enterprise', 'Solución completa', 19990, 1000, 2000000, 5000, 50, 500)
                ON CONFLICT (id) DO NOTHING
            ''')
            results["created"].append("planes_data")
            print("   ✅ Default plans inserted")
        except Exception as e:
            results["errors"].append({"item": "planes_data", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 5. Agregar columna plan_id a empresas si no existe =====
        print("\n📋 Adding 'plan_id' column to 'empresas'...")
        try:
            await conn.execute('''
                ALTER TABLE empresas ADD COLUMN IF NOT EXISTS plan_id VARCHAR(50) DEFAULT 'basico'
            ''')
            results["created"].append("empresas_plan_id")
            print("   ✅ Column 'plan_id' added/verified")
        except Exception as e:
            results["errors"].append({"item": "empresas_plan_id", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 6. Agregar columna uso_suspendido a empresas =====
        print("\n📋 Adding 'uso_suspendido' column to 'empresas'...")
        try:
            await conn.execute('''
                ALTER TABLE empresas ADD COLUMN IF NOT EXISTS uso_suspendido BOOLEAN DEFAULT false
            ''')
            results["created"].append("empresas_uso_suspendido")
            print("   ✅ Column 'uso_suspendido' added/verified")
        except Exception as e:
            results["errors"].append({"item": "empresas_uso_suspendido", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 7. Crear tabla usage_tracking =====
        print("\n📋 Creating 'usage_tracking' table...")
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID NOT NULL,
                    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
                    requests_count INTEGER DEFAULT 0,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    costo_estimado_cents INTEGER DEFAULT 0,
                    chat_requests INTEGER DEFAULT 0,
                    rag_queries INTEGER DEFAULT 0,
                    document_uploads INTEGER DEFAULT 0,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT usage_tracking_empresa_fecha_unique UNIQUE (empresa_id, fecha)
                )
            ''')
            results["created"].append("usage_tracking")
            print("   ✅ Table 'usage_tracking' created/verified")
        except Exception as e:
            results["errors"].append({"table": "usage_tracking", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 8. Crear vista v_usage_dashboard =====
        print("\n📋 Creating 'v_usage_dashboard' view...")
        try:
            await conn.execute('''
                CREATE OR REPLACE VIEW v_usage_dashboard AS
                SELECT
                    u.empresa_id,
                    COALESCE(e.plan_id, 'free') as plan,
                    COALESCE(u.requests_count, 0) as requests_hoy,
                    COALESCE(u.tokens_input + u.tokens_output, 0) as tokens_hoy,
                    COALESCE(p.requests_per_day, 50) as limite_requests,
                    COALESCE(p.tokens_per_day, 100000) as limite_tokens,
                    CASE
                        WHEN p.requests_per_day > 0 THEN
                            LEAST(100, ROUND(COALESCE(u.requests_count, 0)::numeric / p.requests_per_day * 100, 0))
                        ELSE 0
                    END as pct_requests,
                    CASE
                        WHEN p.tokens_per_day > 0 THEN
                            LEAST(100, ROUND(COALESCE(u.tokens_input + u.tokens_output, 0)::numeric / p.tokens_per_day * 100, 0))
                        ELSE 0
                    END as pct_tokens
                FROM usage_tracking u
                LEFT JOIN empresas e ON e.id = u.empresa_id
                LEFT JOIN planes p ON p.id = e.plan_id
                WHERE u.fecha = CURRENT_DATE
            ''')
            results["created"].append("v_usage_dashboard")
            print("   ✅ View 'v_usage_dashboard' created/replaced")
        except Exception as e:
            results["errors"].append({"view": "v_usage_dashboard", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 9. Crear función increment_usage =====
        print("\n📋 Creating 'increment_usage' function...")
        try:
            await conn.execute('''
                CREATE OR REPLACE FUNCTION increment_usage(
                    p_empresa_id UUID,
                    p_requests INTEGER DEFAULT 1,
                    p_tokens_in INTEGER DEFAULT 0,
                    p_tokens_out INTEGER DEFAULT 0,
                    p_usage_type VARCHAR DEFAULT 'chat'
                ) RETURNS TABLE (
                    allowed BOOLEAN,
                    requests_remaining INTEGER,
                    tokens_remaining INTEGER,
                    message VARCHAR
                ) AS $$
                DECLARE
                    v_requests_per_day INTEGER := 50;
                    v_tokens_per_day INTEGER := 100000;
                    v_current_requests INTEGER;
                    v_current_tokens INTEGER;
                    v_plan_id VARCHAR;
                BEGIN
                    -- Get plan limits
                    SELECT e.plan_id INTO v_plan_id FROM empresas e WHERE e.id = p_empresa_id;

                    IF v_plan_id IS NOT NULL THEN
                        SELECT p.requests_per_day, p.tokens_per_day
                        INTO v_requests_per_day, v_tokens_per_day
                        FROM planes p WHERE p.id = v_plan_id;
                    END IF;

                    -- Upsert usage tracking
                    INSERT INTO usage_tracking (empresa_id, fecha, requests_count, tokens_input, tokens_output)
                    VALUES (p_empresa_id, CURRENT_DATE, p_requests, p_tokens_in, p_tokens_out)
                    ON CONFLICT (empresa_id, fecha) DO UPDATE SET
                        requests_count = usage_tracking.requests_count + p_requests,
                        tokens_input = usage_tracking.tokens_input + p_tokens_in,
                        tokens_output = usage_tracking.tokens_output + p_tokens_out,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING requests_count, tokens_input + tokens_output INTO v_current_requests, v_current_tokens;

                    IF v_current_requests > v_requests_per_day THEN
                        RETURN QUERY SELECT FALSE, 0, v_tokens_per_day - v_current_tokens, 'Límite de requests alcanzado'::VARCHAR;
                    ELSIF v_current_tokens > v_tokens_per_day THEN
                        RETURN QUERY SELECT FALSE, v_requests_per_day - v_current_requests, 0, 'Límite de tokens alcanzado'::VARCHAR;
                    ELSE
                        RETURN QUERY SELECT TRUE, v_requests_per_day - v_current_requests, v_tokens_per_day - v_current_tokens, 'OK'::VARCHAR;
                    END IF;
                END;
                $$ LANGUAGE plpgsql
            ''')
            results["created"].append("increment_usage_function")
            print("   ✅ Function 'increment_usage' created/replaced")
        except Exception as e:
            results["errors"].append({"function": "increment_usage", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 10. Crear tabla request_logs =====
        print("\n📋 Creating 'request_logs' table...")
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS request_logs (
                    id SERIAL PRIMARY KEY,
                    empresa_id UUID,
                    user_id UUID,
                    endpoint VARCHAR(255),
                    method VARCHAR(10),
                    tokens_in INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0,
                    latency_ms INTEGER DEFAULT 0,
                    status_code INTEGER,
                    error_message TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_empresa_id ON request_logs(empresa_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_request_logs_created_at ON request_logs(created_at)')
            results["created"].append("request_logs")
            print("   ✅ Table 'request_logs' created/verified")
        except Exception as e:
            results["errors"].append({"table": "request_logs", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        # ===== 11. Crear vista v_usage_monthly =====
        print("\n📋 Creating 'v_usage_monthly' view...")
        try:
            await conn.execute('''
                CREATE OR REPLACE VIEW v_usage_monthly AS
                SELECT
                    empresa_id,
                    DATE_TRUNC('month', fecha) as mes,
                    SUM(requests_count) as total_requests,
                    SUM(tokens_input) as total_tokens_in,
                    SUM(tokens_output) as total_tokens_out,
                    SUM(costo_estimado_cents) as costo_total_cents
                FROM usage_tracking
                GROUP BY empresa_id, DATE_TRUNC('month', fecha)
            ''')
            results["created"].append("v_usage_monthly")
            print("   ✅ View 'v_usage_monthly' created/replaced")
        except Exception as e:
            results["errors"].append({"view": "v_usage_monthly", "error": str(e)[:100]})
            print(f"   ❌ Error: {str(e)[:100]}")

        await conn.close()

        # Print summary
        print("\n" + "=" * 60)
        print("📊 MIGRATION SUMMARY")
        print("=" * 60)
        print(f"✅ Created/Updated: {len(results['created'])} items")
        for item in results['created']:
            print(f"   - {item}")

        if results['errors']:
            print(f"\n❌ Errors: {len(results['errors'])} items")
            for error in results['errors']:
                print(f"   - {error}")

        print(f"\n⏰ Completed at: {datetime.now().isoformat()}")
        print("=" * 60)

        return len(results['errors']) == 0

    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 REVISAR.IA DATABASE MIGRATIONS")
    print("=" * 60)

    success = asyncio.run(run_migrations())

    sys.exit(0 if success else 1)
