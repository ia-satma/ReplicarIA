"""
REVISAR.IA - Inicialización de Base de Datos
============================================

Este módulo maneja:
1. Ejecución del schema de autenticación
2. Migración de usuarios existentes
3. Seeding de administradores
4. Health checks de base de datos

Es idempotente - puede ejecutarse múltiples veces sin problemas.
"""

import os
import asyncio
import logging
import bcrypt
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

import asyncpg

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================

DATABASE_URL = os.environ.get('DATABASE_URL', '')


def get_clean_database_url() -> str:
    """Limpia la URL de la base de datos para asyncpg."""
    url = DATABASE_URL
    if not url:
        return ''

    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    # Remover sslmode (asyncpg lo maneja diferente)
    if '?sslmode=' in url or '&sslmode=' in url:
        import re
        url = re.sub(r'[?&]sslmode=[^&]*', '', url)

    return url


# ============================================================
# VERIFICACIÓN DE TABLAS
# ============================================================

async def check_table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    """Verifica si una tabla existe."""
    result = await conn.fetchval('''
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = $1
        )
    ''', table_name)
    return result


async def get_existing_tables(conn: asyncpg.Connection) -> List[str]:
    """Obtiene lista de tablas existentes."""
    rows = await conn.fetch('''
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    ''')
    return [row['table_name'] for row in rows]


# ============================================================
# EJECUCIÓN DE SCHEMA
# ============================================================

async def execute_auth_schema(conn: asyncpg.Connection) -> bool:
    """Ejecuta el schema de autenticación."""
    schema_path = os.path.join(
        os.path.dirname(__file__), '..', 'database', 'auth_schema.sql'
    )

    if not os.path.exists(schema_path):
        logger.warning(f"Schema file no encontrado: {schema_path}")
        return False

    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Ejecutar en bloques para manejar errores individuales
        statements = schema_sql.split(';')
        executed = 0
        errors = 0

        for statement in statements:
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue

            try:
                await conn.execute(statement)
                executed += 1
            except asyncpg.DuplicateTableError:
                # Tabla ya existe, OK
                pass
            except asyncpg.DuplicateObjectError:
                # Índice/función ya existe, OK
                pass
            except asyncpg.UndefinedTableError as e:
                # Tabla no existe para migración, OK
                if 'users' in str(e) or 'usuarios_autorizados' in str(e):
                    pass
                else:
                    logger.debug(f"Tabla no existe (OK): {e}")
            except Exception as e:
                error_msg = str(e).lower()
                # Ignorar errores esperados
                if 'already exists' in error_msg or 'does not exist' in error_msg:
                    pass
                else:
                    logger.warning(f"Error ejecutando statement: {e}")
                    errors += 1

        logger.info(f"Schema ejecutado: {executed} statements, {errors} errores menores")
        return True

    except Exception as e:
        logger.error(f"Error ejecutando schema: {e}")
        return False


# ============================================================
# SEEDING DE ADMINISTRADORES
# ============================================================

def get_admin_configs() -> List[Dict[str, str]]:
    """Obtiene configuración de administradores desde variables de entorno."""
    admins = []

    # Admin principal
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_email and admin_password:
        admins.append({
            'email': admin_email.lower().strip(),
            'password': admin_password,
            'name': os.environ.get('ADMIN_NAME', 'Administrador'),
            'company': os.environ.get('ADMIN_COMPANY', 'Revisar.IA')
        })

    # Admins adicionales (2-9)
    for i in range(2, 10):
        email = os.environ.get(f'ADMIN_EMAIL_{i}')
        password = os.environ.get(f'ADMIN_PASSWORD_{i}')
        if email and password:
            admins.append({
                'email': email.lower().strip(),
                'password': password,
                'name': os.environ.get(f'ADMIN_NAME_{i}', f'Admin {i}'),
                'company': os.environ.get(f'ADMIN_COMPANY_{i}', 'Revisar.IA')
            })

    return admins


