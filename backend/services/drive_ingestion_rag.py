import logging
import asyncio
from typing import Dict, List
from services.professional_rag_service import ProfessionalRAGService
from services.drive_service import DriveService

logger = logging.getLogger(__name__)

class DriveIngestionRAG:
    """Pipeline de ingestión automática desde Drive con RAG"""
    
    def __init__(self):
        self.rag_service = ProfessionalRAGService()
        self.drive_service = DriveService()
    
    async def ingest_all_agents(self) -> Dict:
        """Ingesta inicial de todos los agentes"""
        
        from services.agent_service import AGENT_CONFIGURATIONS
        
        results = {}
        
        for agent_id, config in AGENT_CONFIGURATIONS.items():
            if agent_id == "PROVEEDOR_IA":
                continue
            
            folder_id = config.get('drive_folder_id')
            if not folder_id:
                continue
            
            logger.info(f"[INGESTION] Procesando {config['name']} ({agent_id})...")
            
            result = await self.rag_service.ingest_drive_folder(
                agent_id=agent_id,
                folder_id=folder_id
            )
            
            results[agent_id] = result
        
        # Resumen
        total_docs = sum(r.get('docs_processed', 0) for r in results.values())
        total_chunks = sum(r.get('chunks_added', 0) for r in results.values())
        
        logger.info(f"✅ INGESTION COMPLETA: {total_docs} documentos, {total_chunks} chunks")
        
        return {
            "success": True,
            "total_docs": total_docs,
            "total_chunks": total_chunks,
            "by_agent": results
        }
    
    async def setup_drive_watch(self, agent_id: str, folder_id: str) -> Dict:
        """
        Configura Drive watch para ingestión continua.
        Nota: Requiere webhook endpoint configurado.
        """
        
        logger.info(f"[DRIVE WATCH] Setup para {agent_id} en folder {folder_id}")
        
        # TODO: Implementar Drive watch API
        # Por ahora, retornar placeholder
        
        return {
            "agent_id": agent_id,
            "folder_id": folder_id,
            "watch_status": "pending",
            "note": "Drive watch requiere webhook endpoint /api/webhooks/drive-changes"
        }
