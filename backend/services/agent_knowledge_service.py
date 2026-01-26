"""
Agent Knowledge Service
Handles ingestion of local training documents for each agent into the RAG system
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.rag_repository import RagRepository

logger = logging.getLogger(__name__)

AGENT_TRAINING_DIR = Path(__file__).parent.parent / "agent_training"

AGENT_FOLDER_MAPPING = {
    "A1_SPONSOR": "A1_SPONSOR",
    "A2_PMO": "A2_PMO",
    "A3_FISCAL": "A3_FISCAL",
    "A5_FINANZAS": "A5_FINANZAS",
    "A5_LEGAL": "A5_LEGAL",
    "LEGAL": "A5_LEGAL",
}

VALID_EXTENSIONS = {".txt", ".md"}


class AgentKnowledgeService:
    def __init__(self, rag_repository: Optional[RagRepository] = None):
        self.rag_repo = rag_repository or RagRepository()
        self.training_dir = AGENT_TRAINING_DIR
        
    def _get_agent_folder(self, agent_id: str) -> Path:
        folder_name = AGENT_FOLDER_MAPPING.get(agent_id, agent_id)
        return self.training_dir / folder_name
    
    def _get_knowledge_folder(self, agent_id: str) -> Path:
        return self._get_agent_folder(agent_id) / "knowledge"
    
    def _get_templates_folder(self, agent_id: str) -> Path:
        return self._get_agent_folder(agent_id) / "templates"
    
    def list_agent_knowledge_files(self, agent_id: str) -> Dict[str, Any]:
        knowledge_folder = self._get_knowledge_folder(agent_id)
        templates_folder = self._get_templates_folder(agent_id)
        
        result = {
            "agent_id": agent_id,
            "knowledge_folder": str(knowledge_folder),
            "templates_folder": str(templates_folder),
            "knowledge_files": [],
            "template_files": [],
            "folder_exists": knowledge_folder.exists()
        }
        
        if knowledge_folder.exists():
            for file_path in knowledge_folder.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in VALID_EXTENSIONS:
                    result["knowledge_files"].append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        if templates_folder.exists():
            for file_path in templates_folder.iterdir():
                if file_path.is_file():
                    result["template_files"].append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        return result
    
    def get_knowledge_stats(self, agent_id: str) -> Dict[str, Any]:
        files_info = self.list_agent_knowledge_files(agent_id)
        rag_count = self.rag_repo.count(agent_id)
        
        return {
            "agent_id": agent_id,
            "local_knowledge_files": len(files_info["knowledge_files"]),
            "local_template_files": len(files_info["template_files"]),
            "rag_documents_count": rag_count,
            "folder_exists": files_info["folder_exists"]
        }
    
    def ingest_document(self, agent_id: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        if not content or not content.strip():
            return {
                "success": False,
                "error": "Empty content provided"
            }
        
        doc_metadata = {
            "agent_id": agent_id,
            "source": metadata.get("source", "manual_upload"),
            "title": metadata.get("title", "Untitled Document"),
            "doc_id": metadata.get("doc_id", f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "chunk_id": metadata.get("chunk_id", "0"),
            "ingested_at": datetime.now().isoformat(),
            **{k: v for k, v in metadata.items() if k not in ["source", "title", "doc_id", "chunk_id"]}
        }
        
        try:
            chunk_id = self.rag_repo.upsert_document(agent_id, content, doc_metadata)
            
            if chunk_id:
                logger.info(f"✅ Ingested document '{doc_metadata['title']}' for agent {agent_id}")
                return {
                    "success": True,
                    "chunk_id": chunk_id,
                    "agent_id": agent_id,
                    "title": doc_metadata["title"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to upsert document to RAG repository"
                }
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                split_points = [
                    text.rfind('\n\n', start, end),
                    text.rfind('\n', start, end),
                    text.rfind('. ', start, end),
                    text.rfind(' ', start, end)
                ]
                
                for split_point in split_points:
                    if split_point > start:
                        end = split_point + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(text) else len(text)
        
        return chunks
    
    def ingest_agent_folder(self, agent_id: str) -> Dict[str, Any]:
        knowledge_folder = self._get_knowledge_folder(agent_id)
        
        if not knowledge_folder.exists():
            return {
                "success": False,
                "error": f"Knowledge folder does not exist: {knowledge_folder}",
                "agent_id": agent_id
            }
        
        results = {
            "agent_id": agent_id,
            "files_processed": 0,
            "chunks_ingested": 0,
            "errors": [],
            "files": []
        }
        
        for file_path in knowledge_folder.iterdir():
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in VALID_EXTENSIONS:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                
                if not content.strip():
                    results["errors"].append(f"Empty file: {file_path.name}")
                    continue
                
                chunks = self._chunk_text(content)
                file_result = {
                    "name": file_path.name,
                    "chunks": len(chunks),
                    "ingested": 0
                }
                
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "source": "local_folder",
                        "title": file_path.stem,
                        "filename": file_path.name,
                        "doc_id": f"{agent_id}_{file_path.stem}",
                        "chunk_id": str(i),
                        "total_chunks": len(chunks)
                    }
                    
                    result = self.ingest_document(agent_id, chunk, metadata)
                    
                    if result["success"]:
                        file_result["ingested"] += 1
                        results["chunks_ingested"] += 1
                    else:
                        results["errors"].append(f"Chunk {i} of {file_path.name}: {result.get('error', 'Unknown error')}")
                
                results["files"].append(file_result)
                results["files_processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_path.name}: {str(e)}")
                results["errors"].append(f"File {file_path.name}: {str(e)}")
        
        results["success"] = results["files_processed"] > 0 or len(results["errors"]) == 0
        logger.info(f"✅ Ingested {results['chunks_ingested']} chunks from {results['files_processed']} files for agent {agent_id}")
        
        return results
    
    def get_all_agents_stats(self) -> List[Dict[str, Any]]:
        stats = []
        
        for folder_name in AGENT_FOLDER_MAPPING.keys():
            if folder_name in ["LEGAL", "A5_FINANZAS"]:
                continue
            
            try:
                agent_stats = self.get_knowledge_stats(folder_name)
                stats.append(agent_stats)
            except Exception as e:
                logger.error(f"Error getting stats for {folder_name}: {str(e)}")
                stats.append({
                    "agent_id": folder_name,
                    "error": str(e)
                })
        
        return stats


agent_knowledge_service = AgentKnowledgeService()
