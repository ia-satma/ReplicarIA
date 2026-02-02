import os
import requests
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

PCLOUD_API_EU = "https://eapi.pcloud.com"
PCLOUD_API_US = "https://api.pcloud.com"

# Carpeta de configuración agéntica (skills, knowledge base)
REVISAR_IA_CONFIG_FOLDER_NAME = "REVISAR.IA"
REVISAR_IA_CONFIG_FOLDER_ID = 29789401752

# Carpeta de operaciones (evidencias, resultados mensuales)
REVISAR_IA_OPERATIONS_FOLDER_NAME = "REVISAR_IA"
REVISAR_IA_OPERATIONS_FOLDER_ID = 29799555433
EVIDENCIAS_FOLDER_ID = 29799555482

# Legacy compatibility
REVISAR_IA_FOLDER_NAME = "REVISAR.IA"

REQUIRED_SUBFOLDERS = [
    # Agentes Principales (7)
    "A1_ESTRATEGIA",
    "A2_PMO",
    "A3_FISCAL",
    "A4_LEGAL",
    "A5_FINANZAS",
    "A6_PROVEEDOR",
    "A7_DEFENSA",
    # Agentes Especializados (1 + KB)
    "A8_AUDITOR",
    "KNOWLEDGE_BASE",  # KB_CURATOR
    # Carpetas de Sistema
    "DEFENSE_FILES",
    "PROYECTOS",
    # Subagentes Fiscales (3) - Reportan a A3_FISCAL
    "SUB_TIPIFICACION",
    "SUB_MATERIALIDAD",
    "SUB_RIESGOS",
    # Subagentes PMO (5) - Reportan a A2_PMO
    "SUB_ANALIZADOR",
    "SUB_CLASIFICADOR",
    "SUB_RESUMIDOR",
    "SUB_VERIFICADOR",
    "SUB_REDACTOR",
]

AGENT_FOLDER_NAMES = {
    # Agentes Principales
    "A1_ESTRATEGIA": ["a1_estrategia"],
    "A2_PMO": ["a2_pmo"],
    "A3_FISCAL": ["a3_fiscal"],
    "A4_LEGAL": ["a4_legal"],
    "A5_FINANZAS": ["a5_finanzas"],
    "A6_PROVEEDOR": ["a6_proveedor"],
    "A7_DEFENSA": ["a7_defensa"],
    "A8_AUDITOR": ["a8_auditor", "auditoria"],
    # Sistema
    "DEFENSE_FILES": ["defense_files"],
    "KNOWLEDGE_BASE": ["knowledge_base"],
    "PROYECTOS": ["proyectos"],
    # Subagentes Fiscales
    "SUB_TIPIFICACION": ["sub_tipificacion"],
    "SUB_MATERIALIDAD": ["sub_materialidad"],
    "SUB_RIESGOS": ["sub_riesgos"],
    # Subagentes PMO
    "SUB_ANALIZADOR": ["sub_analizador"],
    "SUB_CLASIFICADOR": ["sub_clasificador"],
    "SUB_RESUMIDOR": ["sub_resumidor"],
    "SUB_VERIFICADOR": ["sub_verificador"],
    "SUB_REDACTOR": ["sub_redactor"],
}

AGENT_FOLDER_IDS = {
    # Carpetas de agentes principales en REVISAR.IA
    "A1_ESTRATEGIA": 29789474359,
    "A1_SPONSOR": 29789474359,  # Alias
    "A2_PMO": 29789474388,
    "A3_FISCAL": 29789474414,
    "A4_LEGAL": 29789474435,
    "LEGAL": 29789474435,  # Alias
    "A5_FINANZAS": 29789474462,
    "A6_PROVEEDOR": 29789474493,
    "A7_DEFENSA": 29789474511,
    "A8_AUDITOR": 29897074462,
    # Carpetas de sistema
    "DEFENSE_FILES": 29789474531,
    "KNOWLEDGE_BASE": 29789474559,
    "KB_CURATOR": 29789474559,  # Alias
    "PROYECTOS": 29789474598,
    # Subagentes Fiscales (reportan a A3_FISCAL)
    "SUB_TIPIFICACION": 29897074474,
    "S1_TIPIFICACION": 29897074474,  # Alias
    "SUB_MATERIALIDAD": 29897074492,
    "S2_MATERIALIDAD": 29897074492,  # Alias
    "SUB_RIESGOS": 29897074499,
    "S3_RIESGOS": 29897074499,  # Alias
    # Subagentes PMO (reportan a A2_PMO) - Se crearán en pCloud
    "SUB_ANALIZADOR": None,  # Pendiente crear en pCloud
    "S_ANALIZADOR": None,  # Alias
    "SUB_CLASIFICADOR": None,
    "S_CLASIFICADOR": None,  # Alias
    "SUB_RESUMIDOR": None,
    "S_RESUMIDOR": None,  # Alias
    "SUB_VERIFICADOR": None,
    "S_VERIFICADOR": None,  # Alias
    "SUB_REDACTOR": None,
    "S_REDACTOR": None,  # Alias
    # Carpetas raíz
    "REVISAR_IA_CONFIG": 29789401752,  # REVISAR.IA - configuración agéntica
    "REVISAR_IA_OPERATIONS": 29799555433,  # REVISAR_IA - operaciones/evidencias
    "EVIDENCIAS": 29799555482,  # Subcarpeta de evidencias mensuales
}

# Modelo de permisos entre agentes
# Todos los agentes pueden leer de todas las carpetas para contexto transversal
_ALL_FOLDERS = list(AGENT_FOLDER_IDS.keys())

AGENT_READ_PERMISSIONS = {
    # Agentes Principales
    "A1_ESTRATEGIA": _ALL_FOLDERS,
    "A1_SPONSOR": _ALL_FOLDERS,
    "A2_PMO": _ALL_FOLDERS,
    "A3_FISCAL": _ALL_FOLDERS,
    "A4_LEGAL": _ALL_FOLDERS,
    "A5_FINANZAS": _ALL_FOLDERS,
    "A6_PROVEEDOR": _ALL_FOLDERS,
    "A7_DEFENSA": _ALL_FOLDERS,
    "A8_AUDITOR": _ALL_FOLDERS,
    "KB_CURATOR": _ALL_FOLDERS,
    # Subagentes Fiscales
    "SUB_TIPIFICACION": _ALL_FOLDERS,
    "S1_TIPIFICACION": _ALL_FOLDERS,
    "SUB_MATERIALIDAD": _ALL_FOLDERS,
    "S2_MATERIALIDAD": _ALL_FOLDERS,
    "SUB_RIESGOS": _ALL_FOLDERS,
    "S3_RIESGOS": _ALL_FOLDERS,
    # Subagentes PMO
    "SUB_ANALIZADOR": _ALL_FOLDERS,
    "S_ANALIZADOR": _ALL_FOLDERS,
    "SUB_CLASIFICADOR": _ALL_FOLDERS,
    "S_CLASIFICADOR": _ALL_FOLDERS,
    "SUB_RESUMIDOR": _ALL_FOLDERS,
    "S_RESUMIDOR": _ALL_FOLDERS,
    "SUB_VERIFICADOR": _ALL_FOLDERS,
    "S_VERIFICADOR": _ALL_FOLDERS,
    "SUB_REDACTOR": _ALL_FOLDERS,
    "S_REDACTOR": _ALL_FOLDERS,
}

