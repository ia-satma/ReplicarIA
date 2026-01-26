"""
Health check del sistema Revisar.IA.
Ejecutar: python backend/scripts/health_check.py
"""
import asyncio
import asyncpg
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    print("=" * 50)
    print(f"HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        tables = [
            ('empresas', 'Empresas/Tenants'),
            ('users', 'Usuarios'),
            ('projects', 'Proyectos'),
            ('deliberations', 'Deliberaciones'),
            ('knowledge_chunks', 'Chunks RAG'),
            ('knowledge_documents', 'Documentos KB'),
            ('usage_tracking', 'Tracking de Uso'),
            ('planes', 'Planes de Suscripción'),
            ('defense_files', 'Expedientes de Defensa'),
        ]
        
        print("\n📊 TABLAS POSTGRESQL:")
        for table, desc in tables:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"  ✅ {desc}: {count} registros")
            except Exception as e:
                print(f"  ⚠️ {desc}: No existe o error")
        
        has_vector = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        print(f"\n🔍 PGVECTOR: {'✅ Instalado' if has_vector else '❌ Falta'}")
        
        total = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
        with_emb = await conn.fetchval(
            "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL"
        )
        pct = (with_emb / total * 100) if total > 0 else 0
        status = "✅" if pct > 80 or total == 0 else "⚠️" if pct > 50 else "❌"
        print(f"\n📈 EMBEDDINGS: {status} {with_emb}/{total} ({pct:.1f}%)")
        if total == 0:
            print("   (Sube documentos al Repositorio para activar RAG)")
        
        planes = await conn.fetchval("SELECT COUNT(*) FROM planes")
        print(f"\n💰 PLANES: {'✅' if planes >= 4 else '⚠️'} {planes} configurados")
        
        idx_count = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE schemaname = 'public'
        """)
        print(f"\n🔧 ÍNDICES: ✅ {idx_count} índices en PostgreSQL")
        
        await conn.close()
        
        print("\n" + "=" * 50)
        print("✅ HEALTH CHECK COMPLETADO - Sistema operativo")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
