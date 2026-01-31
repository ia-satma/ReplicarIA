#!/usr/bin/env python3
"""
ingest_agent_training.py - Ingesta de Documentos de Entrenamiento para Agentes

Este script:
1. Lee los documentos Markdown de cada agente
2. Los procesa y genera chunks
3. Los ingresa al Knowledge Base con embeddings
4. Asigna los chunks al agente correspondiente

Ejecutar: python backend/scripts/ingest_agent_training.py

Fecha: 2026-01-31
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import hashlib
import json
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
TRAINING_BASE_PATH = os.environ.get(
    "AGENT_TRAINING_PATH",
    "/sessions/stoic-wonderful-fermi/mnt/revisar.ia/agentes"
)

AGENTS = [
    "A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL",
    "A5_FINANZAS", "A6_PROVEEDOR", "A7_DEFENSA"
]


def read_markdown_file(filepath: Path) -> dict:
    """Lee un archivo Markdown y extrae contenido y metadata"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraer título del primer H1
    title = filepath.stem
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break

    return {
        "content": content,
        "title": title,
        "filename": filepath.name,
        "filepath": str(filepath),
        "size_bytes": len(content.encode('utf-8')),
        "hash": hashlib.md5(content.encode()).hexdigest()[:12]
    }


def chunk_document(content: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    """Divide el documento en chunks semánticos"""
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    start = 0

    while start < len(content):
        end = start + chunk_size

        if end < len(content):
            # Buscar punto de corte natural
            split_points = [
                content.rfind('\n\n', start, end),  # Párrafo
                content.rfind('\n', start, end),     # Línea
                content.rfind('. ', start, end),     # Oración
                content.rfind(' ', start, end)       # Palabra
            ]

            for split_point in split_points:
                if split_point > start:
                    end = split_point + 1
                    break

        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(content) else len(content)

    return chunks


async def ingest_to_database(agent_id: str, doc_info: dict, chunks: list) -> bool:
    """Ingresa los chunks al Knowledge Base en PostgreSQL"""
    try:
        import asyncpg
        from openai import OpenAI

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL no configurada")
            return False

        openai_client = OpenAI()
        conn = await asyncpg.connect(db_url)

        doc_id = f"{agent_id}_{doc_info['hash']}"

        # Insertar documento principal
        await conn.execute("""
            INSERT INTO agent_documents (
                id, agent_id, titulo, filepath, content_hash,
                categoria, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
            ON CONFLICT (id) DO UPDATE SET
                titulo = EXCLUDED.titulo,
                updated_at = NOW()
        """, doc_id, agent_id, doc_info['title'], doc_info['filepath'],
            doc_info['hash'], 'training')

        # Procesar cada chunk
        for i, chunk_content in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"

            # Generar embedding
            try:
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk_content
                )
                embedding = response.data[0].embedding
            except Exception as e:
                logger.warning(f"Error generando embedding: {e}")
                embedding = [0.0] * 1536  # Fallback

            # Insertar chunk con embedding
            await conn.execute("""
                INSERT INTO kb_documentos (
                    id, empresa_id, categoria, subcategoria,
                    titulo, contenido, embedding, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    contenido = EXCLUDED.contenido,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
            """, chunk_id, None, 'agent_training', agent_id,
                f"{doc_info['title']} - Chunk {i+1}",
                chunk_content, embedding,
                json.dumps({
                    "agent_id": agent_id,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source_file": doc_info['filename']
                }))

        await conn.close()
        logger.info(f"✅ Ingested {len(chunks)} chunks for {doc_info['title']}")
        return True

    except ImportError as e:
        logger.error(f"Dependencia no instalada: {e}")
        return False
    except Exception as e:
        logger.error(f"Error de ingesta: {e}")
        return False


async def process_agent_documents(agent_id: str) -> dict:
    """Procesa todos los documentos de un agente"""
    results = {
        "agent_id": agent_id,
        "documents_processed": 0,
        "chunks_created": 0,
        "errors": []
    }

    base_path = Path(TRAINING_BASE_PATH) / agent_id

    # Procesar carpeta training
    training_path = base_path / "training"
    if training_path.exists():
        for md_file in training_path.glob("*.md"):
            try:
                doc_info = read_markdown_file(md_file)
                chunks = chunk_document(doc_info["content"])

                success = await ingest_to_database(agent_id, doc_info, chunks)

                if success:
                    results["documents_processed"] += 1
                    results["chunks_created"] += len(chunks)
                    print(f"   ✅ {md_file.name}: {len(chunks)} chunks")
                else:
                    results["errors"].append(f"Failed to ingest {md_file.name}")
                    print(f"   ❌ {md_file.name}: Error de ingesta")

            except Exception as e:
                results["errors"].append(f"{md_file.name}: {str(e)}")
                print(f"   ❌ {md_file.name}: {e}")

    # Procesar carpeta metodologia
    metodo_path = base_path / "metodologia"
    if metodo_path.exists():
        for md_file in metodo_path.glob("*.md"):
            try:
                doc_info = read_markdown_file(md_file)
                chunks = chunk_document(doc_info["content"])

                success = await ingest_to_database(agent_id, doc_info, chunks)

                if success:
                    results["documents_processed"] += 1
                    results["chunks_created"] += len(chunks)
                    print(f"   ✅ [metodología] {md_file.name}: {len(chunks)} chunks")

            except Exception as e:
                results["errors"].append(f"{md_file.name}: {str(e)}")
                print(f"   ❌ [metodología] {md_file.name}: {e}")

    return results


async def main():
    print("\n" + "="*70)
    print("📚 INGESTA DE DOCUMENTOS DE ENTRENAMIENTO PARA AGENTES")
    print("="*70)
    print(f"   Fecha: {datetime.now().isoformat()}")
    print(f"   Base Path: {TRAINING_BASE_PATH}")
    print(f"   DATABASE_URL: {'✅' if os.environ.get('DATABASE_URL') else '❌'}")
    print(f"   OPENAI_API_KEY: {'✅' if os.environ.get('OPENAI_API_KEY') else '❌'}")

    total_docs = 0
    total_chunks = 0
    all_errors = []

    for agent_id in AGENTS:
        print(f"\n📋 Procesando {agent_id}...")
        print("-" * 40)

        results = await process_agent_documents(agent_id)

        total_docs += results["documents_processed"]
        total_chunks += results["chunks_created"]
        all_errors.extend(results["errors"])

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE INGESTA")
    print("="*70)
    print(f"   ✅ Documentos procesados: {total_docs}")
    print(f"   ✅ Chunks creados: {total_chunks}")
    print(f"   ❌ Errores: {len(all_errors)}")

    if all_errors:
        print("\n   Errores encontrados:")
        for err in all_errors[:5]:
            print(f"      - {err}")

    print("\n" + "="*70)
    if total_docs > 0:
        print("✅ INGESTA COMPLETADA")
    else:
        print("⚠️ NO SE PROCESARON DOCUMENTOS - Verificar configuración")
    print("="*70 + "\n")

    return 0 if len(all_errors) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