async def seed_admin_users(conn: asyncpg.Connection) -> int:
    """
    Crea o actualiza usuarios administradores.

    - Usa UPSERT para ser idempotente
    - Siempre actualiza la contraseña
    - Activa la cuenta automáticamente

    Returns:
        Número de admins procesados
    """
    admins = get_admin_configs()

    if not admins:
        logger.warning("⚠️ No hay administradores configurados en variables de entorno")
        logger.warning("   Configura ADMIN_EMAIL y ADMIN_PASSWORD para crear admin")
        return 0

    processed = 0

    for admin in admins:
        try:
            # Hash de contraseña
            password_hash = bcrypt.hashpw(
                admin['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            # UPSERT: crear o actualizar
            await conn.execute('''
                INSERT INTO auth_users (
                    email, password_hash, full_name, company_name,
                    role, status, auth_method, email_verified, approval_required
                ) VALUES ($1, $2, $3, $4, 'admin', 'active', 'password', true, false)
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = $2,
                    full_name = COALESCE(NULLIF($3, ''), auth_users.full_name),
                    company_name = COALESCE(NULLIF($4, ''), auth_users.company_name),
                    role = 'admin',
                    status = 'active',
                    updated_at = NOW()
            ''', admin['email'], password_hash, admin['name'], admin['company'])

            logger.info(f"✅ Admin configurado: {admin['email']}")
            processed += 1

        except Exception as e:
            logger.error(f"❌ Error configurando admin {admin['email']}: {e}")

    return processed


# ============================================================
# MIGRACIÓN DE USUARIOS EXISTENTES
# ============================================================

async def migrate_legacy_users(conn: asyncpg.Connection) -> Tuple[int, int]:
    """
    Migra usuarios de las tablas legacy a auth_users.

    Returns:
        (usuarios_migrados_de_users, usuarios_migrados_de_usuarios_autorizados)
    """
    migrated_users = 0
    migrated_otp = 0

    # 1. Migrar de 'users' (tabla SQLAlchemy)
    if await check_table_exists(conn, 'users'):
        try:
            result = await conn.execute('''
                INSERT INTO auth_users (
                    email, email_verified, password_hash, full_name,
                    company_name, role, status, auth_method,
                    created_at, updated_at
                )
                SELECT
                    LOWER(email),
                    COALESCE(is_active, false),
                    password_hash,
                    COALESCE(full_name, email),
                    company,
                    COALESCE(role, 'user'),
                    CASE
                        WHEN approval_status = 'approved' AND is_active = true THEN 'active'
                        WHEN approval_status = 'rejected' THEN 'blocked'
                        ELSE 'pending'
                    END,
                    CASE WHEN password_hash IS NOT NULL THEN 'password' ELSE 'otp' END,
                    COALESCE(created_at, NOW()),
                    COALESCE(updated_at, NOW())
                FROM users
                WHERE email IS NOT NULL
                ON CONFLICT (email) DO UPDATE SET
                    password_hash = COALESCE(EXCLUDED.password_hash, auth_users.password_hash),
                    full_name = COALESCE(NULLIF(EXCLUDED.full_name, ''), auth_users.full_name),
                    updated_at = NOW()
            ''')
            migrated_users = int(result.split()[-1]) if 'INSERT' in result else 0
            if migrated_users > 0:
                logger.info(f"Migrados {migrated_users} usuarios de tabla 'users'")
        except Exception as e:
            logger.warning(f"No se pudo migrar de 'users': {e}")

    # 2. Migrar de 'usuarios_autorizados' (tabla OTP legacy)
    if await check_table_exists(conn, 'usuarios_autorizados'):
        try:
            result = await conn.execute('''
                INSERT INTO auth_users (
                    email, email_verified, full_name, company_name,
                    role, status, auth_method, created_at
                )
                SELECT
                    LOWER(email),
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
                    updated_at = NOW()
            ''')
            migrated_otp = int(result.split()[-1]) if 'INSERT' in result else 0
            if migrated_otp > 0:
                logger.info(f"Migrados {migrated_otp} usuarios de tabla 'usuarios_autorizados'")
        except Exception as e:
            logger.warning(f"No se pudo migrar de 'usuarios_autorizados': {e}")

    return migrated_users, migrated_otp


# ============================================================
# INICIALIZACIÓN PRINCIPAL
# ============================================================

async def initialize_database() -> Dict[str, Any]:
    """
    Inicializa la base de datos completa.

    Este método es idempotente y puede ejecutarse múltiples veces.

    Returns:
        Diccionario con el resultado de la inicialización
    """
    result = {
        'success': False,
        'database_connected': False,
        'schema_executed': False,
        'admins_created': 0,
        'users_migrated': 0,
        'errors': []
    }

    db_url = get_clean_database_url()
    if not db_url:
        result['errors'].append("DATABASE_URL no configurado")
        logger.error("❌ DATABASE_URL no está configurado")
        return result

    conn = None
    try:
        # Conectar a la base de datos
        conn = await asyncpg.connect(db_url)
        result['database_connected'] = True
        logger.info("✅ Conexión a base de datos establecida")

        # Verificar si auth_users existe
        auth_users_exists = await check_table_exists(conn, 'auth_users')

        if not auth_users_exists:
            logger.info("📦 Ejecutando schema de autenticación...")
            schema_ok = await execute_auth_schema(conn)
            result['schema_executed'] = schema_ok
            if not schema_ok:
                result['errors'].append("Error ejecutando schema")
        else:
            result['schema_executed'] = True
            logger.info("✅ Tablas de autenticación ya existen")

        # Migrar usuarios legacy
        if result['schema_executed']:
            migrated = await migrate_legacy_users(conn)
            result['users_migrated'] = sum(migrated)

        # Crear/actualizar admins
        if result['schema_executed']:
            admins = await seed_admin_users(conn)
            result['admins_created'] = admins

        result['success'] = result['schema_executed']

        # Log resumen
        logger.info("=" * 50)
        logger.info("INICIALIZACIÓN DE BASE DE DATOS COMPLETADA")
        logger.info("=" * 50)
        logger.info(f"  Schema: {'✅' if result['schema_executed'] else '❌'}")
        logger.info(f"  Admins: {result['admins_created']}")
        logger.info(f"  Migrados: {result['users_migrated']}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        result['errors'].append(str(e))
    finally:
        if conn:
            await conn.close()

    return result


async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado de la base de datos.
    """
    db_url = get_clean_database_url()
    if not db_url:
        return {
            'status': 'error',
            'message': 'DATABASE_URL no configurado'
        }

    try:
        conn = await asyncpg.connect(db_url)
        try:
            # Ping
            await conn.fetchval('SELECT 1')

            # Verificar tablas de auth
            tables = await conn.fetch('''
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'auth_%'
            ''')

            # Contar usuarios
            user_count = await conn.fetchval('SELECT COUNT(*) FROM auth_users WHERE deleted_at IS NULL')

            return {
                'status': 'healthy',
                'tables': [row['table_name'] for row in tables],
                'user_count': user_count
            }
        finally:
            await conn.close()

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


# ============================================================
# COMPATIBILIDAD CON SISTEMA LEGACY
# ============================================================

async def sync_to_legacy_tables(user_email: str, user_data: Dict) -> bool:
    """
    Sincroniza un usuario a las tablas legacy para compatibilidad.

    Esto permite que el código viejo siga funcionando mientras se migra.
    """
    db_url = get_clean_database_url()
    if not db_url:
        return False

    try:
        conn = await asyncpg.connect(db_url)
        try:
            # Sincronizar a usuarios_autorizados
            if await check_table_exists(conn, 'usuarios_autorizados'):
                await conn.execute('''
                    INSERT INTO usuarios_autorizados (id, email, nombre, empresa, rol, activo)
                    VALUES (gen_random_uuid()::text, $1, $2, $3, $4, true)
                    ON CONFLICT (email) DO UPDATE SET
                        nombre = $2,
                        empresa = $3,
                        rol = $4,
                        activo = true
                ''', user_email, user_data.get('full_name', ''),
                    user_data.get('company', ''), user_data.get('role', 'user'))

            # Sincronizar a users
            if await check_table_exists(conn, 'users'):
                await conn.execute('''
                    INSERT INTO users (id, email, full_name, company, role, is_active, approval_status)
                    VALUES (gen_random_uuid()::text, $1, $2, $3, $4, true, 'approved')
                    ON CONFLICT (email) DO UPDATE SET
                        full_name = $2,
                        company = $3,
                        role = $4,
                        is_active = true,
                        approval_status = 'approved'
                ''', user_email, user_data.get('full_name', ''),
                    user_data.get('company', ''), user_data.get('role', 'user'))

            return True
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Error sincronizando a tablas legacy: {e}")
        return False


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    """Ejecutar inicialización desde línea de comandos."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    async def main():
        result = await initialize_database()
        if result['success']:
            print("\n✅ Inicialización completada exitosamente")
            return 0
        else:
            print(f"\n❌ Errores: {result['errors']}")
            return 1

    sys.exit(asyncio.run(main()))
