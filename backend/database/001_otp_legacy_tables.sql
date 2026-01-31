-- =====================================================
-- REVISAR.IA - TABLAS LEGACY PARA OTP AUTHENTICATION
-- =====================================================
-- Estas tablas son requeridas por otp_auth_service.py
-- Crear estas tablas ANTES de usar el sistema OTP
-- =====================================================

-- 1. TABLA DE USUARIOS AUTORIZADOS
-- =====================================================
CREATE TABLE IF NOT EXISTS usuarios_autorizados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    empresa VARCHAR(255),
    rol VARCHAR(50) DEFAULT 'user' CHECK (rol IN ('super_admin', 'admin', 'manager', 'user', 'viewer')),
    activo BOOLEAN DEFAULT true,
    empresa_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_usuarios_autorizados_email ON usuarios_autorizados(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_autorizados_activo ON usuarios_autorizados(activo);
CREATE INDEX IF NOT EXISTS idx_usuarios_autorizados_rol ON usuarios_autorizados(rol);

-- 2. TABLA DE CÓDIGOS OTP
-- =====================================================
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

-- Índices
CREATE INDEX IF NOT EXISTS idx_codigos_otp_email ON codigos_otp(email);
CREATE INDEX IF NOT EXISTS idx_codigos_otp_expiracion ON codigos_otp(fecha_expiracion);
CREATE INDEX IF NOT EXISTS idx_codigos_otp_usado ON codigos_otp(usado);

-- 3. TABLA DE SESIONES OTP
-- =====================================================
CREATE TABLE IF NOT EXISTS sesiones_otp (
    id VARCHAR(50) PRIMARY KEY,
    usuario_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    fecha_expiracion TIMESTAMPTZ NOT NULL
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_sesiones_otp_token ON sesiones_otp(token);
CREATE INDEX IF NOT EXISTS idx_sesiones_otp_activa ON sesiones_otp(activa);
CREATE INDEX IF NOT EXISTS idx_sesiones_otp_usuario ON sesiones_otp(usuario_id);

-- 4. INSERTAR USUARIO ADMINISTRADOR POR DEFECTO
-- =====================================================
-- Cambia estos valores según tu configuración
INSERT INTO usuarios_autorizados (email, nombre, empresa, rol, activo)
VALUES
    ('ia@satma.mx', 'Administrador SATMA', 'SATMA', 'super_admin', true),
    ('admin@revisar-ia.com', 'Administrador Sistema', 'Revisar.IA', 'admin', true)
ON CONFLICT (email) DO UPDATE SET
    activo = true,
    rol = EXCLUDED.rol,
    updated_at = NOW();

-- 5. FUNCIÓN PARA LIMPIAR OTP EXPIRADOS
-- =====================================================
CREATE OR REPLACE FUNCTION limpiar_otp_expirados()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM codigos_otp WHERE fecha_expiracion < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 6. FUNCIÓN PARA LIMPIAR SESIONES EXPIRADAS
-- =====================================================
CREATE OR REPLACE FUNCTION limpiar_sesiones_expiradas()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE sesiones_otp SET activa = false WHERE fecha_expiracion < NOW() AND activa = true;
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- 7. TRIGGER PARA ACTUALIZAR updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_usuarios_autorizados_updated_at ON usuarios_autorizados;
CREATE TRIGGER set_usuarios_autorizados_updated_at
    BEFORE UPDATE ON usuarios_autorizados
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_updated_at();
