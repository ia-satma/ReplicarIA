"""
Defense File Service
Manages the audit trail and evidence storage for SAT compliance
Each project has a complete Defense File with all deliberations and communications
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from config.agents_config import AGENT_CONFIGURATIONS

logger = logging.getLogger(__name__)

DEFENSE_FILES_DIR = Path("./defense_files")
DEFENSE_FILES_DIR.mkdir(exist_ok=True)


class DefenseFile:
    """
    Represents a complete Defense File for a project with multi-tenant isolation
    Contains all evidence needed for SAT audit compliance:
    - Project details
    - Deliberation trail
    - Agent communications (emails)
    - RAG context used
    - Provider communications
    - Generated documents
    - Final decision and justification
    """
    
    def __init__(self, project_id: str, empresa_id: Optional[str] = None):
        self.project_id = project_id
        self.empresa_id = empresa_id
        self.created_at = datetime.now(timezone.utc)
        self.project_data: Dict = {}
        self.deliberations: List[Dict] = []
        self.emails: List[Dict] = []
        self.provider_communications: List[Dict] = []
        self.rag_contexts: List[Dict] = []
        self.documents: List[Dict] = []
        self.final_decision: Optional[str] = None
        self.final_justification: Optional[str] = None
        self.compliance_checklist: Dict[str, bool] = {
            "razon_de_negocios": False,
            "beneficio_economico": False,
            "materialidad": False,
            "trazabilidad": False
        }
        self.pcloud_links: Dict[str, str] = {}
        self.pcloud_documents: List[Dict] = []
        self.bitacora_link: Optional[str] = None
        self.consolidation_report: Optional[Dict] = None
        
        self.agent_opinions: List[Dict] = []
        self.purchase_orders: List[Dict] = []
        self.contract_requests: List[Dict] = []
        self.provider_change_requests: List[Dict] = []
        self.version_history: List[Dict] = []
        
        self._load_pcloud_links()
    
    def _load_pcloud_links(self):
        """Load pCloud links for each agent"""
        for agent_id, config in AGENT_CONFIGURATIONS.items():
            if config.get("pcloud_link"):
                self.pcloud_links[agent_id] = config["pcloud_link"]
    
    def set_project_data(self, project: Dict):
        """Set the project data"""
        self.project_data = project
    
    def add_deliberation(self, deliberation: Dict):
        """Add a deliberation record"""
        deliberation["recorded_at"] = datetime.now(timezone.utc).isoformat()
        self.deliberations.append(deliberation)
        self._update_compliance_checklist()
    
    def add_email(self, email: Dict):
        """Add an email record"""
        email["recorded_at"] = datetime.now(timezone.utc).isoformat()
        self.emails.append(email)
        self.compliance_checklist["materialidad"] = True
    
    def add_provider_communication(self, communication: Dict):
        """Add a provider communication record"""
        communication["recorded_at"] = datetime.now(timezone.utc).isoformat()
        self.provider_communications.append(communication)
    
    def add_rag_context(self, agent_id: str, query: str, results: List[Dict]):
        """Add RAG context used during deliberation"""
        self.rag_contexts.append({
            "agent_id": agent_id,
            "query": query,
            "results": results,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })
    
    def add_document(
        self,
        stage: str,
        agent_id: str,
        doc_type: str,
        file_path: str,
        version: int = 1,
        pcloud_link: str = None
    ):
        """Add a generated document record with metadata"""
        self.documents.append({
            "project_id": self.project_id,
            "stage": stage,
            "agent_id": agent_id,
            "doc_type": doc_type,
            "file_path": file_path,
            "pcloud_link": pcloud_link,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "version": version
        })
    
    def add_pcloud_document(
        self,
        agent_id: str,
        doc_type: str,
        local_path: str,
        pcloud_path: str,
        pcloud_link: str,
        file_id: int = None
    ):
        """Add a pCloud document reference"""
        self.pcloud_documents.append({
            "agent_id": agent_id,
            "doc_type": doc_type,
            "local_path": local_path,
            "pcloud_path": pcloud_path,
            "pcloud_link": pcloud_link,
            "file_id": file_id,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        })
    
    def set_bitacora_link(self, pcloud_link: str):
        """Set the pCloud link for the final bitácora"""
        self.bitacora_link = pcloud_link
    
    def set_consolidation_report(self, consolidation_data: Dict):
        """Set the PMO consolidation report data"""
        self.consolidation_report = {
            **consolidation_data,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        self.save()
    
    def get_all_pcloud_links(self) -> Dict[str, Any]:
        """Get all pCloud links organized by type"""
        return {
            "agent_folders": self.pcloud_links,
            "documents": self.pcloud_documents,
            "bitacora": self.bitacora_link
        }
    
    def set_final_decision(self, decision: str, justification: str):
        """Set the final decision"""
        self.final_decision = decision
        self.final_justification = justification
    
    def add_agent_opinion(
        self,
        agent_id: str,
        agent_name: str,
        opinion_type: str,
        content: str,
        decision: str,
        metadata: Dict = None
    ):
        """Registra la opinión de un agente o subagente"""
        self.agent_opinions.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            "opinion_type": opinion_type,
            "content": content,
            "decision": decision,
            "metadata": metadata or {},
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })

    def add_purchase_order(
        self,
        po_number: str,
        amount: float,
        currency: str,
        vendor: str,
        description: str,
        created_by: str,
        status: str = "draft"
    ):
        """Registra una orden de compra"""
        self.purchase_orders.append({
            "po_number": po_number,
            "amount": amount,
            "currency": currency,
            "vendor": vendor,
            "description": description,
            "created_by": created_by,
            "status": status,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })

    def add_contract_request(
        self,
        request_id: str,
        requester_agent: str,
        contract_type: str,
        vendor_name: str,
        terms: str,
        status: str = "pending"
    ):
        """Registra una solicitud de contrato a Legal"""
        self.contract_requests.append({
            "request_id": request_id,
            "requester_agent": requester_agent,
            "contract_type": contract_type,
            "vendor_name": vendor_name,
            "terms": terms,
            "status": status,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })

    def add_provider_change_request(
        self,
        request_id: str,
        requester_agent: str,
        provider_email: str,
        change_type: str,
        description: str,
        deadline: str = None,
        status: str = "pending"
    ):
        """Registra cambios solicitados al proveedor"""
        self.provider_change_requests.append({
            "request_id": request_id,
            "requester_agent": requester_agent,
            "provider_email": provider_email,
            "change_type": change_type,
            "description": description,
            "deadline": deadline,
            "status": status,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })

    def add_version_entry(
        self,
        version_number: int,
        change_type: str,
        description: str,
        changed_by: str,
        affected_fields: List[str] = None
    ):
        """Registra un cambio de versión"""
        self.version_history.append({
            "version_number": version_number,
            "change_type": change_type,
            "description": description,
            "changed_by": changed_by,
            "affected_fields": affected_fields or [],
            "recorded_at": datetime.now(timezone.utc).isoformat()
        })
    
    def _update_compliance_checklist(self):
        """Update compliance checklist based on deliberations"""
        for delib in self.deliberations:
            analysis = delib.get("analysis", "").lower()
            
            if "razón de negocios" in analysis or "razon de negocios" in analysis:
                self.compliance_checklist["razon_de_negocios"] = True
            if "beneficio económico" in analysis or "beneficio economico" in analysis:
                self.compliance_checklist["beneficio_economico"] = True
            if "materialidad" in analysis:
                self.compliance_checklist["materialidad"] = True
        
        if len(self.deliberations) >= 2:
            self.compliance_checklist["trazabilidad"] = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "project_id": self.project_id,
            "empresa_id": self.empresa_id,
            "created_at": self.created_at.isoformat(),
            "project_data": self.project_data,
            "deliberation_count": len(self.deliberations),
            "deliberations": self.deliberations,
            "email_count": len(self.emails),
            "emails": self.emails,
            "provider_communications": self.provider_communications,
            "rag_contexts": self.rag_contexts,
            "documents": self.documents,
            "document_count": len(self.documents),
            "final_decision": self.final_decision,
            "final_justification": self.final_justification,
            "compliance_checklist": self.compliance_checklist,
            "compliance_score": sum(self.compliance_checklist.values()) / len(self.compliance_checklist) * 100,
            "pcloud_links": self.pcloud_links,
            "pcloud_documents": self.pcloud_documents,
            "pcloud_document_count": len(self.pcloud_documents),
            "bitacora_link": self.bitacora_link,
            "consolidation_report": self.consolidation_report,
            "agent_opinions": self.agent_opinions,
            "agent_opinions_count": len(self.agent_opinions),
            "purchase_orders": self.purchase_orders,
            "purchase_orders_count": len(self.purchase_orders),
            "contract_requests": self.contract_requests,
            "contract_requests_count": len(self.contract_requests),
            "provider_change_requests": self.provider_change_requests,
            "provider_change_requests_count": len(self.provider_change_requests),
            "version_history": self.version_history,
            "version_history_count": len(self.version_history),
            "audit_ready": all(self.compliance_checklist.values())
        }
    
    def _get_empresa_dir(self) -> Path:
        """Get empresa-specific directory for defense files"""
        if self.empresa_id:
            empresa_dir = DEFENSE_FILES_DIR / self.empresa_id
            empresa_dir.mkdir(parents=True, exist_ok=True)
            return empresa_dir
        return DEFENSE_FILES_DIR
    
    def save(self):
        """Save Defense File to disk in empresa-specific directory"""
        empresa_dir = self._get_empresa_dir()
        file_path = empresa_dir / f"{self.project_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Defense File saved: {file_path}")
    
    @classmethod
    def load(cls, project_id: str, empresa_id: Optional[str] = None) -> Optional["DefenseFile"]:
        """Load Defense File from disk, checking empresa directory first"""
        if empresa_id:
            empresa_dir = DEFENSE_FILES_DIR / empresa_id
            file_path = empresa_dir / f"{project_id}.json"
            if file_path.exists():
                return cls._load_from_path(file_path, project_id, empresa_id)
        
        file_path = DEFENSE_FILES_DIR / f"{project_id}.json"
        if file_path.exists():
            return cls._load_from_path(file_path, project_id, empresa_id)
        
        for empresa_dir in DEFENSE_FILES_DIR.iterdir():
            if empresa_dir.is_dir():
                file_path = empresa_dir / f"{project_id}.json"
                if file_path.exists():
                    return cls._load_from_path(file_path, project_id, empresa_dir.name)
        
        return None
    
    @classmethod
    def _load_from_path(cls, file_path: Path, project_id: str, empresa_id: Optional[str] = None) -> Optional["DefenseFile"]:
        """Load Defense File from a specific path"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            loaded_empresa_id = data.get("empresa_id") or empresa_id
            df = cls(project_id, empresa_id=loaded_empresa_id)
            df.created_at = datetime.fromisoformat(data.get("created_at", df.created_at.isoformat()))
            df.project_data = data.get("project_data", {})
            df.deliberations = data.get("deliberations", [])
            df.emails = data.get("emails", [])
            df.provider_communications = data.get("provider_communications", [])
            df.rag_contexts = data.get("rag_contexts", [])
            df.documents = data.get("documents", [])
            df.final_decision = data.get("final_decision")
            df.final_justification = data.get("final_justification")
            df.compliance_checklist = data.get("compliance_checklist", df.compliance_checklist)
            df.pcloud_documents = data.get("pcloud_documents", [])
            df.bitacora_link = data.get("bitacora_link")
            df.consolidation_report = data.get("consolidation_report")
            df.agent_opinions = data.get("agent_opinions", [])
            df.purchase_orders = data.get("purchase_orders", [])
            df.contract_requests = data.get("contract_requests", [])
            df.provider_change_requests = data.get("provider_change_requests", [])
            df.version_history = data.get("version_history", [])
            
            return df
        except Exception as e:
            logger.error(f"Error loading Defense File {project_id}: {e}")
            return None


