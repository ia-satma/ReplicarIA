-- ============================================================
-- Schema para tabla de Clientes
-- Usado por el sistema de onboarding y gestión de clientes
-- ============================================================

-- Crear tabla clientes si no existe
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    cliente_uuid UUID NOT NULL DEFAULT gen_random_uuid(),

    -- Datos básicos
    nombre VARCHAR(255) NOT NULL,
    rfc VARCHAR(20),
    razon_social VARCHAR(255),

    -- Datos de contacto
    direccion TEXT,
    email VARCHAR(255),
    telefono VARCHAR(50),

    -- Datos fiscales/comerciales
    giro VARCHAR(255),
    sitio_web VARCHAR(255),
    regimen_fiscal VARCHAR(100),
    tipo_persona VARCHAR(20) DEFAULT 'moral', -- moral, fisica
    actividad_economica VARCHAR(255),

    -- Estado y control
    estado VARCHAR(50) DEFAULT 'pendiente', -- pendiente, activo, inactivo
    origen VARCHAR(50) DEFAULT 'manual', -- manual, chat, importacion

    -- Relaciones
    empresa_id UUID, -- Tenant/empresa que lo creó
    usuario_responsable_id UUID, -- Usuario que lo tiene asignado

    -- Auditoría
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,

    -- Índices
    CONSTRAINT clientes_rfc_empresa_unique UNIQUE (rfc, empresa_id)
);

-- Índices para búsquedas comunes
CREATE INDEX IF NOT EXISTS idx_clientes_empresa_id ON clientes(empresa_id);
CREATE INDEX IF NOT EXISTS idx_clientes_rfc ON clientes(rfc);
CREATE INDEX IF NOT EXISTS idx_clientes_estado ON clientes(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_uuid ON clientes(cliente_uuid);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_clientes_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS clientes_updated_at ON clientes;
CREATE TRIGGER clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_clientes_timestamp();

-- ============================================================
-- Vista para dashboard de uso
-- ============================================================

CREATE OR REPLACE VIEW v_usage_dashboard AS
SELECT
    u.empresa_id,
    COALESCE(p.id, 'free') as plan,
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
WHERE u.fecha = CURRENT_DATE;

-- ============================================================
-- Tabla de planes (si no existe)
-- ============================================================

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
);

-- Insertar planes por defecto si no existen
INSERT INTO planes (id, nombre, descripcion, precio_mensual_mxn, requests_per_day, tokens_per_day, documentos_max, usuarios_max, proyectos_max)
VALUES
    ('basico', 'Plan Básico', 'Ideal para pequeñas empresas', 2990, 50, 100000, 50, 3, 10),
    ('profesional', 'Plan Profesional', 'Para empresas medianas', 7990, 200, 500000, 500, 10, 50),
    ('enterprise', 'Plan Enterprise', 'Solución completa para corporativos', 19990, 1000, 2000000, 5000, 50, 500)
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Tabla usage_tracking (si no existe)
-- ============================================================

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
);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_fecha ON usage_tracking(fecha);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_empresa ON usage_tracking(empresa_id);

-- ============================================================
-- Función para incrementar uso (usada por rate limiter)
-- ============================================================

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
    v_requests_per_day INTEGER;
    v_tokens_per_day INTEGER;
    v_current_requests INTEGER;
    v_current_tokens INTEGER;
BEGIN
    -- Obtener límites del plan
    SELECT COALESCE(p.requests_per_day, 50), COALESCE(p.tokens_per_day, 100000)
    INTO v_requests_per_day, v_tokens_per_day
    FROM empresas e
    LEFT JOIN planes p ON p.id = e.plan_id
    WHERE e.id = p_empresa_id;

    IF v_requests_per_day IS NULL THEN
        v_requests_per_day := 50;
        v_tokens_per_day := 100000;
    END IF;

    -- Insertar o actualizar uso
    INSERT INTO usage_tracking (empresa_id, fecha, requests_count, tokens_input, tokens_output)
    VALUES (p_empresa_id, CURRENT_DATE, p_requests, p_tokens_in, p_tokens_out)
    ON CONFLICT (empresa_id, fecha) DO UPDATE SET
        requests_count = usage_tracking.requests_count + p_requests,
        tokens_input = usage_tracking.tokens_input + p_tokens_in,
        tokens_output = usage_tracking.tokens_output + p_tokens_out,
        updated_at = CURRENT_TIMESTAMP
    RETURNING requests_count, tokens_input + tokens_output INTO v_current_requests, v_current_tokens;

    -- Verificar límites
    IF v_current_requests > v_requests_per_day THEN
        RETURN QUERY SELECT FALSE, 0, v_tokens_per_day - v_current_tokens, 'Límite de requests alcanzado'::VARCHAR;
    ELSIF v_current_tokens > v_tokens_per_day THEN
        RETURN QUERY SELECT FALSE, v_requests_per_day - v_current_requests, 0, 'Límite de tokens alcanzado'::VARCHAR;
    ELSE
        RETURN QUERY SELECT TRUE, v_requests_per_day - v_current_requests, v_tokens_per_day - v_current_tokens, 'OK'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;