AGENT_WRITE_PERMISSIONS = {
    # Cada agente escribe solo en su carpeta por defecto
    "A1_ESTRATEGIA": ["A1_ESTRATEGIA"],
    "A2_PMO": ["A2_PMO", "A1_ESTRATEGIA", "A3_FISCAL", "A4_LEGAL", "A5_FINANZAS", "DEFENSE_FILES", "PROYECTOS"],
    "A3_FISCAL": ["A3_FISCAL"],
    "A4_LEGAL": ["A4_LEGAL", "DEFENSE_FILES"],
    "A5_FINANZAS": ["A5_FINANZAS"],
    "A6_PROVEEDOR": ["A6_PROVEEDOR"],
    "A7_DEFENSA": ["A7_DEFENSA", "DEFENSE_FILES", "A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL", "A5_FINANZAS"],
    "A8_AUDITOR": ["A8_AUDITOR", "DEFENSE_FILES", "A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL", "A5_FINANZAS", "A7_DEFENSA"],
    "SUB_TIPIFICACION": ["SUB_TIPIFICACION"],
    "SUB_MATERIALIDAD": ["SUB_MATERIALIDAD"],
    "SUB_RIESGOS": ["SUB_RIESGOS"],
}

class PCloudService:
    def __init__(self):
        self.username = os.environ.get('PCLOUD_USERNAME', '')
        self.password = os.environ.get('PCLOUD_PASSWORD', '')
        self.api_url = PCLOUD_API_EU
        self.auth_token = None
        self.agent_folders: Dict[str, int] = {}
        self.revisar_ia_folder_id: Optional[int] = None
        self.initialized = False
        self._configured = bool(self.username and self.password)
        
        if self._configured:
            logger.info(f"✅ pCloud service configured for user {self.username}")
        else:
            logger.warning("⚠️ pCloud service not configured - running in demo mode")
    
    def is_available(self) -> bool:
        return self._configured
        
    def _get_auth_params(self) -> Dict[str, str]:
        if self.auth_token:
            return {"auth": self.auth_token}
        return {
            "username": self.username,
            "password": self.password
        }
    
    def login(self) -> Dict[str, Any]:
        apis_to_try = [PCLOUD_API_US, PCLOUD_API_EU]
        
        for api_url in apis_to_try:
            try:
                logger.info(f"Trying pCloud login with {api_url}")
                response = requests.get(
                    f"{api_url}/userinfo",
                    params={
                        "getauth": 1,
                        "logout": 1,
                        "username": self.username,
                        "password": self.password
                    },
                    timeout=15
                )
                data = response.json()
                
                if data.get("result") == 0:
                    self.auth_token = data.get("auth")
                    self.api_url = api_url
                    logger.info(f"pCloud login successful for {data.get('email')} on {api_url}")
                    return {
                        "success": True,
                        "email": data.get("email"),
                        "server": api_url,
                        "quota": data.get("quota"),
                        "usedquota": data.get("usedquota")
                    }
                else:
                    logger.warning(f"pCloud login failed on {api_url}: {data.get('error')}")
                    
            except Exception as e:
                logger.warning(f"pCloud connection error on {api_url}: {str(e)}")
                continue
        
        logger.error("pCloud login failed on all servers")
        return {"success": False, "error": "Login failed on both US and EU servers. Please verify credentials."}
    
    def list_folder(self, folder_id: int = 0, path: str = None) -> Dict[str, Any]:
        try:
            params = self._get_auth_params()
            if path:
                params["path"] = path
            else:
                params["folderid"] = folder_id
                
            response = requests.get(
                f"{self.api_url}/listfolder",
                params=params
            )
            data = response.json()
            
            if data.get("result") == 0:
                metadata = data.get("metadata", {})
                contents = metadata.get("contents", [])
                return {
                    "success": True,
                    "folder_id": metadata.get("folderid"),
                    "name": metadata.get("name"),
                    "items": [
                        {
                            "name": item.get("name"),
                            "id": item.get("folderid") if item.get("isfolder") else item.get("fileid"),
                            "is_folder": item.get("isfolder", False),
                            "size": item.get("size", 0),
                            "modified": item.get("modified"),
                            "content_type": item.get("contenttype")
                        }
                        for item in contents
                    ]
                }
            else:
                return {"success": False, "error": data.get("error")}
                
        except Exception as e:
            logger.error(f"pCloud list folder error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def create_folder(self, parent_folder_id: int, folder_name: str) -> Dict[str, Any]:
        """Create a new folder inside a parent folder"""
        try:
            params = self._get_auth_params()
            params["folderid"] = parent_folder_id
            params["name"] = folder_name
            
            response = requests.get(
                f"{self.api_url}/createfolder",
                params=params,
                timeout=15
            )
            data = response.json()
            
            if data.get("result") == 0:
                metadata = data.get("metadata", {})
                logger.info(f"Created pCloud folder: {folder_name} (ID: {metadata.get('folderid')})")
                return {
                    "success": True,
                    "folder_id": metadata.get("folderid"),
                    "name": metadata.get("name"),
                    "path": metadata.get("path")
                }
            elif data.get("result") == 2004:
                logger.info(f"Folder already exists: {folder_name}")
                return {"success": True, "already_exists": True, "name": folder_name}
            else:
                return {"success": False, "error": data.get("error")}
                
        except Exception as e:
            logger.error(f"pCloud create folder error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def find_revisar_ia_folder(self) -> Dict[str, Any]:
        """Find the REVISAR.ia folder in the root directory"""
        try:
            root_contents = self.list_folder(folder_id=0)
            if not root_contents.get("success"):
                return root_contents
            
            for item in root_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").lower() == REVISAR_IA_FOLDER_NAME.lower():
                    self.revisar_ia_folder_id = item.get("id")
                    logger.info(f"Found REVISAR.ia folder with ID: {self.revisar_ia_folder_id}")
                    return {
                        "success": True,
                        "folder_id": self.revisar_ia_folder_id,
                        "name": item.get("name")
                    }
            
            return {"success": False, "error": f"Folder '{REVISAR_IA_FOLDER_NAME}' not found in root directory"}
            
        except Exception as e:
            logger.error(f"Error finding REVISAR.ia folder: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def initialize_folder_structure(self) -> Dict[str, Any]:
        """Initialize the complete folder structure inside REVISAR.ia"""
        login_result = self.login()
        if not login_result.get("success"):
            return login_result
        
        revisar_result = self.find_revisar_ia_folder()
        if not revisar_result.get("success"):
            return revisar_result
        
        parent_id = self.revisar_ia_folder_id
        created_folders = []
        existing_folders = []
        
        revisar_contents = self.list_folder(folder_id=parent_id)
        existing_names = []
        if revisar_contents.get("success"):
            existing_names = [item.get("name", "").upper() for item in revisar_contents.get("items", []) if item.get("is_folder")]
        
        for subfolder in REQUIRED_SUBFOLDERS:
            if subfolder.upper() in [n.upper() for n in existing_names]:
                existing_folders.append(subfolder)
                for item in revisar_contents.get("items", []):
                    if item.get("is_folder") and item.get("name", "").upper() == subfolder.upper():
                        self.agent_folders[subfolder] = item.get("id")
                        break
            else:
                result = self.create_folder(parent_id, subfolder)
                if result.get("success"):
                    created_folders.append(subfolder)
                    if result.get("folder_id"):
                        self.agent_folders[subfolder] = result.get("folder_id")
        
        self.initialized = True
        
        return {
            "success": True,
            "revisar_ia_folder_id": self.revisar_ia_folder_id,
            "created_folders": created_folders,
            "existing_folders": existing_folders,
            "agent_folders": {k: v for k, v in self.agent_folders.items()},
            "message": f"Initialized {len(created_folders)} new folders, {len(existing_folders)} already existed"
        }
    
    def find_agent_folders(self) -> Dict[str, Any]:
        """Find all agent folders inside REVISAR.ia"""
        if not self.initialized:
            init_result = self.initialize_folder_structure()
            if not init_result.get("success"):
                return init_result
        
        if not self.revisar_ia_folder_id:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
            revisar_result = self.find_revisar_ia_folder()
            if not revisar_result.get("success"):
                return revisar_result
        
        revisar_contents = self.list_folder(folder_id=self.revisar_ia_folder_id)
        if not revisar_contents.get("success"):
            return revisar_contents
            
        found_folders = {}
        for item in revisar_contents.get("items", []):
            if item.get("is_folder"):
                folder_name = item.get("name", "").lower()
                for agent_id, keywords in AGENT_FOLDER_NAMES.items():
                    if any(kw.lower() in folder_name or folder_name in kw.lower() for kw in keywords):
                        found_folders[agent_id] = {
                            "folder_id": item.get("id"),
                            "name": item.get("name")
                        }
                        self.agent_folders[agent_id] = item.get("id")
                        break
                        
        return {
            "success": True,
            "revisar_ia_folder_id": self.revisar_ia_folder_id,
            "agent_folders": found_folders,
            "total_found": len(found_folders),
            "source": "discovered"
        }
    
    def list_agent_documents(self, agent_id: str) -> Dict[str, Any]:
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        folder_id = self.agent_folders.get(agent_id)
        
        if not folder_id:
            folders_result = self.find_agent_folders()
            if not folders_result.get("success"):
                return folders_result
            folder_id = self.agent_folders.get(agent_id)
                
        if not folder_id:
            return {
                "success": False,
                "error": f"No folder found for agent {agent_id} in REVISAR.ia. Available folders: {list(self.agent_folders.keys())}"
            }
            
        folder_contents = self.list_folder(folder_id=folder_id)
        if not folder_contents.get("success"):
            return folder_contents
            
        documents = [
            item for item in folder_contents.get("items", [])
            if not item.get("is_folder") and self._is_document(item.get("name", ""))
        ]
        
        return {
            "success": True,
            "agent_id": agent_id,
            "folder_id": folder_id,
            "documents": documents,
            "document_count": len(documents)
        }
    
    def _is_document(self, filename: str) -> bool:
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.xlsx', '.xls', '.csv', '.pptx', '.ppt']
        return any(filename.lower().endswith(ext) for ext in doc_extensions)
    
    def get_file_link(self, file_id: int) -> Dict[str, Any]:
        """Get a temporary download link (expires in ~4 hours)"""
        try:
            params = self._get_auth_params()
            params["fileid"] = file_id
            
            response = requests.get(
                f"{self.api_url}/getfilelink",
                params=params
            )
            data = response.json()
            
            if data.get("result") == 0:
                hosts = data.get("hosts", [])
                path = data.get("path", "")
                if hosts:
                    download_url = f"https://{hosts[0]}{path}"
                    return {
                        "success": True,
                        "download_url": download_url,
                        "expires": data.get("expires")
                    }
            return {"success": False, "error": data.get("error")}
            
        except Exception as e:
            logger.error(f"pCloud get file link error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_public_file_link(self, file_id: int) -> Dict[str, Any]:
        """
        Create a permanent public link for a file.
        Uses getfilepublink API - creates a non-expiring public share link.
        """
        try:
            params = self._get_auth_params()
            params["fileid"] = file_id
            
            response = requests.get(
                f"{self.api_url}/getfilepublink",
                params=params,
                timeout=15
            )
            data = response.json()
            
            if data.get("result") == 0:
                link = data.get("link", "")
                code = data.get("code", "")
                
                if link:
                    direct_link = f"https://api.pcloud.com/getpubthumb?code={code}&linkpassword=0&size=0&crop=0&type=auto"
                    download_link = f"https://api.pcloud.com/getpublinkdownload?code={code}"
                    
                    return {
                        "success": True,
                        "public_link": link,
                        "download_link": download_link,
                        "code": code,
                        "expires": None
                    }
            
            error_msg = data.get("error", "Unknown error")
            if data.get("result") == 2009:
                existing = self._get_existing_public_link(file_id)
                if existing.get("success"):
                    return existing
                    
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            logger.error(f"pCloud get public file link error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_existing_public_link(self, file_id: int) -> Dict[str, Any]:
        """Get existing public link if file is already shared"""
        try:
            params = self._get_auth_params()
            params["fileid"] = file_id
            
            response = requests.get(
                f"{self.api_url}/getfilepublink",
                params=params,
                timeout=15
            )
            data = response.json()
            
            if data.get("result") == 0 or data.get("link"):
                link = data.get("link", "")
                code = data.get("code", "")
                return {
                    "success": True,
                    "public_link": link,
                    "code": code,
                    "expires": None
                }
            return {"success": False, "error": data.get("error")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_folder_public_link(self, folder_id: int) -> Dict[str, Any]:
        """
        Create a permanent public link for a folder.
        Uses getfolderpublink API - creates a non-expiring public share link.
        """
        try:
            params = self._get_auth_params()
            params["folderid"] = folder_id
            
            response = requests.get(
                f"{self.api_url}/getfolderpublink",
                params=params,
                timeout=15
            )
            data = response.json()
            
            if data.get("result") == 0:
                link = data.get("link", "")
                code = data.get("code", "")
                
                return {
                    "success": True,
                    "public_link": link,
                    "code": code,
                    "expires": None
                }
            
            return {"success": False, "error": data.get("error")}
            
        except Exception as e:
            logger.error(f"pCloud get folder public link error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_or_create_public_link(self, file_id: int) -> Dict[str, Any]:
        """
        Get existing public link or create a new one.
        This is the preferred method for getting document links.
        Returns a permanent, non-expiring link.
        """
        result = self.get_public_file_link(file_id)
        
        if result.get("success"):
            return result
        
        if "already" in str(result.get("error", "")).lower():
            return self._get_existing_public_link(file_id)
        
        return result
    
    def download_file(self, file_id: int) -> Dict[str, Any]:
        try:
            link_result = self.get_file_link(file_id)
            if not link_result.get("success"):
                return link_result
                
            download_url = link_result.get("download_url")
            response = requests.get(download_url)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.content,
                    "content_type": response.headers.get("Content-Type"),
                    "size": len(response.content)
                }
            else:
                return {"success": False, "error": f"Download failed with status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"pCloud download error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def upload_file(self, folder_id: int, filename: str, content: bytes) -> Dict[str, Any]:
        try:
            params = self._get_auth_params()
            params["folderid"] = folder_id
            params["filename"] = filename
            
            files = {"file": (filename, content)}
            
            response = requests.post(
                f"{self.api_url}/uploadfile",
                params=params,
                files=files
            )
            data = response.json()
            
            if data.get("result") == 0:
                metadata = data.get("metadata", [{}])[0]
                return {
                    "success": True,
                    "file_id": metadata.get("fileid"),
                    "name": metadata.get("name"),
                    "size": metadata.get("size")
                }
            else:
                return {"success": False, "error": data.get("error")}
                
        except Exception as e:
            logger.error(f"pCloud upload error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def sync_agent_documents_to_rag(self, agent_id: str, rag_service) -> Dict[str, Any]:
        docs_result = self.list_agent_documents(agent_id)
        if not docs_result.get("success"):
            return docs_result
            
        synced = []
        errors = []
        
        for doc in docs_result.get("documents", []):
            try:
                file_id = doc.get("id")
                filename = doc.get("name")
                
                download_result = self.download_file(file_id)
                if not download_result.get("success"):
                    errors.append({"file": filename, "error": download_result.get("error")})
                    continue
                
                content = download_result.get("content")
                text_content = self._extract_text(filename, content)
                
                if text_content:
                    rag_service.add_document(
                        agent_id=agent_id,
                        document_id=f"pcloud_{file_id}",
                        content=text_content,
                        metadata={
                            "source": "pcloud",
                            "filename": filename,
                            "file_id": file_id,
                            "synced_at": datetime.utcnow().isoformat()
                        }
                    )
                    synced.append(filename)
                    logger.info(f"Synced {filename} to RAG for agent {agent_id}")
                    
            except Exception as e:
                errors.append({"file": doc.get("name"), "error": str(e)})
                
        return {
            "success": True,
            "agent_id": agent_id,
            "synced_count": len(synced),
            "synced_files": synced,
            "error_count": len(errors),
            "errors": errors
        }
    
    def _extract_text(self, filename: str, content: bytes) -> Optional[str]:
        try:
            if filename.lower().endswith('.txt') or filename.lower().endswith('.md'):
                return content.decode('utf-8', errors='ignore')
            elif filename.lower().endswith('.csv'):
                return content.decode('utf-8', errors='ignore')
            elif filename.lower().endswith('.pdf'):
                return f"[PDF Document: {filename}] - PDF text extraction requires additional libraries"
            elif filename.lower().endswith(('.doc', '.docx')):
                return f"[Word Document: {filename}] - Word text extraction requires additional libraries"
            else:
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Text extraction error for {filename}: {str(e)}")
            return None
    
    def can_read(self, agent_id: str, target_folder: str) -> bool:
        """Verifica si un agente puede leer de una carpeta"""
        agent_permissions = AGENT_READ_PERMISSIONS.get(agent_id, [])
        return target_folder in agent_permissions or agent_id in ["A2_PMO", "A7_DEFENSA", "A8_AUDITOR"]
    
    def can_write(self, agent_id: str, target_folder: str) -> bool:
        """Verifica si un agente puede escribir en una carpeta"""
        write_permissions = AGENT_WRITE_PERMISSIONS.get(agent_id, [])
        return target_folder in write_permissions
    
    def list_files_from_agent_folder(self, requesting_agent: str, target_folder: str) -> Dict[str, Any]:
        """Lista archivos de la carpeta de un agente con verificación de permisos de lectura"""
        if not self.can_read(requesting_agent, target_folder):
            logger.warning(f"Agent {requesting_agent} denied read access to {target_folder}")
            return {"success": False, "error": f"Agent {requesting_agent} does not have read permission for {target_folder}"}
        
        folder_id = AGENT_FOLDER_IDS.get(target_folder)
        if not folder_id:
            return {"success": False, "error": f"Folder {target_folder} not found"}
        
        return self.list_folder(folder_id)
    
    def upload_to_agent_folder(self, requesting_agent: str, target_folder: str, file_path: str, filename: str = None) -> Dict[str, Any]:
        """Sube un archivo a la carpeta de un agente con verificación de permisos de escritura"""
        if not self.can_write(requesting_agent, target_folder):
            logger.warning(f"Agent {requesting_agent} denied write access to {target_folder}")
            return {"success": False, "error": f"Agent {requesting_agent} does not have write permission for {target_folder}"}
        
        folder_id = AGENT_FOLDER_IDS.get(target_folder)
        if not folder_id:
            return {"success": False, "error": f"Folder {target_folder} not found"}
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            if not filename:
                filename = os.path.basename(file_path)
            
            return self.upload_file(folder_id, filename, content)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {"success": False, "error": f"Error reading file: {str(e)}"}
    
    def get_agent_accessible_folders(self, agent_id: str) -> Dict[str, List[str]]:
        """Retorna las carpetas que un agente puede leer y escribir"""
        return {
            "read": AGENT_READ_PERMISSIONS.get(agent_id, []),
            "write": AGENT_WRITE_PERMISSIONS.get(agent_id, [])
        }


    # ═══════════════════════════════════════════════════════════════════════════
    # DEFENSE FILES - Sistema de Documentación por Proyecto
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _sanitizar_nombre(self, nombre: str) -> str:
        """Sanitiza nombre para usar como carpeta"""
        import re
        nombre = re.sub(r'[^\w\s-]', '', nombre)
        nombre = re.sub(r'\s+', '_', nombre)
        return nombre[:50]
    
    def crear_estructura_defense_file(self, cliente_rfc: str, anio: int, 
                                       proyecto_id: int, proyecto_nombre: str) -> Dict[str, Any]:
        """Crea toda la estructura de carpetas para un proyecto de Defense File"""
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        nombre_safe = self._sanitizar_nombre(proyecto_nombre)
        defense_files_folder_id = AGENT_FOLDER_IDS.get("DEFENSE_FILES", 0)
        
        carpetas_creadas = []
        errores = []
        
        try:
            cliente_folder = self.create_folder(defense_files_folder_id, cliente_rfc)
            if not cliente_folder.get("success") and not cliente_folder.get("already_exists"):
                errores.append(f"Error creando carpeta cliente: {cliente_folder.get('error')}")
            cliente_id = cliente_folder.get("folder_id", defense_files_folder_id)
            
            anio_folder = self.create_folder(cliente_id, str(anio))
            anio_id = anio_folder.get("folder_id", cliente_id)
            
            proyecto_folder_name = f"{proyecto_id}_{nombre_safe}"
            proyecto_folder = self.create_folder(anio_id, proyecto_folder_name)
            proyecto_id_folder = proyecto_folder.get("folder_id", anio_id)
            
            subcarpetas = [
                "00_Metadata",
                "A1_Facturar.IA", "A1_Facturar.IA/conversaciones", "A1_Facturar.IA/analisis_cfdi", "A1_Facturar.IA/emails_enviados",
                "A2_Bibliotecar.IA", "A2_Bibliotecar.IA/conversaciones", "A2_Bibliotecar.IA/documentos_consultados", "A2_Bibliotecar.IA/chunks_utilizados",
                "A3_Revisar.IA", "A3_Revisar.IA/revisiones", "A3_Revisar.IA/hallazgos", "A3_Revisar.IA/recomendaciones",
                "A4_Trafico.IA", "A4_Trafico.IA/reportes_sistema", "A4_Trafico.IA/emails_enviados", "A4_Trafico.IA/alertas",
                "A5_Disenar.IA", "A5_Disenar.IA/auditorias_ui",
                "A6_Onboarding", "A6_Onboarding/investigaciones", "A6_Onboarding/clientes_creados",
                "A7_Diagnostico", "A7_Diagnostico/verificaciones",
                "Documentos_Generados", "Documentos_Generados/reportes", "Documentos_Generados/cartas", "Documentos_Generados/calculos",
                "Evidencia_Soporte", "Evidencia_Soporte/screenshots", "Evidencia_Soporte/logs_sistema",
                "_Defense_File_Final"
            ]
            
            folder_map = {proyecto_folder_name: proyecto_id_folder}
            
            for subcarpeta in subcarpetas:
                parts = subcarpeta.split("/")
                if len(parts) == 1:
                    result = self.create_folder(proyecto_id_folder, parts[0])
                    if result.get("success") or result.get("already_exists"):
                        folder_map[parts[0]] = result.get("folder_id", proyecto_id_folder)
                        carpetas_creadas.append(subcarpeta)
                else:
                    parent_name = parts[0]
                    child_name = parts[1]
                    parent_id = folder_map.get(parent_name, proyecto_id_folder)
                    result = self.create_folder(parent_id, child_name)
                    if result.get("success") or result.get("already_exists"):
                        folder_map[f"{parent_name}/{child_name}"] = result.get("folder_id")
                        carpetas_creadas.append(subcarpeta)
            
            metadata = {
                "proyecto_id": proyecto_id,
                "nombre": proyecto_nombre,
                "cliente_rfc": cliente_rfc,
                "anio": anio,
                "creado_en": datetime.utcnow().isoformat(),
                "estructura_version": "1.0"
            }
            metadata_folder_id = folder_map.get("00_Metadata", proyecto_id_folder)
            self.upload_json(metadata_folder_id, "proyecto_info.json", metadata)
            
            return {
                "success": True,
                "proyecto_folder_id": proyecto_id_folder,
                "folder_map": folder_map,
                "carpetas_creadas": len(carpetas_creadas),
                "errores": errores
            }
            
        except Exception as e:
            logger.error(f"Error creando estructura Defense File: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_json(self, folder_id: int, filename: str, data: dict) -> Dict[str, Any]:
        """Sube un archivo JSON a una carpeta"""
        import json
        contenido = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        return self.upload_file(folder_id, filename, contenido.encode('utf-8'))
    
    def documentar_evento_agente(self, proyecto_folder_id: int, agente: str, 
                                  tipo_evento: str, datos: dict) -> Dict[str, Any]:
        """Documenta un evento de un agente en la estructura de Defense File"""
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        agente_map = {
            "facturar": "A1_Facturar.IA",
            "bibliotecar": "A2_Bibliotecar.IA",
            "revisar": "A3_Revisar.IA",
            "trafico": "A4_Trafico.IA",
            "disenar": "A5_Disenar.IA",
            "onboarding": "A6_Onboarding",
            "diagnostico": "A7_Diagnostico"
        }
        
        tipo_subcarpeta = {
            "conversacion": "conversaciones",
            "email": "emails_enviados",
            "analisis": "analisis_cfdi",
            "documento": "documentos_consultados",
            "revision": "revisiones",
            "hallazgo": "hallazgos",
            "alerta": "alertas",
            "investigacion": "investigaciones",
            "verificacion": "verificaciones",
            "auditoria": "auditorias_ui"
        }
        
        carpeta_agente = agente_map.get(agente.lower(), f"A1_{agente}")
        subcarpeta = tipo_subcarpeta.get(tipo_evento.lower(), "conversaciones")
        
        evento = {
            "timestamp": datetime.utcnow().isoformat(),
            "agente": agente,
            "tipo": tipo_evento,
            **datos
        }
        
        filename = f"{timestamp}_{tipo_evento}.json"
        
        try:
            proyecto_contents = self.list_folder(folder_id=proyecto_folder_id)
            agente_folder_id = None
            
            for item in proyecto_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == carpeta_agente:
                    agente_folder_id = item.get("id")
                    break
            
            if agente_folder_id:
                agente_contents = self.list_folder(folder_id=agente_folder_id)
                target_folder_id = agente_folder_id
                
                for item in agente_contents.get("items", []):
                    if item.get("is_folder") and item.get("name") == subcarpeta:
                        target_folder_id = item.get("id")
                        break
                
                upload_result = self.upload_json(target_folder_id, filename, evento)
                
                if upload_result.get("success"):
                    self._actualizar_bitacora(agente_folder_id, agente, tipo_evento, timestamp)
                
                return upload_result
            else:
                return self.upload_json(proyecto_folder_id, filename, evento)
                
        except Exception as e:
            logger.error(f"Error documentando evento: {e}")
            return {"success": False, "error": str(e)}
    
    def _actualizar_bitacora(self, agente_folder_id: int, agente: str, 
                              tipo_evento: str, timestamp: str) -> Dict[str, Any]:
        """Actualiza la bitácora del agente"""
        try:
            bitacora_existente = None
            folder_contents = self.list_folder(folder_id=agente_folder_id)
            
            for item in folder_contents.get("items", []):
                if item.get("name") == "bitacora.json":
                    download_result = self.download_file(item.get("id"))
                    if download_result.get("success"):
                        import json
                        bitacora_existente = json.loads(download_result.get("content", b"{}").decode())
                    break
            
            if not bitacora_existente:
                bitacora_existente = {
                    "agente": agente,
                    "creado": datetime.utcnow().isoformat(),
                    "eventos": [],
                    "resumen": {}
                }
            
            bitacora_existente["eventos"].append({
                "timestamp": timestamp,
                "tipo": tipo_evento
            })
            
            resumen = bitacora_existente.get("resumen", {})
            resumen[tipo_evento] = resumen.get(tipo_evento, 0) + 1
            bitacora_existente["resumen"] = resumen
            bitacora_existente["ultima_actualizacion"] = datetime.utcnow().isoformat()
            
            return self.upload_json(agente_folder_id, "bitacora.json", bitacora_existente)
            
        except Exception as e:
            logger.error(f"Error actualizando bitácora: {e}")
            return {"success": False, "error": str(e)}
    
    def generar_timeline_proyecto(self, proyecto_folder_id: int) -> Dict[str, Any]:
        """Genera un timeline completo de todas las acciones del proyecto"""
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        timeline = []
        
        try:
            proyecto_contents = self.list_folder(folder_id=proyecto_folder_id)
            
            for item in proyecto_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").startswith("A"):
                    agente_name = item.get("name")
                    agente_folder_id = item.get("id")
                    
                    for subitem in self.list_folder(folder_id=agente_folder_id).get("items", []):
                        if subitem.get("name") == "bitacora.json":
                            download = self.download_file(subitem.get("id"))
                            if download.get("success"):
                                import json
                                bitacora = json.loads(download.get("content", b"{}").decode())
                                for evento in bitacora.get("eventos", []):
                                    timeline.append({
                                        "agente": agente_name,
                                        **evento
                                    })
            
            timeline.sort(key=lambda x: x.get("timestamp", ""))
            
            timeline_doc = {
                "generado": datetime.utcnow().isoformat(),
                "total_eventos": len(timeline),
                "timeline": timeline
            }
            
            metadata_folder = None
            for item in proyecto_contents.get("items", []):
                if item.get("name") == "00_Metadata":
                    metadata_folder = item.get("id")
                    break
            
            if metadata_folder:
                self.upload_json(metadata_folder, "timeline_completo.json", timeline_doc)
            
            return {
                "success": True,
                "total_eventos": len(timeline),
                "timeline": timeline
            }
            
        except Exception as e:
            logger.error(f"Error generando timeline: {e}")
            return {"success": False, "error": str(e)}


    # ═══════════════════════════════════════════════════════════════════════════
    # DEFENSE FILES V2 - Sistema Expedientes con 17 Carpetas
    # ═══════════════════════════════════════════════════════════════════════════
    
    DEFENSE_FILES_FOLDER_ID = 29789474531
    
    DEFENSE_FILE_SUBCARPETAS = [
        "00_Indice",
        "01_Datos_Contribuyente",
        "01_Datos_Contribuyente/cfdis",
        "01_Datos_Contribuyente/constancias",
        "02_Proveedores",
        "02_Proveedores/69b",
        "02_Proveedores/efos",
        "03_CFDIs_Analizados",
        "03_CFDIs_Analizados/xml",
        "03_CFDIs_Analizados/pdf",
        "04_Fundamentos_Legales",
        "04_Fundamentos_Legales/articulos",
        "04_Fundamentos_Legales/jurisprudencias",
        "05_Calculos_Fiscales",
        "06_Eventos_Timeline",
        "07_Documentos_Soporte",
        "08_Reportes_Generados"
    ]
    
    def crear_estructura_defense_file_v2(self, rfc: str, anio: int, codigo: str) -> Dict[str, Any]:
        """
        Crea la estructura de 17 carpetas para un Defense File.
        Estructura: DEFENSE_FILES/{RFC}/{ANIO}/{CODIGO}/
        """
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        carpetas_creadas = []
        folder_map = {}
        errores = []
        
        try:
            rfc_folder = self.create_folder(self.DEFENSE_FILES_FOLDER_ID, rfc.upper())
            if not rfc_folder.get("success") and not rfc_folder.get("already_exists"):
                errores.append(f"Error carpeta RFC: {rfc_folder.get('error')}")
            rfc_id = rfc_folder.get("folder_id", self.DEFENSE_FILES_FOLDER_ID)
            
            anio_folder = self.create_folder(rfc_id, str(anio))
            anio_id = anio_folder.get("folder_id", rfc_id)
            
            codigo_folder = self.create_folder(anio_id, codigo)
            codigo_id = codigo_folder.get("folder_id", anio_id)
            folder_map["root"] = codigo_id
            
            for subcarpeta in self.DEFENSE_FILE_SUBCARPETAS:
                parts = subcarpeta.split("/")
                if len(parts) == 1:
                    result = self.create_folder(codigo_id, parts[0])
                    if result.get("success") or result.get("already_exists"):
                        folder_map[parts[0]] = result.get("folder_id", codigo_id)
                        carpetas_creadas.append(subcarpeta)
                else:
                    parent_name = parts[0]
                    child_name = parts[1]
                    parent_id = folder_map.get(parent_name, codigo_id)
                    result = self.create_folder(parent_id, child_name)
                    if result.get("success") or result.get("already_exists"):
                        folder_map[f"{parent_name}/{child_name}"] = result.get("folder_id")
                        carpetas_creadas.append(subcarpeta)
            
            indice_inicial = {
                "expediente": codigo,
                "rfc": rfc.upper(),
                "anio_fiscal": anio,
                "creado_en": datetime.utcnow().isoformat(),
                "estructura": self.DEFENSE_FILE_SUBCARPETAS,
                "total_carpetas": len(carpetas_creadas),
                "eventos": [],
                "documentos": [],
                "version": "2.0"
            }
            indice_folder_id = folder_map.get("00_Indice", codigo_id)
            self.upload_json(indice_folder_id, "indice.json", indice_inicial)
            
            logger.info(f"📁 pCloud: Estructura Defense File creada para {rfc}/{anio}/{codigo}")
            
            return {
                "success": True,
                "defense_file_path": f"{rfc}/{anio}/{codigo}",
                "root_folder_id": codigo_id,
                "folder_map": folder_map,
                "carpetas_creadas": len(carpetas_creadas),
                "errores": errores
            }
            
        except Exception as e:
            logger.error(f"Error creando estructura Defense File V2: {e}")
            return {"success": False, "error": str(e)}
    
    def sincronizar_evento(self, defense_file_path: str, agente_id: str, evento: Dict) -> Dict[str, Any]:
        """
        Sube un evento como archivo JSON a la carpeta de timeline.
        """
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        try:
            parts = defense_file_path.split("/")
            if len(parts) != 3:
                return {"success": False, "error": "Path debe ser RFC/ANIO/CODIGO"}
            
            rfc, anio, codigo = parts
            
            rfc_contents = self.list_folder(folder_id=self.DEFENSE_FILES_FOLDER_ID)
            rfc_folder_id = None
            for item in rfc_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").upper() == rfc.upper():
                    rfc_folder_id = item.get("id")
                    break
            
            if not rfc_folder_id:
                return {"success": False, "error": f"No se encontró carpeta RFC: {rfc}"}
            
            anio_contents = self.list_folder(folder_id=rfc_folder_id)
            anio_folder_id = None
            for item in anio_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == str(anio):
                    anio_folder_id = item.get("id")
                    break
            
            if not anio_folder_id:
                return {"success": False, "error": f"No se encontró carpeta año: {anio}"}
            
            codigo_contents = self.list_folder(folder_id=anio_folder_id)
            codigo_folder_id = None
            for item in codigo_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == codigo:
                    codigo_folder_id = item.get("id")
                    break
            
            if not codigo_folder_id:
                return {"success": False, "error": f"No se encontró expediente: {codigo}"}
            
            expediente_contents = self.list_folder(folder_id=codigo_folder_id)
            timeline_folder_id = None
            for item in expediente_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == "06_Eventos_Timeline":
                    timeline_folder_id = item.get("id")
                    break
            
            if not timeline_folder_id:
                result = self.create_folder(codigo_folder_id, "06_Eventos_Timeline")
                timeline_folder_id = result.get("folder_id", codigo_folder_id)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            evento_id = evento.get("id", "")
            filename = f"{timestamp}_{agente_id}_{evento_id}.json"
            
            evento_data = {
                "sincronizado_en": datetime.utcnow().isoformat(),
                "agente": agente_id,
                **evento
            }
            
            upload_result = self.upload_json(timeline_folder_id, filename, evento_data)
            
            if upload_result.get("success"):
                logger.info(f"📁 pCloud: Evento sincronizado {filename}")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error sincronizando evento: {e}")
            return {"success": False, "error": str(e)}
    
    def sincronizar_documento(self, defense_file_path: str, tipo_documento: str, 
                               nombre: str, contenido: bytes) -> Dict[str, Any]:
        """
        Sube un documento al expediente en la carpeta correspondiente.
        tipo_documento: cfdi_xml, cfdi_pdf, fundamento, calculo, soporte, reporte
        """
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        tipo_a_carpeta = {
            "cfdi_xml": "03_CFDIs_Analizados/xml",
            "cfdi_pdf": "03_CFDIs_Analizados/pdf",
            "fundamento_articulo": "04_Fundamentos_Legales/articulos",
            "fundamento_jurisprudencia": "04_Fundamentos_Legales/jurisprudencias",
            "calculo": "05_Calculos_Fiscales",
            "soporte": "07_Documentos_Soporte",
            "reporte": "08_Reportes_Generados",
            "proveedor_69b": "02_Proveedores/69b",
            "proveedor_efos": "02_Proveedores/efos",
            "abogado_diablo": "09_Abogado_Diablo"
        }
        
        carpeta_destino = tipo_a_carpeta.get(tipo_documento, "07_Documentos_Soporte")
        
        try:
            parts = defense_file_path.split("/")
            if len(parts) != 3:
                return {"success": False, "error": "Path debe ser RFC/ANIO/CODIGO"}
            
            rfc, anio, codigo = parts
            
            rfc_contents = self.list_folder(folder_id=self.DEFENSE_FILES_FOLDER_ID)
            rfc_folder_id = None
            for item in rfc_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").upper() == rfc.upper():
                    rfc_folder_id = item.get("id")
                    break
            
            if not rfc_folder_id:
                return {"success": False, "error": f"No se encontró carpeta RFC: {rfc}"}
            
            anio_contents = self.list_folder(folder_id=rfc_folder_id)
            anio_folder_id = None
            for item in anio_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == str(anio):
                    anio_folder_id = item.get("id")
                    break
            
            if not anio_folder_id:
                return {"success": False, "error": f"No se encontró carpeta año: {anio}"}
            
            codigo_contents = self.list_folder(folder_id=anio_folder_id)
            codigo_folder_id = None
            for item in codigo_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == codigo:
                    codigo_folder_id = item.get("id")
                    break
            
            if not codigo_folder_id:
                return {"success": False, "error": f"No se encontró expediente: {codigo}"}
            
            carpeta_parts = carpeta_destino.split("/")
            target_folder_id = codigo_folder_id
            
            expediente_contents = self.list_folder(folder_id=codigo_folder_id)
            for item in expediente_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == carpeta_parts[0]:
                    target_folder_id = item.get("id")
                    break
            
            if len(carpeta_parts) > 1:
                sub_contents = self.list_folder(folder_id=target_folder_id)
                for item in sub_contents.get("items", []):
                    if item.get("is_folder") and item.get("name") == carpeta_parts[1]:
                        target_folder_id = item.get("id")
                        break
            
            upload_result = self.upload_file(target_folder_id, nombre, contenido)
            
            if upload_result.get("success"):
                logger.info(f"📁 pCloud: Documento sincronizado {nombre} en {carpeta_destino}")
                file_id = upload_result.get("file_id")
                link_result = self.get_or_create_public_link(file_id)
                upload_result["public_link"] = link_result.get("public_link", "")
            
            return upload_result
            
        except Exception as e:
            logger.error(f"Error sincronizando documento: {e}")
            return {"success": False, "error": str(e)}
    
    def generar_indice(self, defense_file_path: str) -> Dict[str, Any]:
        """
        Genera/actualiza el índice completo del expediente.
        Recorre todas las carpetas y lista los archivos.
        """
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        try:
            parts = defense_file_path.split("/")
            if len(parts) != 3:
                return {"success": False, "error": "Path debe ser RFC/ANIO/CODIGO"}
            
            rfc, anio, codigo = parts
            
            rfc_contents = self.list_folder(folder_id=self.DEFENSE_FILES_FOLDER_ID)
            rfc_folder_id = None
            for item in rfc_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").upper() == rfc.upper():
                    rfc_folder_id = item.get("id")
                    break
            
            if not rfc_folder_id:
                return {"success": False, "error": f"No se encontró carpeta RFC: {rfc}"}
            
            anio_contents = self.list_folder(folder_id=rfc_folder_id)
            anio_folder_id = None
            for item in anio_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == str(anio):
                    anio_folder_id = item.get("id")
                    break
            
            if not anio_folder_id:
                return {"success": False, "error": f"No se encontró carpeta año: {anio}"}
            
            codigo_contents = self.list_folder(folder_id=anio_folder_id)
            codigo_folder_id = None
            for item in codigo_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == codigo:
                    codigo_folder_id = item.get("id")
                    break
            
            if not codigo_folder_id:
                return {"success": False, "error": f"No se encontró expediente: {codigo}"}
            
            indice = {
                "expediente": codigo,
                "rfc": rfc.upper(),
                "anio_fiscal": int(anio),
                "generado_en": datetime.utcnow().isoformat(),
                "carpetas": {},
                "total_archivos": 0,
                "total_carpetas": 0
            }
            
            def listar_recursivo(folder_id: int, path: str):
                contents = self.list_folder(folder_id=folder_id)
                archivos = []
                subcarpetas = {}
                
                for item in contents.get("items", []):
                    if item.get("is_folder"):
                        subcarpeta_path = f"{path}/{item.get('name')}" if path else item.get("name")
                        subcarpetas[item.get("name")] = listar_recursivo(item.get("id"), subcarpeta_path)
                        indice["total_carpetas"] += 1
                    else:
                        archivos.append({
                            "nombre": item.get("name"),
                            "tamaño": item.get("size", 0),
                            "id": item.get("id")
                        })
                        indice["total_archivos"] += 1
                
                return {"archivos": archivos, "subcarpetas": subcarpetas}
            
            indice["carpetas"] = listar_recursivo(codigo_folder_id, "")
            
            indice_folder_id = None
            expediente_contents = self.list_folder(folder_id=codigo_folder_id)
            for item in expediente_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == "00_Indice":
                    indice_folder_id = item.get("id")
                    break
            
            if indice_folder_id:
                self.upload_json(indice_folder_id, "indice.json", indice)
            
            logger.info(f"📁 pCloud: Índice generado para {defense_file_path}")
            
            return {
                "success": True,
                "indice": indice,
                "total_archivos": indice["total_archivos"],
                "total_carpetas": indice["total_carpetas"]
            }
            
        except Exception as e:
            logger.error(f"Error generando índice: {e}")
            return {"success": False, "error": str(e)}
    
    def listar_documentos_expediente(self, defense_file_path: str) -> Dict[str, Any]:
        """Lista todos los documentos de un expediente con sus rutas."""
        if not self.auth_token:
            login_result = self.login()
            if not login_result.get("success"):
                return login_result
        
        try:
            parts = defense_file_path.split("/")
            if len(parts) != 3:
                return {"success": False, "error": "Path debe ser RFC/ANIO/CODIGO"}
            
            rfc, anio, codigo = parts
            
            rfc_contents = self.list_folder(folder_id=self.DEFENSE_FILES_FOLDER_ID)
            rfc_folder_id = None
            for item in rfc_contents.get("items", []):
                if item.get("is_folder") and item.get("name", "").upper() == rfc.upper():
                    rfc_folder_id = item.get("id")
                    break
            
            if not rfc_folder_id:
                return {"success": False, "error": f"No se encontró carpeta RFC: {rfc}"}
            
            anio_contents = self.list_folder(folder_id=rfc_folder_id)
            anio_folder_id = None
            for item in anio_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == str(anio):
                    anio_folder_id = item.get("id")
                    break
            
            if not anio_folder_id:
                return {"success": False, "error": f"No se encontró carpeta año: {anio}"}
            
            codigo_contents = self.list_folder(folder_id=anio_folder_id)
            codigo_folder_id = None
            for item in codigo_contents.get("items", []):
                if item.get("is_folder") and item.get("name") == codigo:
                    codigo_folder_id = item.get("id")
                    break
            
            if not codigo_folder_id:
                return {"success": False, "error": f"No se encontró expediente: {codigo}"}
            
            documentos = []
            
            def listar_recursivo(folder_id: int, path: str):
                contents = self.list_folder(folder_id=folder_id)
                for item in contents.get("items", []):
                    if item.get("is_folder"):
                        subcarpeta_path = f"{path}/{item.get('name')}" if path else item.get("name")
                        listar_recursivo(item.get("id"), subcarpeta_path)
                    else:
                        documentos.append({
                            "nombre": item.get("name"),
                            "ruta": f"{path}/{item.get('name')}" if path else item.get("name"),
                            "tamaño": item.get("size", 0),
                            "id": item.get("id"),
                            "tipo": item.get("content_type", ""),
                            "modificado": item.get("modified")
                        })
            
            listar_recursivo(codigo_folder_id, "")
            
            return {
                "success": True,
                "documentos": documentos,
                "total": len(documentos)
            }
            
        except Exception as e:
            logger.error(f"Error listando documentos: {e}")
            return {"success": False, "error": str(e)}


pcloud_service = PCloudService()


async def upload_defense_file(local_path: str, remote_folder: str) -> Dict[str, Any]:
    """Wrapper async para subir archivos de defensa"""
    if not pcloud_service.is_available():
        import hashlib
        fake_id = hashlib.md5(local_path.encode()).hexdigest()[:10]
        return {
            "success": True,
            "simulado": True,
            "file_id": f"demo-{fake_id}",
            "public_link": f"https://demo.pcloud.link/{fake_id}"
        }
    
    login_result = pcloud_service.login()
    if not login_result.get("success"):
        return {"success": False, "error": login_result.get("error")}
    
    try:
        with open(local_path, 'rb') as f:
            content = f.read()
        
        import os
        filename = os.path.basename(local_path)
        
        folder_id = AGENT_FOLDER_IDS.get("DEFENSE_FILES", 0)
        
        upload_result = pcloud_service.upload_file(folder_id, filename, content)
        
        if upload_result.get("success"):
            file_id = upload_result.get("file_id")
            link_result = pcloud_service.get_or_create_public_link(file_id)
            
            return {
                "success": True,
                "simulado": False,
                "file_id": str(file_id),
                "filename": filename,
                "public_link": link_result.get("public_link", "")
            }
        return upload_result
    except Exception as e:
        return {"success": False, "error": str(e)}
