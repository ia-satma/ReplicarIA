"""
Revisar.IA - Database Service for MongoDB
Handles all CRUD operations for Revisar.IA fiscal audit system collections
Uses lazy initialization to share connection with main server
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from models.durezza_models import (
    Project, Supplier, ProjectPhase, AgentDeliberation, DefenseFile,
    ChecklistTemplate, AgentConfig, Document, AuditLog
)
from models.durezza_enums import (
    TipologiaProyecto, FaseProyecto, EstadoGlobal, TipoAgente, AccionAuditLog
)

logger = logging.getLogger(__name__)

_db = None
_demo_mode = None

def get_db():
    global _db, _demo_mode
    if _db is not None or _demo_mode is True:
        return _db, _demo_mode
    
    mongo_url = os.environ.get('MONGO_URL', '')
    db_name = os.environ.get('DB_NAME', 'revisar_agent_network')
    
    if not mongo_url or not mongo_url.startswith(('mongodb://', 'mongodb+srv://')):
        logger.warning("MONGO_URL not set or invalid format - Revisar.IA using demo mode")
        _demo_mode = True
        return None, True
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        _db = client[db_name]
        _demo_mode = False
        logger.info(f"Revisar.IA DB connected to MongoDB: {db_name}")
        return _db, False
    except Exception as e:
        logger.warning(f"Revisar.IA MongoDB connection failed: {e}, using demo mode")
        _demo_mode = True
        return None, True


DEMO_SUPPLIERS: List[Dict[str, Any]] = []
DEMO_PROJECTS: List[Dict[str, Any]] = []
DEMO_PROJECT_PHASES: List[Dict[str, Any]] = []
DEMO_DELIBERATIONS: List[Dict[str, Any]] = []
DEMO_DEFENSE_FILES: List[Dict[str, Any]] = []
DEMO_CHECKLIST_TEMPLATES: List[Dict[str, Any]] = []
DEMO_AGENT_CONFIGS: List[Dict[str, Any]] = []
DEMO_DOCUMENTS: List[Dict[str, Any]] = []
DEMO_AUDIT_LOGS: List[Dict[str, Any]] = []


def clean_mongo_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    doc.pop('_id', None)
    return doc


def clean_mongo_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [clean_mongo_doc(d) for d in docs if d is not None]


class DurezzaDatabaseService:
    @property
    def demo_mode(self):
        _, demo = get_db()
        return demo
    
    def _get_db(self):
        db, _ = get_db()
        return db

    async def create_indexes(self):
        if self.demo_mode:
            return
        try:
            await self._get_db().durezza_suppliers.create_index("rfc", unique=True)
            await self._get_db().durezza_suppliers.create_index("tipo_relacion")
            await self._get_db().durezza_suppliers.create_index("alerta_efos")
            await self._get_db().durezza_suppliers.create_index("activo")

            await self._get_db().durezza_projects.create_index("estado_global")
            await self._get_db().durezza_projects.create_index("fase_actual")
            await self._get_db().durezza_projects.create_index("tipologia")
            await self._get_db().durezza_projects.create_index("proveedor_id")
            await self._get_db().durezza_projects.create_index("created_at")

            await self._get_db().durezza_project_phases.create_index("proyecto_id")
            await self._get_db().durezza_project_phases.create_index("fase")
            await self._get_db().durezza_project_phases.create_index("estado")
            await self._get_db().durezza_project_phases.create_index([("proyecto_id", 1), ("fase", 1)], unique=True)

            await self._get_db().durezza_deliberations.create_index("proyecto_id")
            await self._get_db().durezza_deliberations.create_index("agente")
            await self._get_db().durezza_deliberations.create_index("fase")
            await self._get_db().durezza_deliberations.create_index("decision")
            await self._get_db().durezza_deliberations.create_index([("proyecto_id", 1), ("agente", 1), ("fase", 1), ("version", 1)], unique=True)

            await self._get_db().durezza_defense_files.create_index("proyecto_id", unique=True)
            await self._get_db().durezza_defense_files.create_index("vbc_fiscal_emitido")
            await self._get_db().durezza_defense_files.create_index("vbc_legal_emitido")
            await self._get_db().durezza_defense_files.create_index("indice_defendibilidad")

            await self._get_db().durezza_checklist_templates.create_index([("tipologia", 1), ("fase", 1)], unique=True)
            await self._get_db().durezza_checklist_templates.create_index("activo")

            await self._get_db().durezza_agent_configs.create_index("agente", unique=True)
            await self._get_db().durezza_agent_configs.create_index("activo")

            await self._get_db().durezza_documents.create_index("proyecto_id")
            await self._get_db().durezza_documents.create_index("defense_file_id")
            await self._get_db().durezza_documents.create_index("tipo")
            await self._get_db().durezza_documents.create_index("fase_asociada")

            await self._get_db().durezza_audit_logs.create_index("proyecto_id")
            await self._get_db().durezza_audit_logs.create_index("accion")
            await self._get_db().durezza_audit_logs.create_index("entidad_tipo")
            await self._get_db().durezza_audit_logs.create_index("created_at")
            await self._get_db().durezza_audit_logs.create_index("usuario")

            await self._get_db().proveedores.create_index("empresa_id")
            await self._get_db().proveedores.create_index([("empresa_id", 1), ("rfc", 1)], unique=True)
            await self._get_db().proveedores.create_index([("empresa_id", 1), ("estatus", 1)])
            await self._get_db().proveedores.create_index([("empresa_id", 1), ("riesgo.nivel_riesgo", 1)])
            await self._get_db().proveedores.create_index([("empresa_id", 1), ("tipo_proveedor", 1)])

            logger.info("Revisar.IA indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating Revisar.IA indexes: {e}")

    async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        supplier = Supplier(**supplier_data)
        data = supplier.model_dump()
        if self.demo_mode:
            DEMO_SUPPLIERS.append(data)
            return data
        await self._get_db().durezza_suppliers.insert_one(data.copy())
        return data

    async def get_supplier(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((s for s in DEMO_SUPPLIERS if s['id'] == supplier_id), None)
        return clean_mongo_doc(await self._get_db().durezza_suppliers.find_one({'id': supplier_id}))

    async def get_supplier_by_rfc(self, rfc: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((s for s in DEMO_SUPPLIERS if s['rfc'] == rfc), None)
        return clean_mongo_doc(await self._get_db().durezza_suppliers.find_one({'rfc': rfc}))

    async def get_suppliers(self, activo: Optional[bool] = None) -> List[Dict[str, Any]]:
        if self.demo_mode:
            if activo is not None:
                return [s for s in DEMO_SUPPLIERS if s['activo'] == activo]
            return DEMO_SUPPLIERS
        query = {}
        if activo is not None:
            query['activo'] = activo
        cursor = self._get_db().durezza_suppliers.find(query).sort('nombre_razon_social', 1)
        return clean_mongo_docs(await cursor.to_list(length=500))

    async def update_supplier(self, supplier_id: str, update_data: Dict[str, Any]) -> bool:
        update_data['updated_at'] = datetime.utcnow()
        if self.demo_mode:
            for i, s in enumerate(DEMO_SUPPLIERS):
                if s['id'] == supplier_id:
                    DEMO_SUPPLIERS[i].update(update_data)
                    return True
            return False
        result = await self._get_db().durezza_suppliers.update_one({'id': supplier_id}, {'$set': update_data})
        return result.modified_count > 0

    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        project = Project(**project_data)
        data = project.model_dump()
        if self.demo_mode:
            DEMO_PROJECTS.append(data)
            return data
        await self._get_db().durezza_projects.insert_one(data.copy())
        return data

    async def get_project(
        self, 
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            for p in DEMO_PROJECTS:
                if p['id'] == project_id:
                    if empresa_id and p.get('empresa_id') != empresa_id:
                        return None
                    return p
            return None
        query = {'id': project_id}
        if empresa_id:
            query['empresa_id'] = empresa_id
        return clean_mongo_doc(await self._get_db().durezza_projects.find_one(query))

    async def get_projects(
        self,
        empresa_id: Optional[str] = None,
        estado: Optional[str] = None,
        fase: Optional[str] = None,
        tipologia: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        if self.demo_mode:
            result = DEMO_PROJECTS
            if empresa_id:
                result = [p for p in result if p.get('empresa_id') == empresa_id]
            if estado:
                result = [p for p in result if p['estado_global'] == estado]
            if fase:
                result = [p for p in result if p['fase_actual'] == fase]
            if tipologia:
                result = [p for p in result if p['tipologia'] == tipologia]
            return result[:limit]
        query = {}
        if empresa_id:
            query['empresa_id'] = empresa_id
        if estado:
            query['estado_global'] = estado
        if fase:
            query['fase_actual'] = fase
        if tipologia:
            query['tipologia'] = tipologia
        cursor = self._get_db().durezza_projects.find(query).sort('created_at', -1).limit(limit)
        return clean_mongo_docs(await cursor.to_list(length=limit))

    async def update_project(self, project_id: str, update_data: Dict[str, Any]) -> bool:
        update_data['updated_at'] = datetime.utcnow()
        if self.demo_mode:
            for i, p in enumerate(DEMO_PROJECTS):
                if p['id'] == project_id:
                    DEMO_PROJECTS[i].update(update_data)
                    return True
            return False
        result = await self._get_db().durezza_projects.update_one({'id': project_id}, {'$set': update_data})
        return result.modified_count > 0

    async def create_project_phase(self, phase_data: Dict[str, Any]) -> Dict[str, Any]:
        phase = ProjectPhase(**phase_data)
        data = phase.model_dump()
        if self.demo_mode:
            DEMO_PROJECT_PHASES.append(data)
            return data
        await self._get_db().durezza_project_phases.insert_one(data.copy())
        return data

    async def get_project_phases(self, proyecto_id: str) -> List[Dict[str, Any]]:
        if self.demo_mode:
            return [p for p in DEMO_PROJECT_PHASES if p['proyecto_id'] == proyecto_id]
        cursor = self._get_db().durezza_project_phases.find({'proyecto_id': proyecto_id}).sort('fase', 1)
        return clean_mongo_docs(await cursor.to_list(length=20))

    async def get_project_phase(self, proyecto_id: str, fase: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((p for p in DEMO_PROJECT_PHASES if p['proyecto_id'] == proyecto_id and p['fase'] == fase), None)
        return clean_mongo_doc(await self._get_db().durezza_project_phases.find_one({'proyecto_id': proyecto_id, 'fase': fase}))

    async def update_project_phase(self, phase_id: str, update_data: Dict[str, Any]) -> bool:
        update_data['updated_at'] = datetime.utcnow()
        if self.demo_mode:
            for i, p in enumerate(DEMO_PROJECT_PHASES):
                if p['id'] == phase_id:
                    DEMO_PROJECT_PHASES[i].update(update_data)
                    return True
            return False
        result = await self._get_db().durezza_project_phases.update_one({'id': phase_id}, {'$set': update_data})
        return result.modified_count > 0

    async def create_deliberation(self, deliberation_data: Dict[str, Any]) -> Dict[str, Any]:
        deliberation = AgentDeliberation(**deliberation_data)
        data = deliberation.model_dump()
        if self.demo_mode:
            DEMO_DELIBERATIONS.append(data)
            return data
        await self._get_db().durezza_deliberations.insert_one(data.copy())
        return data

    async def get_deliberations(self, proyecto_id: str, fase: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.demo_mode:
            result = [d for d in DEMO_DELIBERATIONS if d['proyecto_id'] == proyecto_id]
            if fase:
                result = [d for d in result if d['fase'] == fase]
            return result
        query = {'proyecto_id': proyecto_id}
        if fase:
            query['fase'] = fase
        cursor = self._get_db().durezza_deliberations.find(query).sort('created_at', -1)
        return clean_mongo_docs(await cursor.to_list(length=100))

    async def get_latest_deliberation(self, proyecto_id: str, agente: str, fase: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            matching = [d for d in DEMO_DELIBERATIONS 
                       if d['proyecto_id'] == proyecto_id and d['agente'] == agente and d['fase'] == fase]
            return max(matching, key=lambda x: x['version'], default=None)
        cursor = self._get_db().durezza_deliberations.find({
            'proyecto_id': proyecto_id,
            'agente': agente,
            'fase': fase
        }).sort('version', -1).limit(1)
        results = await cursor.to_list(length=1)
        return clean_mongo_doc(results[0]) if results else None

    async def create_defense_file(self, defense_file_data: Dict[str, Any]) -> Dict[str, Any]:
        defense_file = DefenseFile(**defense_file_data)
        data = defense_file.model_dump()
        if self.demo_mode:
            DEMO_DEFENSE_FILES.append(data)
            return data
        await self._get_db().durezza_defense_files.insert_one(data.copy())
        return data

    async def get_defense_file(self, proyecto_id: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((d for d in DEMO_DEFENSE_FILES if d['proyecto_id'] == proyecto_id), None)
        return clean_mongo_doc(await self._get_db().durezza_defense_files.find_one({'proyecto_id': proyecto_id}))

    async def update_defense_file(self, defense_file_id: str, update_data: Dict[str, Any]) -> bool:
        update_data['updated_at'] = datetime.utcnow()
        if self.demo_mode:
            for i, d in enumerate(DEMO_DEFENSE_FILES):
                if d['id'] == defense_file_id:
                    DEMO_DEFENSE_FILES[i].update(update_data)
                    return True
            return False
        result = await self._get_db().durezza_defense_files.update_one({'id': defense_file_id}, {'$set': update_data})
        return result.modified_count > 0

    async def create_checklist_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        template = ChecklistTemplate(**template_data)
        data = template.model_dump()
        if self.demo_mode:
            existing_idx = next((i for i, t in enumerate(DEMO_CHECKLIST_TEMPLATES) 
                                if t['tipologia'] == data['tipologia'] and t['fase'] == data['fase']), None)
            if existing_idx is not None:
                DEMO_CHECKLIST_TEMPLATES[existing_idx] = data
            else:
                DEMO_CHECKLIST_TEMPLATES.append(data)
            return data
        await self._get_db().durezza_checklist_templates.replace_one(
            {'tipologia': data['tipologia'], 'fase': data['fase']},
            data,
            upsert=True
        )
        return data

    async def get_checklist_template(self, tipologia: str, fase: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((t for t in DEMO_CHECKLIST_TEMPLATES 
                        if t['tipologia'] == tipologia and t['fase'] == fase), None)
        return clean_mongo_doc(await self._get_db().durezza_checklist_templates.find_one({'tipologia': tipologia, 'fase': fase}))

    async def get_checklist_templates(self, tipologia: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.demo_mode:
            if tipologia:
                return [t for t in DEMO_CHECKLIST_TEMPLATES if t['tipologia'] == tipologia]
            return DEMO_CHECKLIST_TEMPLATES
        query = {}
        if tipologia:
            query['tipologia'] = tipologia
        cursor = self._get_db().durezza_checklist_templates.find(query).sort('fase', 1)
        return clean_mongo_docs(await cursor.to_list(length=100))

    async def create_agent_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        config = AgentConfig(**config_data)
        data = config.model_dump()
        if self.demo_mode:
            existing_idx = next((i for i, c in enumerate(DEMO_AGENT_CONFIGS) 
                                if c['agente'] == data['agente']), None)
            if existing_idx is not None:
                DEMO_AGENT_CONFIGS[existing_idx] = data
            else:
                DEMO_AGENT_CONFIGS.append(data)
            return data
        await self._get_db().durezza_agent_configs.replace_one(
            {'agente': data['agente']},
            data,
            upsert=True
        )
        return data

    async def get_agent_config(self, agente: str) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return next((c for c in DEMO_AGENT_CONFIGS if c['agente'] == agente), None)
        return clean_mongo_doc(await self._get_db().durezza_agent_configs.find_one({'agente': agente}))

    async def get_agent_configs(self, activo: bool = True) -> List[Dict[str, Any]]:
        if self.demo_mode:
            return [c for c in DEMO_AGENT_CONFIGS if c['activo'] == activo]
        cursor = self._get_db().durezza_agent_configs.find({'activo': activo})
        return clean_mongo_docs(await cursor.to_list(length=50))

    async def create_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        document = Document(**document_data)
        data = document.model_dump()
        if self.demo_mode:
            DEMO_DOCUMENTS.append(data)
            return data
        await self._get_db().durezza_documents.insert_one(data.copy())
        return data

    async def get_documents(self, proyecto_id: str, tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.demo_mode:
            result = [d for d in DEMO_DOCUMENTS if d['proyecto_id'] == proyecto_id]
            if tipo:
                result = [d for d in result if d['tipo'] == tipo]
            return result
        query = {'proyecto_id': proyecto_id}
        if tipo:
            query['tipo'] = tipo
        cursor = self._get_db().durezza_documents.find(query).sort('created_at', -1)
        return clean_mongo_docs(await cursor.to_list(length=200))

    async def create_audit_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        log = AuditLog(**log_data)
        data = log.model_dump()
        if self.demo_mode:
            DEMO_AUDIT_LOGS.append(data)
            return data
        await self._get_db().durezza_audit_logs.insert_one(data.copy())
        return data

    async def get_audit_logs(
        self,
        proyecto_id: Optional[str] = None,
        accion: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        if self.demo_mode:
            result = DEMO_AUDIT_LOGS
            if proyecto_id:
                result = [l for l in result if l.get('proyecto_id') == proyecto_id]
            if accion:
                result = [l for l in result if l['accion'] == accion]
            return result[:limit]
        query = {}
        if proyecto_id:
            query['proyecto_id'] = proyecto_id
        if accion:
            query['accion'] = accion
        cursor = self._get_db().durezza_audit_logs.find(query).sort('created_at', -1).limit(limit)
        return clean_mongo_docs(await cursor.to_list(length=limit))


    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas para el dashboard"""
        if self.demo_mode:
            return {
                "total_proyectos": len(DEMO_PROJECTS),
                "proyectos_activos": len([p for p in DEMO_PROJECTS if p.get("estado_global") == "EN_PROCESO"]),
                "total_proveedores": len(DEMO_SUPPLIERS),
                "proveedores_alertas": len([s for s in DEMO_SUPPLIERS if s.get("alerta_efos")]),
                "expedientes_generados": len(DEMO_DEFENSE_FILES),
                "deliberaciones_pendientes": len([d for d in DEMO_DELIBERATIONS if d.get("estado") != "COMPLETADA"]),
                "demo_mode": True
            }
        
        try:
            proyectos = await self._get_db().durezza_projects.count_documents({})
            proyectos_activos = await self._get_db().durezza_projects.count_documents({"estado_global": "EN_PROCESO"})
            proveedores = await self._get_db().durezza_suppliers.count_documents({})
            proveedores_alertas = await self._get_db().durezza_suppliers.count_documents({"alerta_efos": True})
            expedientes = await self._get_db().durezza_defense_files.count_documents({})
            deliberaciones_pendientes = await self._get_db().durezza_deliberations.count_documents({"estado": {"$ne": "COMPLETADA"}})
            
            return {
                "total_proyectos": proyectos,
                "proyectos_activos": proyectos_activos,
                "total_proveedores": proveedores,
                "proveedores_alertas": proveedores_alertas,
                "expedientes_generados": expedientes,
                "deliberaciones_pendientes": deliberaciones_pendientes,
                "demo_mode": False
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {"error": str(e), "demo_mode": True}


durezza_db = DurezzaDatabaseService()