class DefenseFileService:
    """
    Service for managing Defense Files with multi-tenant isolation
    """
    
    def __init__(self):
        self.defense_files: Dict[str, DefenseFile] = {}
    
    def get_or_create(self, project_id: str, empresa_id: Optional[str] = None) -> DefenseFile:
        """Get existing or create new Defense File"""
        cache_key = f"{empresa_id}:{project_id}" if empresa_id else project_id
        
        if cache_key not in self.defense_files:
            existing = DefenseFile.load(project_id, empresa_id)
            if existing:
                self.defense_files[cache_key] = existing
            else:
                self.defense_files[cache_key] = DefenseFile(project_id, empresa_id=empresa_id)
        
        return self.defense_files[cache_key]
    
    def create_defense_file(self, project_id: str, project_data: Dict) -> DefenseFile:
        """Create a new Defense File for a project with empresa_id from project data"""
        empresa_id = project_data.get("empresa_id")
        df = DefenseFile(project_id, empresa_id=empresa_id)
        df.set_project_data(project_data)
        cache_key = f"{empresa_id}:{project_id}" if empresa_id else project_id
        self.defense_files[cache_key] = df
        df.save()
        return df
    
    def add_deliberation(self, project_id: str, deliberation: Dict):
        """Add a deliberation to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_deliberation(deliberation)
        df.save()
    
    def add_email(self, project_id: str, email: Dict):
        """Add an email to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_email(email)
        df.save()
    
    def add_provider_communication(self, project_id: str, communication: Dict):
        """Add a provider communication to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_provider_communication(communication)
        df.save()
    
    def add_document(
        self,
        project_id: str,
        stage: str,
        agent_id: str,
        doc_type: str,
        file_path: str,
        version: int = 1,
        pcloud_link: str = None
    ):
        """Add a generated document to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_document(stage, agent_id, doc_type, file_path, version, pcloud_link)
        df.save()
    
    def add_pcloud_document(
        self,
        project_id: str,
        agent_id: str,
        doc_type: str,
        local_path: str,
        pcloud_path: str,
        pcloud_link: str,
        file_id: int = None
    ):
        """Add a pCloud document reference to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_pcloud_document(agent_id, doc_type, local_path, pcloud_path, pcloud_link, file_id)
        df.save()
    
    def set_bitacora_link(self, project_id: str, pcloud_link: str):
        """Set the bitácora pCloud link for a project"""
        df = self.get_or_create(project_id)
        df.set_bitacora_link(pcloud_link)
        df.save()
    
    def set_consolidation_report(self, project_id: str, consolidation_data: Dict):
        """Set the PMO consolidation report for a project"""
        df = self.get_or_create(project_id)
        df.set_consolidation_report(consolidation_data)
    
    def get_pcloud_links(self, project_id: str) -> Dict[str, Any]:
        """Get all pCloud links for a project"""
        df = self.get_or_create(project_id)
        return df.get_all_pcloud_links()
    
    def get_document_count(self, project_id: str, agent_id: str) -> int:
        """Get count of documents for a specific agent in a project"""
        df = self.get_or_create(project_id)
        return len([d for d in df.documents if d.get("agent_id") == agent_id])
    
    def get_defense_file(self, project_id: str) -> Optional[Dict]:
        """Get a Defense File as dictionary"""
        df = self.get_or_create(project_id)
        return df.to_dict() if df else None
    
    def finalize_defense_file(self, project_id: str, decision: str, justification: str) -> Dict:
        """Finalize a Defense File with the final decision"""
        df = self.get_or_create(project_id)
        df.set_final_decision(decision, justification)
        df.save()
        return df.to_dict()
    
    def export_for_sat(self, project_id: str) -> Dict:
        """
        Export Defense File in SAT-ready format
        Includes all compliance documentation
        """
        df = self.get_or_create(project_id)
        data = df.to_dict()
        
        data["sat_export"] = {
            "version": "1.0",
            "export_date": datetime.now(timezone.utc).isoformat(),
            "compliance_summary": {
                "articulo_5a_cff": {
                    "cumplimiento": df.compliance_checklist.get("razon_de_negocios", False),
                    "descripcion": "Razón de Negocios - Los actos jurídicos tienen una razón de negocios documentada"
                },
                "articulo_27_lisr": {
                    "cumplimiento": df.compliance_checklist.get("beneficio_economico", False),
                    "descripcion": "Beneficio Económico Esperado - Existe beneficio económico cuantificable"
                },
                "articulo_69b_cff": {
                    "cumplimiento": df.compliance_checklist.get("materialidad", False),
                    "descripcion": "Materialidad - Evidencia de servicios realmente prestados"
                },
                "nom_151": {
                    "cumplimiento": df.compliance_checklist.get("trazabilidad", False),
                    "descripcion": "Trazabilidad - Trail completo de deliberaciones y comunicaciones"
                }
            },
            "evidence_count": {
                "deliberations": len(df.deliberations),
                "emails": len(df.emails),
                "provider_communications": len(df.provider_communications),
                "rag_documents_referenced": len(df.rag_contexts)
            },
            "pcloud_document_repositories": df.pcloud_links,
            "audit_trail_complete": df.compliance_checklist.get("trazabilidad", False)
        }
        
        return data
    
    def list_all(self, empresa_id: Optional[str] = None) -> List[Dict]:
        """
        List all Defense Files with full deliberation data.
        If empresa_id is provided, filters by empresa_id.
        """
        files = []
        for file_path in DEFENSE_FILES_DIR.glob("**/*.json"):
            project_id = file_path.stem
            df = self.get_or_create(project_id)
            
            if empresa_id:
                df_empresa = df.project_data.get("empresa_id")
                if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
                    continue
            
            files.append({
                "project_id": project_id,
                "created_at": df.created_at.isoformat(),
                "empresa_id": df.project_data.get("empresa_id"),
                "project_data": df.project_data,
                "deliberations": df.deliberations,
                "deliberation_count": len(df.deliberations),
                "documents": df.documents,
                "pcloud_documents": df.pcloud_documents,
                "pcloud_links": df.pcloud_links,
                "bitacora_link": df.bitacora_link,
                "compliance_score": sum(df.compliance_checklist.values()) / len(df.compliance_checklist) * 100,
                "compliance_checklist": df.compliance_checklist,
                "audit_ready": all(df.compliance_checklist.values()),
                "final_decision": df.final_decision,
                "final_justification": df.final_justification,
                "emails": df.emails,
                "provider_communications": df.provider_communications,
                "agent_opinions": df.agent_opinions,
                "purchase_orders": df.purchase_orders,
                "contract_requests": df.contract_requests,
                "provider_change_requests": df.provider_change_requests,
                "version_history": df.version_history
            })
        return files
    
    def get_defense_file_by_empresa(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> Optional[Dict]:
        """Get a Defense File as dictionary, validating empresa ownership"""
        df = self.get_or_create(project_id)
        if not df:
            return None
        
        df_empresa = df.project_data.get("empresa_id")
        if df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
            return None
        
        return df.to_dict()

    def add_agent_opinion(
        self,
        project_id: str,
        agent_id: str,
        agent_name: str,
        opinion_type: str,
        content: str,
        decision: str,
        metadata: Dict = None
    ):
        """Add an agent opinion to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_agent_opinion(agent_id, agent_name, opinion_type, content, decision, metadata)
        df.save()

    def add_purchase_order(
        self,
        project_id: str,
        po_number: str,
        amount: float,
        currency: str,
        vendor: str,
        description: str,
        created_by: str,
        status: str = "draft"
    ):
        """Add a purchase order to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_purchase_order(po_number, amount, currency, vendor, description, created_by, status)
        df.save()

    def add_contract_request(
        self,
        project_id: str,
        request_id: str,
        requester_agent: str,
        contract_type: str,
        vendor_name: str,
        terms: str,
        status: str = "pending"
    ):
        """Add a contract request to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_contract_request(request_id, requester_agent, contract_type, vendor_name, terms, status)
        df.save()

    def add_provider_change_request(
        self,
        project_id: str,
        request_id: str,
        requester_agent: str,
        provider_email: str,
        change_type: str,
        description: str,
        deadline: str = None,
        status: str = "pending"
    ):
        """Add a provider change request to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_provider_change_request(request_id, requester_agent, provider_email, change_type, description, deadline, status)
        df.save()

    def add_version_entry(
        self,
        project_id: str,
        version_number: int,
        change_type: str,
        description: str,
        changed_by: str,
        affected_fields: List[str] = None
    ):
        """Add a version entry to a project's Defense File"""
        df = self.get_or_create(project_id)
        df.add_version_entry(version_number, change_type, description, changed_by, affected_fields)
        df.save()


defense_file_service = DefenseFileService()
