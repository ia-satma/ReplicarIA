"""
REVISAR.IA - Script de Ingestión de Documentos del Acervo
=========================================================

Este script descarga e ingesta automáticamente los documentos
definidos en acervo_requerido.py en la base de conocimientos.

Ejecutar con: python -m scripts.ingest_acervo
"""

import asyncio
import os
import sys
import logging
import hashlib
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from config.acervo_requerido import (
    ACERVO_REQUERIDO, 
    get_todos_los_documentos
)


class DocumentIngester:
    """Ingesta documentos del acervo requerido a la base de conocimientos."""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn: Optional[asyncpg.Connection] = None
        self.kb_legal_path = Path(__file__).parent.parent / "kb_legal"
        self.stats = {
            "downloaded": 0,
            "ingested": 0,
            "skipped": 0,
            "errors": 0
        }
    
    async def connect(self):
        """Conectar a la base de datos."""
        db_url = self.db_url
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)
        
        self.conn = await asyncpg.connect(db_url, ssl='require')
        logger.info("✅ Conectado a la base de datos")
    
    async def disconnect(self):
        """Desconectar de la base de datos."""
        if self.conn:
            await self.conn.close()
    
    async def ensure_tables(self):
        """Asegurar que las tablas necesarias existen."""
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS kb_documentos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                titulo VARCHAR(500) NOT NULL,
                contenido TEXT,
                categoria VARCHAR(100),
                subcategoria VARCHAR(100),
                agente_id VARCHAR(10),
                url_origen VARCHAR(1000),
                hash_contenido VARCHAR(64),
                metadata JSONB DEFAULT '{}',
                empresa_id UUID,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kb_documentos_agente 
            ON kb_documentos(agente_id)
        """)
        
        await self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kb_documentos_categoria 
            ON kb_documentos(categoria)
        """)
        
        logger.info("✅ Tablas verificadas/creadas")
    
    async def document_exists(self, doc_id: str, url: str = None) -> bool:
        """Verificar si un documento ya fue ingestado."""
        # Check by metadata doc_id or URL
        exists = await self.conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM kb_documentos 
                WHERE metadata->>'doc_id' = $1 
                   OR url_origen = $2
            )
        """, doc_id, url or "")
        return exists
    
    async def ingest_local_markdown(self):
        """Ingestar documentos markdown locales de kb_legal/."""
        logger.info("📂 Ingesting local markdown files from kb_legal/...")
        
        for md_file in self.kb_legal_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(self.kb_legal_path)
                parts = relative_path.parts
                
                # Determine category from path
                if len(parts) >= 2:
                    categoria = parts[0]
                    subcategoria = parts[1] if len(parts) > 2 else None
                else:
                    categoria = "general"
                    subcategoria = None
                
                # Map category to agent
                agente_map = {
                    "CFF": "A1",
                    "LISR": "A3",
                    "LIVA": "A3",
                    "RMF": "A3",
                    "TESIS_CRITERIOS": "A7",
                    "OTRAS_LEYES": "A4"
                }
                agente_id = agente_map.get(categoria, "A7")
                
                # Read content
                content = md_file.read_text(encoding='utf-8')
                titulo = md_file.stem.replace("_", " ")
                hash_contenido = hashlib.sha256(content.encode()).hexdigest()[:16]
                
                # Check if exists
                exists = await self.conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM kb_documentos 
                        WHERE hash_contenido = $1
                    )
                """, hash_contenido)
                
                if exists:
                    self.stats["skipped"] += 1
                    continue
                
                # Insert
                await self.conn.execute("""
                    INSERT INTO kb_documentos 
                    (titulo, contenido, categoria, subcategoria, agente_id, 
                     url_origen, hash_contenido, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    titulo,
                    content,
                    categoria.lower(),
                    subcategoria,
                    agente_id,
                    f"file://{md_file}",
                    hash_contenido,
                    json.dumps({
                        "source": "local_kb",
                        "file_path": str(relative_path),
                        "ingested_at": datetime.now().isoformat()
                    })
                )
                
                self.stats["ingested"] += 1
                logger.info(f"  ✅ {titulo} ({categoria})")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"  ❌ Error ingesting {md_file}: {e}")
    
    async def ingest_from_kb_dir(self):
        """Ingestar documentos del directorio kb/."""
        kb_path = Path(__file__).parent.parent / "kb"
        
        if not kb_path.exists():
            logger.warning("⚠️ Directorio kb/ no existe")
            return
        
        logger.info("📂 Ingesting from kb/ directory...")
        
        # Agent mapping based on directory
        dir_agent_map = {
            "1_normativa": "A3",      # Fiscal
            "2_pilares": "A1",        # Razón de Negocios
            "3_tipologias": "A2",     # Materialidad
            "4_efos_proveedores": "A6",  # EFOS
            "5_plantillas": "A4"      # Legal
        }
        
        for md_file in kb_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(kb_path)
                parts = relative_path.parts
                
                # Determine agent from first directory
                first_dir = parts[0] if parts else "1_normativa"
                agente_id = dir_agent_map.get(first_dir, "A7")
                
                # Determine category
                if len(parts) >= 2:
                    categoria = parts[1] if len(parts) > 1 else first_dir
                else:
                    categoria = first_dir
                
                # Read and hash
                content = md_file.read_text(encoding='utf-8')
                titulo = md_file.stem.replace("_", " ")
                hash_contenido = hashlib.sha256(content.encode()).hexdigest()[:16]
                
                # Check duplicate
                exists = await self.conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM kb_documentos 
                        WHERE hash_contenido = $1
                    )
                """, hash_contenido)
                
                if exists:
                    self.stats["skipped"] += 1
                    continue
                
                # Insert
                await self.conn.execute("""
                    INSERT INTO kb_documentos 
                    (titulo, contenido, categoria, subcategoria, agente_id, 
                     url_origen, hash_contenido, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    titulo,
                    content,
                    categoria.lower(),
                    None,
                    agente_id,
                    f"file://{md_file}",
                    hash_contenido,
                    json.dumps({
                        "source": "kb_repository",
                        "file_path": str(relative_path),
                        "ingested_at": datetime.now().isoformat()
                    })
                )
                
                self.stats["ingested"] += 1
                logger.info(f"  ✅ {titulo} ({agente_id})")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"  ❌ Error: {e}")
    
    async def ingest_from_rag_templates(self):
        """Ingestar templates RAG predefinidos."""
        rag_path = Path(__file__).parent.parent / "rag" / "templates"
        
        if not rag_path.exists():
            logger.warning("⚠️ Directorio rag/templates no existe")
            return
        
        logger.info("📂 Ingesting RAG templates...")
        
        for md_file in rag_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(rag_path)
                parts = relative_path.parts
                
                # Extract agent from directory name (e.g., A3_FISCAL)
                if parts and "_" in parts[0]:
                    agente_id = parts[0].split("_")[0]
                else:
                    agente_id = "A7"
                
                # Read content
                content = md_file.read_text(encoding='utf-8')
                titulo = md_file.stem.replace("_", " ")
                hash_contenido = hashlib.sha256(content.encode()).hexdigest()[:16]
                
                # Check duplicate
                exists = await self.conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM kb_documentos 
                        WHERE hash_contenido = $1
                    )
                """, hash_contenido)
                
                if exists:
                    self.stats["skipped"] += 1
                    continue
                
                # Insert
                await self.conn.execute("""
                    INSERT INTO kb_documentos 
                    (titulo, contenido, categoria, subcategoria, agente_id, 
                     url_origen, hash_contenido, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    titulo,
                    content,
                    "rag_template",
                    parts[0] if parts else None,
                    agente_id,
                    f"file://{md_file}",
                    hash_contenido,
                    json.dumps({
                        "source": "rag_templates",
                        "file_path": str(relative_path),
                        "is_template": True,
                        "ingested_at": datetime.now().isoformat()
                    })
                )
                
                self.stats["ingested"] += 1
                logger.info(f"  ✅ {titulo} ({agente_id})")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"  ❌ Error: {e}")
    
    async def ingest_from_repositorio(self):
        """Ingestar documentos del repositorio."""
        repo_path = Path(__file__).parent.parent / "repositorio"
        
        if not repo_path.exists():
            logger.warning("⚠️ Directorio repositorio/ no existe")
            return
        
        logger.info("📂 Ingesting from repositorio/...")
        
        for md_file in repo_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(repo_path)
                parts = relative_path.parts
                
                # Extract agent from directory name
                if parts and "_" in parts[0]:
                    agente_id = parts[0].split("_")[0]
                else:
                    agente_id = "A7"
                
                content = md_file.read_text(encoding='utf-8')
                titulo = md_file.stem.replace("_", " ")
                hash_contenido = hashlib.sha256(content.encode()).hexdigest()[:16]
                
                exists = await self.conn.fetchval("""
                    SELECT EXISTS(
                        SELECT 1 FROM kb_documentos 
                        WHERE hash_contenido = $1
                    )
                """, hash_contenido)
                
                if exists:
                    self.stats["skipped"] += 1
                    continue
                
                await self.conn.execute("""
                    INSERT INTO kb_documentos 
                    (titulo, contenido, categoria, subcategoria, agente_id, 
                     url_origen, hash_contenido, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    titulo,
                    content,
                    "repositorio",
                    parts[0] if parts else None,
                    agente_id,
                    f"file://{md_file}",
                    hash_contenido,
                    json.dumps({
                        "source": "repositorio",
                        "file_path": str(relative_path),
                        "ingested_at": datetime.now().isoformat()
                    })
                )
                
                self.stats["ingested"] += 1
                logger.info(f"  ✅ {titulo} ({agente_id})")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"  ❌ Error: {e}")
    
    async def run(self):
        """Ejecutar ingestión completa."""
        logger.info("=" * 60)
        logger.info("🚀 INICIANDO INGESTIÓN DE ACERVO DOCUMENTAL")
        logger.info("=" * 60)
        
        await self.connect()
        await self.ensure_tables()
        
        # Ingest from all sources
        await self.ingest_local_markdown()
        await self.ingest_from_kb_dir()
        await self.ingest_from_rag_templates()
        await self.ingest_from_repositorio()
        
        await self.disconnect()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 RESUMEN DE INGESTIÓN")
        logger.info("=" * 60)
        logger.info(f"  ✅ Documentos ingestados: {self.stats['ingested']}")
        logger.info(f"  ⏭️  Documentos omitidos (duplicados): {self.stats['skipped']}")
        logger.info(f"  ❌ Errores: {self.stats['errors']}")
        
        return self.stats


async def main():
    """Punto de entrada principal."""
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL no configurada")
        sys.exit(1)
    
    ingester = DocumentIngester(db_url)
    stats = await ingester.run()
    
    if stats["ingested"] > 0:
        logger.info("✅ Ingestión completada exitosamente")
    elif stats["skipped"] > 0:
        logger.info("ℹ️ Todos los documentos ya estaban ingestados")
    else:
        logger.warning("⚠️ No se ingestaron documentos")


if __name__ == "__main__":
    asyncio.run(main())
