"""
Migration script to backfill embeddings for existing chunks.
Run this after setting up pgvector to enable semantic search on existing documents.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')


async def migrate_all_chunks(batch_size: int = 50, limit: int = None):
    """
    Migrate all existing chunks to have embeddings.
    
    Args:
        batch_size: Number of chunks to process at a time
        limit: Maximum number of chunks to process (None for all)
    """
    if not DATABASE_URL:
        logger.error("DATABASE_URL not set")
        return False
    
    from services.embedding_service import embedding_service
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        has_column = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'knowledge_chunks' 
                AND column_name = 'embedding'
            )
        """)
        
        if not has_column:
            logger.error("Embedding column not found. Run setup_pgvector.py first.")
            return False
        
        query = """
            SELECT id, contenido, empresa_id
            FROM knowledge_chunks 
            WHERE embedding IS NULL
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"
        
        chunks = await conn.fetch(query)
        
        total = len(chunks)
        logger.info(f"Found {total} chunks without embeddings")
        
        if total == 0:
            logger.info("All chunks already have embeddings!")
            return True
        
        processed = 0
        failed = 0
        start_time = datetime.now()
        
        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c["contenido"] for c in batch]
            ids = [c["id"] for c in batch]
            
            try:
                embeddings = await embedding_service.generate_batch_embeddings(texts)
                
                for chunk_id, embedding in zip(ids, embeddings):
                    if embedding:
                        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                        await conn.execute("""
                            UPDATE knowledge_chunks 
                            SET embedding = $1::vector
                            WHERE id = $2
                        """, embedding_str, chunk_id)
                        processed += 1
                    else:
                        failed += 1
                
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = processed / elapsed if elapsed > 0 else 0
                eta = (total - processed - failed) / rate if rate > 0 else 0
                
                logger.info(
                    f"Progress: {processed + failed}/{total} "
                    f"({((processed + failed) / total * 100):.1f}%) "
                    f"- {processed} success, {failed} failed "
                    f"- {rate:.1f} chunks/sec "
                    f"- ETA: {int(eta)}s"
                )
                
            except Exception as e:
                logger.error(f"Batch processing error at index {i}: {e}")
                failed += len(batch)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "="*50)
        logger.info("Migration completed!")
        logger.info(f"Total processed: {processed + failed}")
        logger.info(f"Successful: {processed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Time elapsed: {elapsed:.1f} seconds")
        logger.info("="*50)
        
        return failed == 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        await conn.close()


async def migrate_single_document(document_id: str, empresa_id: str):
    """Migrate embeddings for a single document's chunks."""
    if not DATABASE_URL:
        return False
    
    from services.embedding_service import embedding_service
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        chunks = await conn.fetch("""
            SELECT id, contenido
            FROM knowledge_chunks 
            WHERE document_id = $1 AND empresa_id = $2 AND embedding IS NULL
            ORDER BY chunk_index
        """, document_id, empresa_id)
        
        if not chunks:
            return True
        
        texts = [c["contenido"] for c in chunks]
        embeddings = await embedding_service.generate_batch_embeddings(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            if embedding:
                embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                await conn.execute("""
                    UPDATE knowledge_chunks 
                    SET embedding = $1::vector
                    WHERE id = $2
                """, embedding_str, chunk["id"])
        
        return True
        
    except Exception as e:
        logger.error(f"Single document migration failed: {e}")
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate embeddings for knowledge chunks")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--limit", type=int, default=None, help="Maximum chunks to process")
    
    args = parser.parse_args()
    
    asyncio.run(migrate_all_chunks(
        batch_size=args.batch_size,
        limit=args.limit
    ))
