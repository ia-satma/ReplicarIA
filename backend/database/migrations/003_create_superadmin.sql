-- =====================================================
-- REVISAR.IA - CREATE SUPER ADMIN USER
-- =====================================================
-- This migration creates the super_admin user in auth_users table
-- for password-based authentication (bypassing OTP)
-- =====================================================

-- 1. Ensure auth_users table exists
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('super_admin', 'admin', 'manager', 'user', 'viewer')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('active', 'pending', 'suspended', 'deleted')),
    auth_method VARCHAR(50) DEFAULT 'otp' CHECK (auth_method IN ('password', 'otp', 'both')),
    empresa_id UUID,
    company_name VARCHAR(255),
    email_verified BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    last_login_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    approved_by UUID,
    approval_required BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 2. Ensure auth_sessions table exists
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    token_prefix VARCHAR(10),
    auth_method VARCHAR(50) DEFAULT 'password',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for auth_sessions
CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(is_active, expires_at);

-- 3. Insert Super Admin User
-- Password: Sillybanana142# (bcrypt hashed)
INSERT INTO auth_users (
    email,
    full_name,
    password_hash,
    role,
    status,
    auth_method,
    email_verified,
    approval_required,
    company_name
) VALUES (
    'santiago@satma.mx',
    'Santiago De Santiago',
    '$2b$12$8QPA/6q8GvLn9TanuW60BOxJziS.n7AQOt6OLpkjpxemzvjLkm802',
    'super_admin',
    'active',
    'password',
    true,
    false,
    'SATMA'
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = 'super_admin',
    status = 'active',
    auth_method = 'password',
    email_verified = true,
    approval_required = false,
    updated_at = NOW();

-- 4. Also ensure user exists in usuarios_autorizados for OTP fallback
INSERT INTO usuarios_autorizados (email, nombre, empresa, rol, activo)
VALUES ('santiago@satma.mx', 'Santiago De Santiago', 'SATMA', 'super_admin', true)
ON CONFLICT (email) DO UPDATE SET
    activo = true,
    rol = 'super_admin',
    updated_at = NOW();

-- 5. Verify insertion
DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM auth_users WHERE email = 'santiago@satma.mx' AND role = 'super_admin';
    IF user_count = 1 THEN
        RAISE NOTICE '✅ Super Admin santiago@satma.mx created successfully';
    ELSE
        RAISE WARNING '❌ Super Admin creation may have failed';
    END IF;
END $$;
