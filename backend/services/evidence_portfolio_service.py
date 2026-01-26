"""
Evidence Portfolio Service
Manages pCloud storage for project evidence and communication logs (bitácora)
Organizes documents in monthly folders by project
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from services.pcloud_service import PCloudService

logger = logging.getLogger(__name__)

REVISAR_IA_FOLDER_PATH = "/REVISAR_IA"
EVIDENCIAS_FOLDER_PATH = "/REVISAR_IA/Evidencias"

BITACORA_DIR = Path(__file__).parent.parent / "bitacoras"
BITACORA_DIR.mkdir(exist_ok=True)


class EvidencePortfolioService:
    """
    Service for managing evidence portfolio in pCloud
    Creates organized folder structure for SAT audit compliance
    """
    
    def __init__(self):
        self.pcloud = PCloudService()
        self.initialized = False
        self.revisar_folder_id: Optional[int] = None
        self.evidencias_folder_id: Optional[int] = None
        self.monthly_folders: Dict[str, int] = {}
        self.project_folders: Dict[str, int] = {}
        self.communication_logs: Dict[str, List[Dict]] = {}
        
    def _ensure_login(self) -> bool:
        """Ensure pCloud connection is established"""
        if self.initialized and self.pcloud.auth_token:
            return True
        
        if not self.pcloud.username or not self.pcloud.password:
            logger.warning("pCloud credentials not configured - running in offline mode")
            return False
        
        result = self.pcloud.login()
        if result.get("success"):
            self.initialized = True
            return True
        
        logger.error(f"pCloud login failed: {result.get('error')}")
        return False
    
    def _create_folder(self, parent_id: int, folder_name: str) -> Optional[int]:
        """Create a folder in pCloud and return its ID"""
        try:
            params = self.pcloud._get_auth_params()
            params["folderid"] = parent_id
            params["name"] = folder_name
            
            import requests
            response = requests.get(
                f"{self.pcloud.api_url}/createfolder",
                params=params
            )
            data = response.json()
            
            if data.get("result") == 0:
                folder_id = data.get("metadata", {}).get("folderid")
                logger.info(f"Created pCloud folder: {folder_name} (ID: {folder_id})")
                return folder_id
            elif data.get("result") == 2004:
                logger.info(f"Folder already exists: {folder_name}")
                return None
            else:
                logger.error(f"Failed to create folder {folder_name}: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Error creating folder {folder_name}: {e}")
            return None
    
    def _find_folder_by_name(self, parent_id: int, folder_name: str) -> Optional[int]:
        """Find a folder by name within a parent folder"""
        result = self.pcloud.list_folder(folder_id=parent_id)
        if not result.get("success"):
            return None
        
        for item in result.get("items", []):
            if item.get("is_folder") and item.get("name") == folder_name:
                return item.get("id")
        return None
    
    def _get_or_create_folder(self, parent_id: int, folder_name: str) -> Optional[int]:
        """Get existing folder or create new one"""
        existing = self._find_folder_by_name(parent_id, folder_name)
        if existing:
            return existing
        
        new_id = self._create_folder(parent_id, folder_name)
        if new_id:
            return new_id
        
        return self._find_folder_by_name(parent_id, folder_name)
    
    def _ensure_base_folders(self) -> bool:
        """Ensure REVISAR_IA and Evidencias folders exist"""
        if not self._ensure_login():
            return False
        
        root_result = self.pcloud.list_folder(folder_id=0)
        if not root_result.get("success"):
            logger.error("Failed to list root folder")
            return False
        
        for item in root_result.get("items", []):
            if item.get("is_folder") and item.get("name") == "REVISAR_IA":
                self.revisar_folder_id = item.get("id")
                break
        
        if not self.revisar_folder_id:
            self.revisar_folder_id = self._create_folder(0, "REVISAR_IA")
            if not self.revisar_folder_id:
                root_result = self.pcloud.list_folder(folder_id=0)
                for item in root_result.get("items", []):
                    if item.get("is_folder") and item.get("name") == "REVISAR_IA":
                        self.revisar_folder_id = item.get("id")
                        break
        
        if not self.revisar_folder_id:
            logger.error("Failed to find or create REVISAR_IA folder")
            return False
        
        self.evidencias_folder_id = self._get_or_create_folder(self.revisar_folder_id, "Evidencias")
        
        if not self.evidencias_folder_id:
            logger.error("Failed to find or create Evidencias folder")
            return False
        
        return True
    
    def get_or_create_monthly_folder(self, year_month: str = None) -> Dict[str, Any]:
        """
        Get or create monthly evidence folder
        Format: YYYY-MM-Evidencias (e.g., 2025-11-Evidencias)
        
        Args:
            year_month: Optional year-month string (default: current month)
        
        Returns:
            Dict with folder_id and path
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")
        
        folder_name = f"{year_month}-Evidencias"
        
        if folder_name in self.monthly_folders:
            return {
                "success": True,
                "folder_id": self.monthly_folders[folder_name],
                "folder_name": folder_name,
                "cached": True
            }
        
        if not self._ensure_base_folders():
            return {
                "success": False,
                "error": "pCloud not available",
                "offline_mode": True
            }
        
        folder_id = self._get_or_create_folder(self.evidencias_folder_id, folder_name)
        
        if folder_id:
            self.monthly_folders[folder_name] = folder_id
            return {
                "success": True,
                "folder_id": folder_id,
                "folder_name": folder_name,
                "path": f"{EVIDENCIAS_FOLDER_PATH}/{folder_name}"
            }
        
        return {
            "success": False,
            "error": f"Failed to create monthly folder: {folder_name}"
        }
    
    def get_or_create_project_folder(self, project_id: str, year_month: str = None) -> Dict[str, Any]:
        """
        Get or create project subfolder within monthly folder
        
        Args:
            project_id: The project ID (used as folder name)
            year_month: Optional year-month string
        
        Returns:
            Dict with folder_id and path
        """
        cache_key = f"{year_month or datetime.now().strftime('%Y-%m')}_{project_id}"
        
        if cache_key in self.project_folders:
            return {
                "success": True,
                "folder_id": self.project_folders[cache_key],
                "project_id": project_id,
                "cached": True
            }
        
        monthly_result = self.get_or_create_monthly_folder(year_month)
        
        if not monthly_result.get("success"):
            return monthly_result
        
        monthly_folder_id = monthly_result["folder_id"]
        safe_project_id = project_id.replace("/", "_").replace("\\", "_")[:50]
        
        folder_id = self._get_or_create_folder(monthly_folder_id, safe_project_id)
        
        if folder_id:
            self.project_folders[cache_key] = folder_id
            return {
                "success": True,
                "folder_id": folder_id,
                "project_id": project_id,
                "path": f"{monthly_result.get('path', '')}/{safe_project_id}"
            }
        
        return {
            "success": False,
            "error": f"Failed to create project folder: {safe_project_id}"
        }
    
    def upload_document(
        self,
        project_id: str,
        file_path: str,
        doc_type: str,
        agent_id: str = None,
        year_month: str = None
    ) -> Dict[str, Any]:
        """
        Upload a document to pCloud in the project's monthly folder
        
        Args:
            project_id: The project ID
            file_path: Local path to the file
            doc_type: Type of document (e.g., "reporte_fiscal", "bitacora")
            agent_id: Optional agent ID for naming
            year_month: Optional year-month for folder organization
        
        Returns:
            Dict with upload result and pCloud link
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "offline_fallback": True
            }
        
        folder_result = self.get_or_create_project_folder(project_id, year_month)
        
        if not folder_result.get("success"):
            logger.warning(f"pCloud unavailable, file stored locally: {file_path}")
            return {
                "success": False,
                "error": folder_result.get("error", "pCloud unavailable"),
                "local_path": file_path,
                "offline_mode": True
            }
        
        folder_id = folder_result["folder_id"]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = os.path.basename(file_path)
        
        if agent_id:
            new_filename = f"{agent_id}_{doc_type}_{timestamp}.pdf"
        else:
            name_parts = os.path.splitext(original_name)
            new_filename = f"{name_parts[0]}_{timestamp}{name_parts[1]}"
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            upload_result = self.pcloud.upload_file(folder_id, new_filename, content)
            
            if upload_result.get("success"):
                file_id = upload_result.get("file_id")
                link_result = self.pcloud.get_or_create_public_link(file_id)
                
                public_link = None
                if link_result.get("success"):
                    public_link = link_result.get("public_link")
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": new_filename,
                    "pcloud_path": f"{folder_result.get('path', '')}/{new_filename}",
                    "download_url": public_link,
                    "public_link": public_link,
                    "size": upload_result.get("size"),
                    "uploaded_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": upload_result.get("error"),
                    "local_path": file_path
                }
                
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {
                "success": False,
                "error": str(e),
                "local_path": file_path
            }
    
    def add_to_communication_log(self, project_id: str, entry: Dict) -> Dict[str, Any]:
        """
        Add entry to the project's communication log (bitácora)
        
        Args:
            project_id: The project ID
            entry: Dict containing:
                - timestamp: When the communication occurred
                - from_agent: Sender agent ID
                - to_agent: Recipient agent ID
                - email_subject: Subject of the email
                - attachment_name: Name of attached document
                - pcloud_link: Link to document in pCloud
                - action: Type of action (email_sent, document_uploaded, etc.)
        
        Returns:
            Dict with operation result
        """
        if project_id not in self.communication_logs:
            self.communication_logs[project_id] = []
            self._load_bitacora_from_disk(project_id)
        
        entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
        entry["sequence_number"] = len(self.communication_logs[project_id]) + 1
        
        self.communication_logs[project_id].append(entry)
        
        self._save_bitacora_to_disk(project_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "entry_count": len(self.communication_logs[project_id]),
            "latest_entry": entry
        }
    
    def get_communication_log(self, project_id: str) -> Dict[str, Any]:
        """
        Get the complete communication log (bitácora) for a project
        
        Args:
            project_id: The project ID
        
        Returns:
            Dict with full bitácora
        """
        if project_id not in self.communication_logs:
            self._load_bitacora_from_disk(project_id)
        
        entries = self.communication_logs.get(project_id, [])
        
        return {
            "success": True,
            "project_id": project_id,
            "entry_count": len(entries),
            "entries": entries,
            "first_entry": entries[0] if entries else None,
            "last_entry": entries[-1] if entries else None
        }
    
    def _get_bitacora_path(self, project_id: str) -> Path:
        """Get path to bitácora JSON file"""
        safe_id = project_id.replace("/", "_").replace("\\", "_")
        return BITACORA_DIR / f"{safe_id}_bitacora.json"
    
    def _save_bitacora_to_disk(self, project_id: str):
        """Save bitácora to local disk"""
        try:
            path = self._get_bitacora_path(project_id)
            data = {
                "project_id": project_id,
                "entries": self.communication_logs.get(project_id, []),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Bitácora saved: {path}")
        except Exception as e:
            logger.error(f"Error saving bitácora for {project_id}: {e}")
    
    def _load_bitacora_from_disk(self, project_id: str):
        """Load bitácora from local disk"""
        try:
            path = self._get_bitacora_path(project_id)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.communication_logs[project_id] = data.get("entries", [])
                logger.debug(f"Bitácora loaded: {path}")
            else:
                self.communication_logs[project_id] = []
        except Exception as e:
            logger.error(f"Error loading bitácora for {project_id}: {e}")
            self.communication_logs[project_id] = []
    
    def generate_bitacora_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a summary of the communication log
        
        Args:
            project_id: The project ID
        
        Returns:
            Dict with summary statistics
        """
        log = self.get_communication_log(project_id)
        entries = log.get("entries", [])
        
        if not entries:
            return {
                "project_id": project_id,
                "total_entries": 0,
                "summary": "No hay comunicaciones registradas"
            }
        
        emails_sent = len([e for e in entries if e.get("action") == "email_sent"])
        documents_uploaded = len([e for e in entries if e.get("action") == "document_uploaded"])
        
        agents_involved = set()
        for entry in entries:
            if entry.get("from_agent"):
                agents_involved.add(entry["from_agent"])
            if entry.get("to_agent"):
                agents_involved.add(entry["to_agent"])
        
        return {
            "project_id": project_id,
            "total_entries": len(entries),
            "emails_sent": emails_sent,
            "documents_uploaded": documents_uploaded,
            "agents_involved": list(agents_involved),
            "first_communication": entries[0].get("timestamp") if entries else None,
            "last_communication": entries[-1].get("timestamp") if entries else None,
            "summary": f"{emails_sent} emails, {documents_uploaded} documentos, {len(agents_involved)} agentes"
        }
    
    def upload_bitacora_to_pcloud(self, project_id: str, bitacora_pdf_path: str) -> Dict[str, Any]:
        """
        Upload the final bitácora PDF to pCloud
        
        Args:
            project_id: The project ID
            bitacora_pdf_path: Path to the generated bitácora PDF
        
        Returns:
            Dict with upload result
        """
        return self.upload_document(
            project_id=project_id,
            file_path=bitacora_pdf_path,
            doc_type="bitacora_final",
            agent_id="SYSTEM"
        )
    
    def get_project_documents(self, project_id: str, year_month: str = None) -> Dict[str, Any]:
        """
        List all documents in a project folder
        
        Args:
            project_id: The project ID
            year_month: Optional year-month
        
        Returns:
            Dict with list of documents
        """
        folder_result = self.get_or_create_project_folder(project_id, year_month)
        
        if not folder_result.get("success"):
            return folder_result
        
        folder_id = folder_result["folder_id"]
        list_result = self.pcloud.list_folder(folder_id=folder_id)
        
        if not list_result.get("success"):
            return list_result
        
        documents = [
            item for item in list_result.get("items", [])
            if not item.get("is_folder")
        ]
        
        return {
            "success": True,
            "project_id": project_id,
            "folder_path": folder_result.get("path"),
            "documents": documents,
            "document_count": len(documents)
        }


evidence_portfolio_service = EvidencePortfolioService()
