"""
Health V4 Routes - Endpoints de salud y administración.
Incluye migraciones de base de datos, reset de demo, y diagnósticos.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import asyncpg
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health V4"])

DATABASE_URL = os.environ.get('DATABASE_URL', '')
RESET_SECRET = os.environ.get('RESET_SECRET_KEY', 'satma-reset-2024-confirmado')


def get_clean_db_url() -> str:
    """Limpia y normaliza la URL de PostgreSQL."""
    url = DATABASE_URL
    if not url:
        return ''
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)
    return url


class ResetRequest(BaseModel):
    secret_key: str


@router.post('/reset-demo')
async def reset_demo_data(request: ResetRequest):
    """Reset all demo data. Requires secret_key."""
    if request.secret_key != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    db_url = get_clean_db_url()
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    try:
        conn = await asyncpg.connect(db_url, ssl='require')
        logger.warning("⚠️ RESET DEMO DATA started")

        results = {"cleaned": [], "errors": []}

        tables = [
            'clientes_historial', 'clientes_interacciones', 'clientes_contexto',
            'clientes_documentos', 'proveedores_scoring', 'df_proveedores',
            'df_documents', 'df_metadata', 'kb_chunk_agente', 'kb_chunks',
            'kb_documentos', 'kb_metricas', 'projects', 'project_documents',
            'project_notes', 'clientes', 'proveedores', 'auth_otp_codes',
            'auth_rate_limits'
        ]

        for table in tables:
            try:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", table
                )
                if exists:
                    count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                    await conn.execute(f'DELETE FROM {table}')
                    results["cleaned"].append({"table": table, "deleted": count})
            except Exception as e:
                results["errors"].append({"table": table, "error": str(e)[:50]})

        # Clean non-admin users
        try:
            await conn.execute('''
                DELETE FROM auth_users
                WHERE email NOT IN ('ia@satma.mx', 'admin@revisar-ia.com')
                AND role NOT IN ('super_admin', 'admin')
            ''')
            results["cleaned"].append({"table": "auth_users (non-admin)", "deleted": "done"})
        except Exception as e:
            results["errors"].append({"table": "auth_users", "error": str(e)[:50]})

        await conn.close()
        logger.warning("✅ RESET DEMO DATA completed")

        return {"success": True, "results": results, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/rag_count/{agent_id}')
def rag_count(agent_id: str):
    """Cuenta chunks RAG para un agente. Importación lazy de RagRepository."""
    try:
        from services.rag_repository import RagRepository
        rag = RagRepository()
        count = rag.count(agent_id)
        return {"success": True, "agent": agent_id, "count": count}
    except ImportError as e:
        return {"success": False, "error": f"RagRepository not available: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get('/sql_refresh')
def sql_refresh():
    """Refresca catálogo SQL. Importación lazy de sql_engine_service."""
    try:
        from services.sql_engine_service import refresh_catalog, list_tables
        result = refresh_catalog()
        tables = list_tables()
        return {"success": True, "refreshed": result, "tables": tables}
    except ImportError as e:
        return {"success": False, "error": f"SQL engine not available: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get('/kg_stats')
def kg_statistics():
    """Estadísticas de Knowledge Graph. Importación lazy."""
    try:
        from services.knowledge_graph_service import get_stats as kg_stats
        stats = kg_stats()
        return {"success": True, "kg": stats}
    except ImportError as e:
        return {"success": False, "error": f"Knowledge Graph not available: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post('/router_test')
def test_router(query: str):
    """Test de router de queries. Importación lazy."""
    try:
        from services.query_router import get_route_explanation
        explanation = get_route_explanation(query)
        return {"success": True, "routing": explanation}
    except ImportError as e:
        return {"success": False, "error": f"Query router not available: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post('/run-migrations')
async def run_migrations(request: ResetRequest):
    """
    Ejecuta las migraciones SQL para crear tablas y vistas faltantes.
    Requiere secret_key.
    """
    if request.secret_key != RESET_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    db_url = get_clean_db_url()
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

    results = {"created": [], "errors": [], "skipped": []}

    try:
        conn = await asyncpg.connect(db_url, ssl='require')
        logger.info("🔧 Running database migrations...")

        # ===== 1. Crear tabla clientes =====
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
            logger.info("✅ Tabla 'clientes' creada/verificada")
        except Exception as e:
            results["errors"].append({"table": "clientes", "error": str(e)[:100]})

        # ===== 2. Crear índices para clientes =====
        try:
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_empresa_id ON clientes(empresa_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_rfc ON clientes(rfc)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado)')
            results["created"].append("clientes_indexes")
        except Exception as e:
            results["errors"].append({"item": "clientes_indexes", "error": str(e)[:100]})

        # ===== 3. Crear tabla planes =====
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
        except Exception as e:
            results["errors"].append({"table": "planes", "error": str(e)[:100]})

        # ===== 4. Insertar planes por defecto =====
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
        except Exception as e:
            results["errors"].append({"item": "planes_data", "error": str(e)[:100]})

        # ===== 5. Agregar columna plan_id a empresas si no existe =====
        try:
            await conn.execute('''
                ALTER TABLE empresas ADD COLUMN IF NOT EXISTS plan_id VARCHAR(50) DEFAULT 'basico'
            ''')
            results["created"].append("empresas_plan_id")
        except Exception as e:
            results["errors"].append({"item": "empresas_plan_id", "error": str(e)[:100]})

        # ===== 6. Agregar columna uso_suspendido a empresas =====
        try:
            await conn.execute('''
                ALTER TABLE empresas ADD COLUMN IF NOT EXISTS uso_suspendido BOOLEAN DEFAULT false
            ''')
            results["created"].append("empresas_uso_suspendido")
        except Exception as e:
            results["errors"].append({"item": "empresas_uso_suspendido", "error": str(e)[:100]})

        # ===== 7. Crear tabla usage_tracking =====
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
        except Exception as e:
            results["errors"].append({"table": "usage_tracking", "error": str(e)[:100]})

        # ===== 8. Crear vista v_usage_dashboard =====
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
        except Exception as e:
            results["errors"].append({"view": "v_usage_dashboard", "error": str(e)[:100]})

        # ===== 9. Crear función increment_usage =====
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
        except Exception as e:
            results["errors"].append({"function": "increment_usage", "error": str(e)[:100]})

        # ===== 10. Crear tabla request_logs =====
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
        except Exception as e:
            results["errors"].append({"table": "request_logs", "error": str(e)[:100]})

        # ===== 11. Crear vista v_usage_monthly =====
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
        except Exception as e:
            results["errors"].append({"view": "v_usage_monthly", "error": str(e)[:100]})

        await conn.close()
        logger.info(f"✅ Migrations completed: {len(results['created'])} created, {len(results['errors'])} errors")

        return {
            "success": len(results["errors"]) == 0,
            "message": "Migraciones ejecutadas",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/db-status')
async def db_status():
    """Verifica el estado de la base de datos y las tablas existentes."""
    db_url = get_clean_db_url()
    if not db_url:
        return {"success": False, "error": "DATABASE_URL not configured"}

    try:
        conn = await asyncpg.connect(db_url, ssl='require')

        # Get list of tables
        tables = await conn.fetch('''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        ''')

        # Get list of views
        views = await conn.fetch('''
            SELECT table_name as view_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        ''')

        # Get list of functions
        functions = await conn.fetch('''
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'public'
            AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        ''')

        await conn.close()

        return {
            "success": True,
            "tables": [r['table_name'] for r in tables],
            "views": [r['view_name'] for r in views],
            "functions": [r['routine_name'] for r in functions],
            "tables_count": len(tables),
            "views_count": len(views),
            "functions_count": len(functions)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
