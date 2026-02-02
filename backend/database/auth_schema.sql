-- =====================================================
-- REVISAR.IA - SCHEMA DE AUTENTICACIÓN UNIFICADO
-- =====================================================
-- Este schema reemplaza y consolida:
-- - users (SQLAlchemy)
-- - usuarios_autorizados (asyncpg legacy)
-- - otp_users (nunca usado)
-- - otp_tokens (nunca usado)
-- - sessions (nunca usado)
-- =====================================================

-- 1. TABLA PRINCIPAL DE USUARIOS (Consolidada)
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,

    -- Autenticación Password
    password_hash VARCHAR(255),
    password_changed_at TIMESTAMP WITH TIME ZONE,

    -- Datos personales
    full_name VARCHAR(255) NOT NULL,
    avatar_url TEXT,

    -- Organización
    empresa_id UUID,
    company_name VARCHAR(255),
    department VARCHAR(100),

    -- Roles y permisos
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('super_admin', 'admin', 'manager', 'user', 'viewer')),
    permissions JSONB DEFAULT '[]'::jsonb,

    -- Estado de cuenta
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'blocked', 'deleted')),
    status_reason TEXT,
    status_changed_at TIMESTAMP WITH TIME ZONE,
    status_changed_by UUID,

    -- Aprobación (para usuarios que requieren revisión)
    approval_required BOOLEAN DEFAULT true,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID,
    rejection_reason TEXT,

    -- Método de autenticación preferido
    auth_method VARCHAR(20) DEFAULT 'otp' CHECK (auth_method IN ('password', 'otp', 'both', 'sso')),

    -- Seguridad
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    last_login_user_agent TEXT,

    -- Multi-tenant
    tenant_id UUID,
    allowed_empresas UUID[] DEFAULT ARRAY[]::UUID[],

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Índices para auth_users
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_status ON auth_users(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_auth_users_empresa ON auth_users(empresa_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_auth_users_role ON auth_users(role) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_auth_users_approval ON auth_users(approval_required, status) WHERE deleted_at IS NULL;

-- 2. CÓDIGOS OTP (Con TTL y rate limiting en DB)
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Referencia al usuario
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,

    -- El código OTP
    code VARCHAR(6) NOT NULL,
    code_hash VARCHAR(255), -- Hash del código para seguridad adicional

    -- Propósito del código
    purpose VARCHAR(50) DEFAULT 'login' CHECK (purpose IN ('login', 'verify_email', 'reset_password', 'change_email', 'confirm_action')),

    -- Estado
    used BOOLEAN DEFAULT false,
    used_at TIMESTAMP WITH TIME ZONE,

    -- Expiración
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Intentos de verificación
    verification_attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Metadata de seguridad
    requested_ip INET,
    requested_user_agent TEXT,
    verified_ip INET,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT code_format CHECK (code ~ '^[0-9]{6}$'),
    CONSTRAINT max_attempts_check CHECK (verification_attempts <= max_attempts + 1)
);

-- Índices para auth_otp_codes
CREATE INDEX IF NOT EXISTS idx_otp_user_id ON auth_otp_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_email ON auth_otp_codes(email);
CREATE INDEX IF NOT EXISTS idx_otp_expires ON auth_otp_codes(expires_at) WHERE used = false;
CREATE INDEX IF NOT EXISTS idx_otp_cleanup ON auth_otp_codes(created_at);

-- 3. SESIONES DE USUARIO (Stateful para control total)
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Referencia al usuario
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,

    -- Token de sesión (hash, nunca guardamos el token real)
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    token_prefix VARCHAR(8), -- Primeros 8 chars para identificación en logs

    -- Tipo de autenticación usada
    auth_method VARCHAR(20) NOT NULL CHECK (auth_method IN ('password', 'otp', 'refresh', 'sso')),

    -- Estado de la sesión
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_reason VARCHAR(100),

    -- Expiración
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Información del dispositivo
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    device_name VARCHAR(100),

    -- Geolocalización (opcional)
    geo_country VARCHAR(2),
    geo_city VARCHAR(100),

    -- Refresh token (para renovación)
    refresh_token_hash VARCHAR(255),
    refresh_expires_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para auth_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user ON auth_sessions(user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sessions_token ON auth_sessions(token_hash) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON auth_sessions(expires_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sessions_cleanup ON auth_sessions(expires_at);

-- 4. RATE LIMITING (En DB, no en memoria)
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificador (puede ser email, IP, o combinación)
    identifier VARCHAR(255) NOT NULL,
    identifier_type VARCHAR(20) NOT NULL CHECK (identifier_type IN ('email', 'ip', 'email_ip', 'user_id')),

    -- Acción que se está limitando
    action VARCHAR(50) NOT NULL CHECK (action IN ('login', 'otp_request', 'otp_verify', 'password_reset', 'register', 'api_call')),

    -- Contadores
    attempt_count INTEGER DEFAULT 1,
    first_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Bloqueo
    blocked_until TIMESTAMP WITH TIME ZONE,
    block_count INTEGER DEFAULT 0, -- Cuántas veces ha sido bloqueado

    -- Configuración
    window_minutes INTEGER DEFAULT 15,
    max_attempts INTEGER DEFAULT 5,
    block_duration_minutes INTEGER DEFAULT 15,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraint único por identifier + action
    CONSTRAINT unique_rate_limit UNIQUE (identifier, identifier_type, action)
);

-- Índices para auth_rate_limits
CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON auth_rate_limits(identifier, action);
CREATE INDEX IF NOT EXISTS idx_rate_limits_blocked ON auth_rate_limits(blocked_until);
CREATE INDEX IF NOT EXISTS idx_rate_limits_cleanup ON auth_rate_limits(last_attempt_at);

-- 5. AUDITORÍA DE AUTENTICACIÓN
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Referencia al usuario (puede ser NULL para intentos fallidos)
    user_id UUID REFERENCES auth_users(id) ON DELETE SET NULL,
    email VARCHAR(255),

    -- Acción realizada
    action VARCHAR(50) NOT NULL,
    action_result VARCHAR(20) NOT NULL CHECK (action_result IN ('success', 'failure', 'blocked', 'error')),

    -- Detalles del error/fallo
    failure_reason VARCHAR(255),
    error_code VARCHAR(50),

    -- Información de la solicitud
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),

    -- Geolocalización
    geo_country VARCHAR(2),
    geo_city VARCHAR(100),

    -- Metadata adicional
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para auth_audit_log (optimizados para queries de seguridad)
CREATE INDEX IF NOT EXISTS idx_audit_user ON auth_audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_email ON auth_audit_log(email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_ip ON auth_audit_log(ip_address, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON auth_audit_log(action, action_result, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_failures ON auth_audit_log(created_at DESC) WHERE action_result = 'failure';

-- 6. INVITACIONES DE USUARIO
-- =====================================================
CREATE TABLE IF NOT EXISTS auth_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Email invitado
    email VARCHAR(255) NOT NULL,

    -- Quién invitó
    invited_by UUID NOT NULL REFERENCES auth_users(id),

    -- Token de invitación
    token VARCHAR(255) NOT NULL UNIQUE,
    token_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Configuración del usuario invitado
    role VARCHAR(50) DEFAULT 'user',
    empresa_id UUID,
    department VARCHAR(100),
    permissions JSONB DEFAULT '[]'::jsonb,

    -- Estado
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'expired', 'revoked')),
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_user_id UUID REFERENCES auth_users(id),

    -- Metadata
    message TEXT, -- Mensaje personalizado de invitación
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para auth_invitations
CREATE INDEX IF NOT EXISTS idx_invitations_email ON auth_invitations(email) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_invitations_token ON auth_invitations(token) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_invitations_invited_by ON auth_invitations(invited_by);

-- 7. FUNCIONES DE UTILIDAD
-- =====================================================

-- Función para limpiar códigos OTP expirados
CREATE OR REPLACE FUNCTION cleanup_expired_otp_codes()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_otp_codes
    WHERE expires_at < NOW() - INTERVAL '1 hour'
       OR (used = true AND created_at < NOW() - INTERVAL '1 day');
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar sesiones expiradas
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE auth_sessions
    SET is_active = false, revoked_reason = 'expired'
    WHERE is_active = true AND expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Eliminar sesiones muy antiguas
    DELETE FROM auth_sessions
    WHERE is_active = false AND created_at < NOW() - INTERVAL '90 days';

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para limpiar rate limits antiguos
CREATE OR REPLACE FUNCTION cleanup_rate_limits()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth_rate_limits
    WHERE last_attempt_at < NOW() - INTERVAL '24 hours'
      AND (blocked_until IS NULL OR blocked_until < NOW());
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Función para verificar rate limit (retorna TRUE si está bloqueado)
CREATE OR REPLACE FUNCTION check_rate_limit(
    p_identifier VARCHAR(255),
    p_identifier_type VARCHAR(20),
    p_action VARCHAR(50),
    p_max_attempts INTEGER DEFAULT 5,
    p_window_minutes INTEGER DEFAULT 15,
    p_block_duration_minutes INTEGER DEFAULT 15
)
RETURNS TABLE (
    is_blocked BOOLEAN,
    attempts_remaining INTEGER,
    blocked_until TIMESTAMP WITH TIME ZONE,
    should_block BOOLEAN
) AS $$
DECLARE
    v_record auth_rate_limits%ROWTYPE;
    v_is_blocked BOOLEAN := false;
    v_attempts_remaining INTEGER;
    v_blocked_until TIMESTAMP WITH TIME ZONE;
    v_should_block BOOLEAN := false;
BEGIN
    -- Buscar registro existente
    SELECT * INTO v_record
    FROM auth_rate_limits
    WHERE identifier = p_identifier
      AND identifier_type = p_identifier_type
      AND action = p_action;

    IF NOT FOUND THEN
        -- Crear nuevo registro
        INSERT INTO auth_rate_limits (identifier, identifier_type, action, max_attempts, window_minutes, block_duration_minutes)
        VALUES (p_identifier, p_identifier_type, p_action, p_max_attempts, p_window_minutes, p_block_duration_minutes)
        RETURNING * INTO v_record;
    ELSE
        -- Verificar si está bloqueado
        IF v_record.blocked_until IS NOT NULL AND v_record.blocked_until > NOW() THEN
            v_is_blocked := true;
            v_blocked_until := v_record.blocked_until;
        ELSE
            -- Si la ventana expiró, resetear contador
            IF v_record.first_attempt_at < NOW() - (v_record.window_minutes || ' minutes')::INTERVAL THEN
                UPDATE auth_rate_limits
                SET attempt_count = 1,
                    first_attempt_at = NOW(),
                    last_attempt_at = NOW(),
                    blocked_until = NULL
                WHERE id = v_record.id
                RETURNING * INTO v_record;
            ELSE
                -- Incrementar contador
                UPDATE auth_rate_limits
                SET attempt_count = attempt_count + 1,
                    last_attempt_at = NOW()
                WHERE id = v_record.id
                RETURNING * INTO v_record;

                -- Verificar si debe bloquearse
                IF v_record.attempt_count >= p_max_attempts THEN
                    v_should_block := true;
                    v_blocked_until := NOW() + (p_block_duration_minutes || ' minutes')::INTERVAL;

                    UPDATE auth_rate_limits
                    SET blocked_until = v_blocked_until,
                        block_count = block_count + 1
                    WHERE id = v_record.id;
                END IF;
            END IF;
        END IF;
    END IF;

    v_attempts_remaining := GREATEST(0, p_max_attempts - v_record.attempt_count);

    RETURN QUERY SELECT v_is_blocked, v_attempts_remaining, v_blocked_until, v_should_block;
END;
$$ LANGUAGE plpgsql;

-- Función para registrar auditoría
CREATE OR REPLACE FUNCTION log_auth_event(
    p_user_id UUID,
    p_email VARCHAR(255),
    p_action VARCHAR(50),
    p_result VARCHAR(20),
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_failure_reason VARCHAR(255) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO auth_audit_log (user_id, email, action, action_result, ip_address, user_agent, failure_reason, metadata)
    VALUES (p_user_id, p_email, p_action, p_result, p_ip_address, p_user_agent, p_failure_reason, p_metadata)
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- 8. TRIGGERS
-- =====================================================

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_auth_users_updated_at
    BEFORE UPDATE ON auth_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. MIGRACIÓN DE DATOS EXISTENTES
-- =====================================================

-- Migrar usuarios de tabla 'users' a 'auth_users' (SKIP: Table users does not exist)
-- INSERT INTO auth_users (
--     id, email, email_verified, password_hash, full_name,
--     company_name, role, status, auth_method,
--     created_at, updated_at
-- )
-- SELECT ... (omitted)


-- Migrar usuarios de tabla 'usuarios_autorizados' a 'auth_users'
INSERT INTO auth_users (
    email, email_verified, full_name, company_name, role, status, auth_method, created_at
)
SELECT
    email,
    COALESCE(activo, false),
    COALESCE(nombre, email),
    empresa,
    COALESCE(rol, 'user'),
    CASE WHEN activo = true THEN 'active' ELSE 'pending' END,
    'otp',
    NOW()
FROM usuarios_autorizados
WHERE email IS NOT NULL
ON CONFLICT (email) DO UPDATE SET
    full_name = COALESCE(NULLIF(EXCLUDED.full_name, ''), auth_users.full_name),
    company_name = COALESCE(EXCLUDED.company_name, auth_users.company_name),
    updated_at = NOW();

-- 10. VISTAS ÚTILES
-- =====================================================

-- Vista de usuarios activos con estadísticas
CREATE OR REPLACE VIEW auth_users_summary AS
SELECT
    u.id,
    u.email,
    u.full_name,
    u.role,
    u.status,
    u.auth_method,
    u.last_login_at,
    u.created_at,
    (SELECT COUNT(*) FROM auth_sessions s WHERE s.user_id = u.id AND s.is_active = true) as active_sessions,
    (SELECT COUNT(*) FROM auth_audit_log a WHERE a.user_id = u.id AND a.action = 'login' AND a.action_result = 'failure' AND a.created_at > NOW() - INTERVAL '24 hours') as failed_logins_24h
FROM auth_users u
WHERE u.deleted_at IS NULL;

-- Vista de intentos de login sospechosos
CREATE OR REPLACE VIEW auth_suspicious_activity AS
SELECT
    email,
    ip_address,
    COUNT(*) as attempt_count,
    MIN(created_at) as first_attempt,
    MAX(created_at) as last_attempt,
    array_agg(DISTINCT action_result) as results
FROM auth_audit_log
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND action = 'login'
GROUP BY email, ip_address
HAVING COUNT(*) > 5
   OR COUNT(*) FILTER (WHERE action_result = 'failure') > 3;

-- 11. POLÍTICAS DE SEGURIDAD (RLS - Row Level Security)
-- =====================================================

-- Habilitar RLS en tablas sensibles
ALTER TABLE auth_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_audit_log ENABLE ROW LEVEL SECURITY;

-- Las políticas específicas se configuran según el rol de la aplicación
-- Por ahora, permitimos acceso total al rol de la aplicación
CREATE POLICY auth_users_app_policy ON auth_users FOR ALL USING (true);
CREATE POLICY auth_sessions_app_policy ON auth_sessions FOR ALL USING (true);
CREATE POLICY auth_audit_app_policy ON auth_audit_log FOR ALL USING (true);

-- 12. GRANTS
-- =====================================================
-- Estos se configurarían según el usuario de la base de datos
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;
