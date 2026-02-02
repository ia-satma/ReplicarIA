#!/usr/bin/env python3
"""
Script para ingestar los documentos legales de kb_legal/ a la base de datos PostgreSQL.
Esto poblará la tabla kb_documentos para que el Checklist de Agentes muestre el progreso correcto.
"""
import asyncio
import os
import sys
from pathlib import Path
import yaml
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping from directory names to database categories
CATEGORY_MAPPING = {
    "CFF": "marco_legal",
    "LISR": "marco_legal",
    "LIVA": "marco_legal",
    "RMF": "marco_legal",
    "OTRAS_LEYES": "marco_legal",
    "TESIS_CRITERIOS": "jurisprudencias",
}


async def ingest_kb_legal_files():
    """Read all markdown files from kb_legal and insert them into kb_documentos."""
    from services.kb_processor import kb_processor
    
    kb_legal_path = Path(__file__).parent.parent / "kb_legal"
    
    if not kb_legal_path.exists():
        logger.error(f"kb_legal directory not found at {kb_legal_path}")
        return {"success": False, "error": "kb_legal directory not found"}
    
    # Get database pool
    pool = await kb_processor.get_pool()
    if not pool:
        logger.error("Could not get database pool")
        return {"success": False, "error": "Database pool not available"}
    
    ingested = []
    errors = []
    skipped = []
    
    # Walk through all subdirectories
    for subdir in kb_legal_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.'):
            categoria = CATEGORY_MAPPING.get(subdir.name, "marco_legal")
            
            for md_file in subdir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    
                    # Parse YAML frontmatter if present
                    metadata = {}
                    if content.startswith('---'):
                        try:
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                metadata = yaml.safe_load(parts[1]) or {}
                                content_body = parts[2].strip()
                            else:
                                content_body = content
                        except Exception as e:
                            logger.warning(f"Could not parse YAML from {md_file.name}: {e}")
                            content_body = content
                    else:
                        content_body = content
                    
                    # Extract info from metadata
                    doc_id = metadata.get('id', md_file.stem)
                    tags = metadata.get('tags', [])
                    prioridad = metadata.get('prioridad', 'normal')
                    titulo = metadata.get('titulo', md_file.stem.replace('_', ' '))
                    ley = metadata.get('ley', subdir.name)
                    
                    # Check if document already exists
                    async with pool.acquire() as conn:
                        existing = await conn.fetchval("""
                            SELECT id FROM kb_documentos 
                            WHERE nombre = $1 AND empresa_id IS NULL
                        """, md_file.name)
                        
                        if existing:
                            skipped.append({
                                "file": md_file.name,
                                "reason": "Already exists"
                            })
                            continue
                        
                        # Insert document
                        doc_uuid = await conn.fetchval("""
                            INSERT INTO kb_documentos (
                                nombre, tipo_archivo, categoria, subcategoria,
                                version, estado, procesado, contenido_completo,
                                total_chunks, empresa_id, created_at, updated_at
                            ) VALUES (
                                $1, 'md', $2, $3,
                                '1.0', 'activo', TRUE, $4,
                                1, NULL, NOW(), NOW()
                            )
                            RETURNING id
                        """, md_file.name, categoria, subdir.name, content)
                        
                        # Create a chunk for the document
                        await conn.execute("""
                            INSERT INTO kb_chunks (
                                documento_id, chunk_index, contenido, 
                                tipo_chunk, created_at
                            ) VALUES ($1, 0, $2, 'full_document', NOW())
                        """, doc_uuid, content_body[:10000])  # Limit chunk size
                        
                        ingested.append({
                            "file": md_file.name,
                            "id": str(doc_uuid),
                            "categoria": categoria,
                            "subcategoria": subdir.name,
                            "doc_id": doc_id,
                            "tags": tags
                        })
                        
                        logger.info(f"✅ Ingested: {md_file.name} -> {categoria}/{subdir.name}")
                        
                except Exception as e:
                    errors.append({
                        "file": str(md_file),
                        "error": str(e)
                    })
                    logger.error(f"❌ Error ingesting {md_file.name}: {e}")
    
    # Also ingest root-level markdown files
    for md_file in kb_legal_path.glob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8')
            
            async with pool.acquire() as conn:
                existing = await conn.fetchval("""
                    SELECT id FROM kb_documentos 
                    WHERE nombre = $1 AND empresa_id IS NULL
                """, md_file.name)
                
                if existing:
                    skipped.append({"file": md_file.name, "reason": "Already exists"})
                    continue
                
                doc_uuid = await conn.fetchval("""
                    INSERT INTO kb_documentos (
                        nombre, tipo_archivo, categoria, subcategoria,
                        version, estado, procesado, contenido_completo,
                        total_chunks, empresa_id, created_at, updated_at
                    ) VALUES (
                        $1, 'md', 'catalogos_sat', 'referencias',
                        '1.0', 'activo', TRUE, $2,
                        1, NULL, NOW(), NOW()
                    )
                    RETURNING id
                """, md_file.name, content)
                
                await conn.execute("""
                    INSERT INTO kb_chunks (
                        documento_id, chunk_index, contenido, 
                        tipo_chunk, created_at
                    ) VALUES ($1, 0, $2, 'full_document', NOW())
                """, doc_uuid, content[:10000])
                
                ingested.append({
                    "file": md_file.name,
                    "id": str(doc_uuid),
                    "categoria": "catalogos_sat"
                })
                logger.info(f"✅ Ingested root file: {md_file.name}")
                
        except Exception as e:
            errors.append({"file": str(md_file), "error": str(e)})
            logger.error(f"❌ Error ingesting root file {md_file.name}: {e}")
    
    result = {
        "success": True,
        "ingested": len(ingested),
        "skipped": len(skipped),
        "errors": len(errors),
        "details": {
            "ingested": ingested,
            "skipped": skipped,
            "errors": errors
        }
    }
    
    logger.info(f"\n📊 Ingestion Summary:")
    logger.info(f"   ✅ Ingested: {len(ingested)} documents")
    logger.info(f"   ⏭️ Skipped: {len(skipped)} documents")
    logger.info(f"   ❌ Errors: {len(errors)} documents")
    
    return result


async def main():
    """Run the ingestion."""
    result = await ingest_kb_legal_files()
    print(f"\n🎉 Done! Result: {result['ingested']} documents ingested, {result['skipped']} skipped, {result['errors']} errors")
    return result


if __name__ == "__main__":
    asyncio.run(main())
