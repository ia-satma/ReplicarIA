"""
Repository para operaciones CRUD de Empresa/Tenant.
Soporta MongoDB y modo demo (in-memory).
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.empresa import Empresa, EmpresaCreate, EmpresaUpdate

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', '')
DEMO_MODE = not MONGO_URL

db = None
if not DEMO_MODE:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[os.environ.get('DB_NAME', 'revisar_agent_network')]
        logger.info("EmpresaRepository: Connected to MongoDB")
    except Exception as e:
        logger.warning(f"EmpresaRepository: MongoDB connection failed: {e}, using demo mode")
        DEMO_MODE = True


class EmpresaRepository:
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self._demo_empresas: List[Dict[str, Any]] = []
        
    async def create(self, empresa: Empresa) -> Empresa:
        empresa_dict = empresa.model_dump()
        empresa_dict['fecha_alta'] = empresa_dict['fecha_alta'].isoformat() if isinstance(empresa_dict['fecha_alta'], datetime) else empresa_dict['fecha_alta']
        empresa_dict['fecha_actualizacion'] = empresa_dict['fecha_actualizacion'].isoformat() if isinstance(empresa_dict['fecha_actualizacion'], datetime) else empresa_dict['fecha_actualizacion']
        
        if self.demo_mode:
            self._demo_empresas.append(empresa_dict)
            logger.info(f"Demo: Created empresa {empresa.id}")
            return empresa
        
        await db.empresas.insert_one(empresa_dict)
        logger.info(f"MongoDB: Created empresa {empresa.id}")
        return empresa
    
    async def get_by_id(self, empresa_id: str) -> Optional[Empresa]:
        if self.demo_mode:
            for emp in self._demo_empresas:
                if emp['id'] == empresa_id:
                    return Empresa(**emp)
            return None
        
        doc = await db.empresas.find_one({'id': empresa_id})
        if doc:
            doc.pop('_id', None)
            return Empresa(**doc)
        return None
    
    async def get_by_rfc(self, rfc: str) -> Optional[Empresa]:
        if self.demo_mode:
            for emp in self._demo_empresas:
                if emp['rfc'] == rfc:
                    return Empresa(**emp)
            return None
        
        doc = await db.empresas.find_one({'rfc': rfc})
        if doc:
            doc.pop('_id', None)
            return Empresa(**doc)
        return None
    
    async def get_all(self, only_active: bool = True) -> List[Empresa]:
        if self.demo_mode:
            empresas = self._demo_empresas
            if only_active:
                empresas = [e for e in empresas if e.get('activa', True)]
            return [Empresa(**e) for e in empresas]
        
        query = {'activa': True} if only_active else {}
        cursor = db.empresas.find(query)
        docs = await cursor.to_list(length=1000)
        
        result = []
        for doc in docs:
            doc.pop('_id', None)
            result.append(Empresa(**doc))
        return result
    
    async def update(self, empresa_id: str, update_data: Dict[str, Any]) -> Optional[Empresa]:
        update_data['fecha_actualizacion'] = datetime.utcnow().isoformat()
        
        if self.demo_mode:
            for i, emp in enumerate(self._demo_empresas):
                if emp['id'] == empresa_id:
                    self._demo_empresas[i].update(update_data)
                    logger.info(f"Demo: Updated empresa {empresa_id}")
                    return Empresa(**self._demo_empresas[i])
            return None
        
        result = await db.empresas.update_one(
            {'id': empresa_id},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"MongoDB: Updated empresa {empresa_id}")
            return await self.get_by_id(empresa_id)
        return None
    
    async def update_tipologias(self, empresa_id: str, tipologias: List[Dict[str, Any]]) -> Optional[Empresa]:
        update_data = {
            'tipologias_configuradas': tipologias,
            'fecha_actualizacion': datetime.utcnow().isoformat()
        }
        return await self.update(empresa_id, update_data)
    
    async def update_vision_mision(self, empresa_id: str, vision: Optional[str], mision: Optional[str]) -> Optional[Empresa]:
        update_data = {'fecha_actualizacion': datetime.utcnow().isoformat()}
        if vision is not None:
            update_data['vision'] = vision
        if mision is not None:
            update_data['mision'] = mision
        return await self.update(empresa_id, update_data)
    
    async def update_pilares(self, empresa_id: str, pilares: List[Dict[str, Any]]) -> Optional[Empresa]:
        update_data = {
            'pilares_estrategicos': pilares,
            'fecha_actualizacion': datetime.utcnow().isoformat()
        }
        return await self.update(empresa_id, update_data)
    
    async def update_okrs(self, empresa_id: str, okrs: List[Dict[str, Any]]) -> Optional[Empresa]:
        update_data = {
            'okrs': okrs,
            'fecha_actualizacion': datetime.utcnow().isoformat()
        }
        return await self.update(empresa_id, update_data)
    
    async def delete(self, empresa_id: str) -> bool:
        if self.demo_mode:
            for i, emp in enumerate(self._demo_empresas):
                if emp['id'] == empresa_id:
                    self._demo_empresas.pop(i)
                    logger.info(f"Demo: Deleted empresa {empresa_id}")
                    return True
            return False
        
        result = await db.empresas.delete_one({'id': empresa_id})
        if result.deleted_count > 0:
            logger.info(f"MongoDB: Deleted empresa {empresa_id}")
            return True
        return False
    
    async def soft_delete(self, empresa_id: str) -> Optional[Empresa]:
        return await self.update(empresa_id, {'activa': False})


empresa_repository = EmpresaRepository()
