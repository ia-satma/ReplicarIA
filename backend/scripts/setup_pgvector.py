"""
Setup pgvector extension and add embedding column to knowledge_chunks table.
Run this script once to enable vector search capabilities.
"""

import os
import asyncio
import asyncpg

DATABASE_URL = os.environ.get('DATABASE_URL', '')


async def setup_pgvector():
    """Setup pgvector extension and add embedding column."""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return False
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🔧 Checking pgvector extension...")
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        
        if not exists:
            print("📦 Creating pgvector extension...")
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print("✅ pgvector extension created")
            except Exception as e:
                print(f"⚠️ Could not create pgvector extension: {e}")
                print("   This is expected on some PostgreSQL hosts.")
                print("   Vector search will use keyword fallback.")
                return False
        else:
            print("✅ pgvector extension already exists")
        
        print("\n🔧 Checking embedding column in knowledge_chunks...")
        
        has_column = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'knowledge_chunks' 
                AND column_name = 'embedding'
            )
        """)
        
        if not has_column:
            print("📦 Adding embedding column (vector(1536))...")
            await conn.execute("""
                ALTER TABLE knowledge_chunks 
                ADD COLUMN IF NOT EXISTS embedding vector(1536)
            """)
            print("✅ Embedding column added")
        else:
            print("✅ Embedding column already exists")
        
        print("\n🔧 Creating vector index...")
        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunks")
            
            await conn.execute("""
                DROP INDEX IF EXISTS idx_chunks_embedding_hnsw
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
                ON knowledge_chunks 
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            print(f"✅ IVFFlat index created ({count} chunks)")
        except Exception as e:
            print(f"⚠️ Could not create vector index: {e}")
            print("   Searches will still work but may be slower.")
        
        print("\n🔧 Setting up usage_tracking table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_tracking (
                id SERIAL PRIMARY KEY,
                empresa_id UUID NOT NULL,
                fecha DATE NOT NULL,
                requests_today INTEGER DEFAULT 0,
                tokens_today INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(empresa_id, fecha)
            )
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_empresa_fecha 
            ON usage_tracking(empresa_id, fecha)
        """)
        print("✅ usage_tracking table ready")
        
        print("\n" + "="*50)
        print("✅ pgvector setup completed successfully!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False
    finally:
        await conn.close()


async def check_status():
    """Check current pgvector status."""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        return
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        has_ext = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        
        has_column = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'knowledge_chunks' 
                AND column_name = 'embedding'
            )
        """)
        
        total_chunks = await conn.fetchval(
            "SELECT COUNT(*) FROM knowledge_chunks"
        )
        
        chunks_with_embedding = 0
        if has_column:
            chunks_with_embedding = await conn.fetchval(
                "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL"
            )
        
        print("\n📊 pgvector Status Report")
        print("="*40)
        print(f"Extension installed: {'✅ Yes' if has_ext else '❌ No'}")
        print(f"Embedding column exists: {'✅ Yes' if has_column else '❌ No'}")
        print(f"Total chunks: {total_chunks}")
        print(f"Chunks with embeddings: {chunks_with_embedding}")
        
        if total_chunks > 0:
            pct = (chunks_with_embedding / total_chunks) * 100
            print(f"Embedding coverage: {pct:.1f}%")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        asyncio.run(check_status())
    else:
        asyncio.run(setup_pgvector())
