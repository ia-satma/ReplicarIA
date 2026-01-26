"""
Script de migración MongoDB → PostgreSQL.
Ejecutar una sola vez después de crear las tablas.

Uso:
    python -m scripts.migrate_mongo_to_postgres
    
    # Dry run (solo muestra qué se migraría):
    python -m scripts.migrate_mongo_to_postgres --dry-run
    
    # Solo una colección:
    python -m scripts.migrate_mongo_to_postgres --collection projects
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Any
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    print("⚠️  Motor no instalado. Instala con: pip install motor")

DATABASE_URL = os.getenv("DATABASE_URL")
MONGO_URI = os.getenv("MONGO_URL") or os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")


class MigrationStats:
    def __init__(self):
        self.collections = {}
    
    def add(self, collection: str, success: bool):
        if collection not in self.collections:
            self.collections[collection] = {"success": 0, "failed": 0}
        
        if success:
            self.collections[collection]["success"] += 1
        else:
            self.collections[collection]["failed"] += 1
    
    def print_summary(self):
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("=" * 60)
        
        total_success = 0
        total_failed = 0
        
        for collection, counts in self.collections.items():
            print(f"  {collection}:")
            print(f"    ✅ Migrados: {counts['success']}")
            print(f"    ❌ Fallidos: {counts['failed']}")
            total_success += counts["success"]
            total_failed += counts["failed"]
        
        print("-" * 60)
        print(f"  TOTAL: {total_success} migrados, {total_failed} fallidos")


def convert_objectid(obj: Any) -> Any:
    """Convierte ObjectId de MongoDB a string."""
    if obj is None:
        return None
    if hasattr(obj, '__str__') and type(obj).__name__ == 'ObjectId':
        return str(obj)
    if isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_objectid(i) for i in obj]
    return obj


def mongo_id_to_uuid(mongo_id: Any) -> str:
    """
    Converts a MongoDB ObjectId to a valid UUID.
    If already a valid UUID string, returns it as-is.
    Otherwise generates a deterministic UUID from the ObjectId hex.
    """
    if mongo_id is None:
        return str(uuid.uuid4())
    
    id_str = str(mongo_id)
    
    try:
        uuid.UUID(id_str)
        return id_str
    except (ValueError, AttributeError):
        pass
    
    try:
        hex_str = id_str.ljust(32, '0')[:32]
        formatted = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"
        uuid.UUID(formatted)
        return formatted
    except (ValueError, AttributeError):
        return str(uuid.uuid4())


def safe_json(obj: Any) -> str:
    """Convierte a JSON de forma segura."""
    try:
        converted = convert_objectid(obj)
        return json.dumps(converted, default=str)
    except:
        return '{}'


async def migrate_projects(mongo_db, pg_conn, stats: MigrationStats, dry_run: bool):
    """Migrar colección projects."""
    print("\n📦 Migrando projects...")
    
    cursor = mongo_db.projects.find({})
    count = 0
    
    async for doc in cursor:
        count += 1
        
        if dry_run:
            print(f"  [DRY] Proyecto: {doc.get('nombre', 'Sin nombre')}")
            stats.add("projects", True)
            continue
        
        try:
            project_id = mongo_id_to_uuid(doc.get("_id"))
            empresa_id = doc.get("empresa_id")
            
            if not empresa_id:
                print(f"  ⚠️  Proyecto sin empresa_id: {project_id}")
                stats.add("projects", False)
                continue
            
            await pg_conn.execute("""
                INSERT INTO projects (
                    id, empresa_id, nombre, descripcion, tipo,
                    fase_actual, estado, proveedor_rfc, proveedor_nombre,
                    monto_total, moneda, metadata, datos_sib,
                    risk_score, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3, $4, $5,
                    $6, $7, $8, $9,
                    $10, $11, $12::jsonb, $13::jsonb,
                    $14, $15, $16
                )
                ON CONFLICT (id) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    fase_actual = EXCLUDED.fase_actual,
                    estado = EXCLUDED.estado,
                    updated_at = NOW()
            """,
                project_id,
                empresa_id,
                doc.get("nombre", "Sin nombre"),
                doc.get("descripcion"),
                doc.get("tipo"),
                doc.get("fase_actual", 0),
                doc.get("estado", "activo"),
                doc.get("proveedor_rfc"),
                doc.get("proveedor_nombre"),
                doc.get("monto_total"),
                doc.get("moneda", "MXN"),
                safe_json(doc.get("metadata", {})),
                safe_json(doc.get("datos_sib", {})),
                doc.get("risk_score"),
                doc.get("created_at", datetime.utcnow()),
                doc.get("updated_at", datetime.utcnow())
            )
            
            stats.add("projects", True)
            
        except Exception as e:
            print(f"  ❌ Error en proyecto {doc.get('_id')}: {e}")
            stats.add("projects", False)
    
    print(f"  Procesados: {count} proyectos")


async def migrate_deliberations(mongo_db, pg_conn, stats: MigrationStats, dry_run: bool):
    """Migrar colección deliberations."""
    print("\n💬 Migrando deliberations...")
    
    cursor = mongo_db.deliberations.find({})
    count = 0
    
    async for doc in cursor:
        count += 1
        
        if dry_run:
            print(f"  [DRY] Deliberación: {doc.get('agente_id')} - Fase {doc.get('fase')}")
            stats.add("deliberations", True)
            continue
        
        try:
            await pg_conn.execute("""
                INSERT INTO deliberations (
                    id, project_id, empresa_id, fase, agente_id,
                    tipo, contenido, resumen, decision,
                    referencias, tokens_usados, created_at
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5,
                    $6, $7, $8, $9::jsonb,
                    $10::jsonb, $11, $12
                )
                ON CONFLICT (id) DO NOTHING
            """,
                mongo_id_to_uuid(doc.get("_id")),
                mongo_id_to_uuid(doc.get("project_id")) if doc.get("project_id") else None,
                doc.get("empresa_id"),
                doc.get("fase", 0),
                doc.get("agente_id", "UNKNOWN"),
                doc.get("tipo", "opinion"),
                doc.get("contenido", ""),
                doc.get("resumen"),
                safe_json(doc.get("decision", {})),
                safe_json(doc.get("referencias", [])),
                doc.get("tokens_usados"),
                doc.get("created_at", datetime.utcnow())
            )
            
            stats.add("deliberations", True)
            
        except Exception as e:
            print(f"  ❌ Error en deliberación {doc.get('_id')}: {e}")
            stats.add("deliberations", False)
    
    print(f"  Procesadas: {count} deliberaciones")


async def migrate_interactions(mongo_db, pg_conn, stats: MigrationStats, dry_run: bool):
    """Migrar colección agent_interactions."""
    print("\n🤖 Migrando agent_interactions...")
    
    cursor = mongo_db.agent_interactions.find({})
    count = 0
    
    async for doc in cursor:
        count += 1
        
        if dry_run:
            stats.add("agent_interactions", True)
            continue
        
        try:
            await pg_conn.execute("""
                INSERT INTO agent_interactions (
                    id, project_id, empresa_id, user_id, session_id,
                    agente_id, user_message, agent_response,
                    tokens_in, tokens_out, latency_ms, modelo_usado,
                    rag_chunks_used, metadata, created_at
                ) VALUES (
                    $1::uuid, $2::uuid, $3, $4, $5,
                    $6, $7, $8,
                    $9, $10, $11, $12,
                    $13::jsonb, $14::jsonb, $15
                )
                ON CONFLICT (id) DO NOTHING
            """,
                mongo_id_to_uuid(doc.get("_id")),
                mongo_id_to_uuid(doc.get("project_id")) if doc.get("project_id") else None,
                doc.get("empresa_id"),
                doc.get("user_id"),
                doc.get("session_id"),
                doc.get("agente_id", "UNKNOWN"),
                doc.get("user_message"),
                doc.get("agent_response"),
                doc.get("tokens_in"),
                doc.get("tokens_out"),
                doc.get("latency_ms"),
                doc.get("modelo_usado"),
                safe_json(doc.get("rag_chunks_used", [])),
                safe_json(doc.get("metadata", {})),
                doc.get("created_at", datetime.utcnow())
            )
            
            stats.add("agent_interactions", True)
            
        except Exception as e:
            print(f"  ❌ Error en interaction {doc.get('_id')}: {e}")
            stats.add("agent_interactions", False)
    
    print(f"  Procesadas: {count} interacciones")


async def migrate_durezza_suppliers(mongo_db, pg_conn, stats: MigrationStats, dry_run: bool):
    """Migrar colección durezza_suppliers a proveedores_scoring."""
    print("\n📊 Migrando durezza_suppliers → proveedores_scoring...")
    
    cursor = mongo_db.durezza_suppliers.find({})
    count = 0
    
    async for doc in cursor:
        count += 1
        
        if dry_run:
            print(f"  [DRY] Proveedor: {doc.get('rfc')}")
            stats.add("durezza_suppliers", True)
            continue
        
        try:
            await pg_conn.execute("""
                INSERT INTO proveedores_scoring (
                    id, empresa_id, proveedor_rfc, proveedor_nombre,
                    efos_status, efos_verificado_at, efos_detalle,
                    score_total, score_fiscal, score_financiero,
                    scores_detalle, alertas, metadata,
                    created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3, $4,
                    $5, $6, $7::jsonb,
                    $8, $9, $10,
                    $11::jsonb, $12::jsonb, $13::jsonb,
                    $14, $15
                )
                ON CONFLICT (empresa_id, proveedor_rfc) DO UPDATE SET
                    score_total = EXCLUDED.score_total,
                    efos_status = EXCLUDED.efos_status,
                    updated_at = NOW()
            """,
                mongo_id_to_uuid(doc.get("_id")),
                doc.get("empresa_id"),
                doc.get("rfc"),
                doc.get("nombre"),
                doc.get("efos_status"),
                doc.get("efos_verificado_at"),
                safe_json(doc.get("efos_detalle", {})),
                doc.get("score_total"),
                doc.get("score_fiscal"),
                doc.get("score_financiero"),
                safe_json(doc.get("scores_detalle", {})),
                safe_json(doc.get("alertas", [])),
                safe_json(doc.get("metadata", {})),
                doc.get("created_at", datetime.utcnow()),
                doc.get("updated_at", datetime.utcnow())
            )
            
            stats.add("durezza_suppliers", True)
            
        except Exception as e:
            print(f"  ❌ Error en proveedor {doc.get('rfc')}: {e}")
            stats.add("durezza_suppliers", False)
    
    print(f"  Procesados: {count} proveedores")


async def run_migration(
    dry_run: bool = False,
    collection: Optional[str] = None
):
    """Ejecuta la migración completa."""
    
    print("=" * 60)
    print("🚀 MIGRACIÓN MONGODB → POSTGRESQL")
    print("=" * 60)
    
    if dry_run:
        print("⚠️  MODO DRY RUN - No se guardarán cambios")
    
    if not MOTOR_AVAILABLE:
        print("❌ Motor no disponible. Instala con: pip install motor")
        return
    
    if not MONGO_URI:
        print("❌ MONGO_URI no configurada")
        print("   Esta migración requiere una conexión a MongoDB existente.")
        print("   Si no tienes MongoDB, no hay datos que migrar.")
        return
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada")
        return
    
    print("\n📡 Conectando a MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    mongo_db = mongo_client.get_default_database() or mongo_client.revisar_ia
    print(f"   Base de datos: {mongo_db.name}")
    
    print("📡 Conectando a PostgreSQL...")
    pg_conn = await asyncpg.connect(DATABASE_URL)
    print("   Conectado ✓")
    
    stats = MigrationStats()
    
    collections_to_migrate = {
        "projects": migrate_projects,
        "deliberations": migrate_deliberations,
        "agent_interactions": migrate_interactions,
        "durezza_suppliers": migrate_durezza_suppliers,
    }
    
    if collection:
        if collection in collections_to_migrate:
            await collections_to_migrate[collection](mongo_db, pg_conn, stats, dry_run)
        else:
            print(f"❌ Colección desconocida: {collection}")
            print(f"   Disponibles: {', '.join(collections_to_migrate.keys())}")
    else:
        for name, migrate_func in collections_to_migrate.items():
            try:
                await migrate_func(mongo_db, pg_conn, stats, dry_run)
            except Exception as e:
                print(f"❌ Error migrando {name}: {e}")
    
    await pg_conn.close()
    mongo_client.close()
    
    stats.print_summary()
    
    if dry_run:
        print("\n⚠️  Esto fue un DRY RUN. Ejecuta sin --dry-run para aplicar cambios.")
    else:
        print("\n✅ Migración completada!")
        print("   Siguiente paso: Actualizar servicios para usar PostgreSQL")


def main():
    parser = argparse.ArgumentParser(description="Migrar MongoDB a PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se migraría")
    parser.add_argument("--collection", help="Migrar solo una colección específica")
    
    args = parser.parse_args()
    
    asyncio.run(run_migration(
        dry_run=args.dry_run,
        collection=args.collection
    ))


if __name__ == "__main__":
    main()
