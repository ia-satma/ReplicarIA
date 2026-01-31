#!/usr/bin/env python3
"""
RESET DEMO DATA - Borra todos los datos de prueba de la base de datos
Preserva: usuarios administradores, configuración del sistema
"""

import asyncio
import os
import logging
from datetime import datetime

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')


def get_clean_database_url() -> str:
    """Limpia la URL de la base de datos para asyncpg."""
    url = DATABASE_URL
    if not url:
        return ''

    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    import re
    url = re.sub(r'[?&]sslmode=[^&]*', '', url)

    return url


async def reset_demo_data():
    """Borra todos los datos demo de la base de datos."""

    db_url = get_clean_database_url()
    if not db_url:
        logger.error("DATABASE_URL no configurada")
        return False

    logger.info("=" * 60)
    logger.info("RESET DE DATOS DEMO")
    logger.info("=" * 60)
    logger.info(f"Fecha: {datetime.now().isoformat()}")

    try:
        conn = await asyncpg.connect(db_url, ssl='require')
        logger.info("✅ Conectado a la base de datos")

        # Obtener lista de tablas
        tables = await conn.fetch('''
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        ''')

        logger.info(f"\n📋 Tablas encontradas: {len(tables)}")
        for t in tables:
            logger.info(f"   - {t['table_name']}")

        # Tablas a limpiar (orden importante por foreign keys)
        tables_to_clean = [
            # Historial y logs primero
            'clientes_historial',
            'clientes_interacciones',
            'clientes_contexto',
            'clientes_documentos',
            'proveedores_scoring',
            'df_proveedores',
            'df_documents',
            'df_metadata',

            # Knowledge base
            'kb_chunk_agente',
            'kb_chunks',
            'kb_documentos',
            'kb_metricas',

            # Proyectos
            'projects',
            'project_documents',
            'project_notes',

            # Entidades principales (al final)
            'clientes',
            'proveedores',

            # Auth cleanup (excepto admins)
            'auth_otp_codes',
            'auth_rate_limits',
            'auth_audit_log',
        ]

        logger.info("\n🗑️  Limpiando tablas...")

        for table in tables_to_clean:
            try:
                # Verificar si la tabla existe
                exists = await conn.fetchval('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = $1
                    )
                ''', table)

                if exists:
                    # Contar registros antes
                    count_before = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')

                    # Borrar datos
                    await conn.execute(f'DELETE FROM {table}')

                    logger.info(f"   ✓ {table}: {count_before} registros eliminados")
                else:
                    logger.info(f"   - {table}: no existe")

            except Exception as e:
                logger.warning(f"   ⚠ {table}: {str(e)[:50]}")

        # Limpiar usuarios no-admin (preservar admins)
        try:
            admin_emails = ['ia@satma.mx', 'admin@revisar-ia.com']
            deleted_users = await conn.execute('''
                DELETE FROM auth_users
                WHERE email NOT IN (SELECT unnest($1::text[]))
                AND role NOT IN ('super_admin', 'admin')
            ''', admin_emails)
            logger.info(f"   ✓ auth_users: usuarios no-admin eliminados")
        except Exception as e:
            logger.warning(f"   ⚠ auth_users: {e}")

        # Limpiar sesiones viejas
        try:
            await conn.execute('''
                DELETE FROM auth_sessions WHERE expires_at < NOW()
            ''')
            logger.info(f"   ✓ auth_sessions: sesiones expiradas eliminadas")
        except Exception as e:
            logger.warning(f"   ⚠ auth_sessions: {e}")

        await conn.close()

        logger.info("\n" + "=" * 60)
        logger.info("✅ RESET COMPLETADO")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


async def show_current_counts():
    """Muestra conteos actuales de las tablas."""

    db_url = get_clean_database_url()
    if not db_url:
        return

    try:
        conn = await asyncpg.connect(db_url, ssl='require')

        tables = ['clientes', 'proveedores', 'projects', 'auth_users', 'kb_documentos']

        logger.info("\n📊 Conteos actuales:")
        for table in tables:
            try:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
                logger.info(f"   {table}: {count}")
            except:
                pass

        await conn.close()

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == '__main__':
    print("\n⚠️  ADVERTENCIA: Este script borrará TODOS los datos demo.")
    print("Los administradores y configuración se preservarán.\n")

    confirm = input("¿Continuar? (escribir 'CONFIRMAR'): ")

    if confirm == 'CONFIRMAR':
        asyncio.run(show_current_counts())
        asyncio.run(reset_demo_data())
        asyncio.run(show_current_counts())
    else:
        print("Cancelado.")
