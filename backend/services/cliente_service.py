"""
Servicio de Clientes con soporte multi-tenant.
Los clientes pertenecen a una empresa (tenant).
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

from services.database import db, DEMO_MODE, serialize_mongo_doc, serialize_mongo_docs

DEMO_CLIENTES: List[Dict[str, Any]] = []


class ClienteService:
    def __init__(self):
        self.collection_name = "clientes"
    
    def _get_collection(self):
        if DEMO_MODE or db is None:
            return None
        return db[self.collection_name]
    
    async def create_cliente(
        self,
        cliente_data: Dict[str, Any],
        empresa_id: str,
        creado_por: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crear un nuevo cliente asociado a una empresa (tenant).
        """
        if not empresa_id:
            raise ValueError("empresa_id es requerido para crear clientes")
        
        cliente_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        cliente = {
            "id": cliente_id,
            "empresa_id": empresa_id,
            **cliente_data,
            "fecha_alta": now,
            "fecha_actualizacion": now,
            "creado_por": creado_por,
            "status": cliente_data.get("status", "activo")
        }
        
        collection = self._get_collection()
        if collection is None:
            cliente["_demo"] = True
            DEMO_CLIENTES.append(cliente)
            logger.info(f"[DEMO] Created cliente: {cliente_id}")
            return cliente
        
        await collection.insert_one(cliente)
        logger.info(f"Created cliente {cliente_id} for empresa {empresa_id}")
        return serialize_mongo_doc(cliente)
    
    async def get_cliente(
        self,
        cliente_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener un cliente por ID.
        Si empresa_id se proporciona, valida que el cliente pertenezca a esa empresa.
        """
        collection = self._get_collection()
        
        if collection is None:
            for c in DEMO_CLIENTES:
                if c["id"] == cliente_id:
                    if empresa_id and c.get("empresa_id") != empresa_id:
                        return None
                    return c
            return None
        
        query = {"id": cliente_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        cliente = await collection.find_one(query)
        return serialize_mongo_doc(cliente)
    
    async def list_clientes(
        self,
        empresa_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Listar clientes con filtros opcionales.
        Si empresa_id se proporciona, solo retorna clientes de esa empresa.
        Si empresa_id es None (admin), retorna todos los clientes.
        """
        collection = self._get_collection()
        
        if collection is None:
            results = DEMO_CLIENTES
            if empresa_id:
                results = [c for c in results if c.get("empresa_id") == empresa_id]
            if status:
                results = [c for c in results if c.get("status") == status]
            if search:
                search_lower = search.lower()
                results = [c for c in results if 
                          search_lower in c.get("razon_social", "").lower() or
                          search_lower in (c.get("rfc") or "").lower() or
                          search_lower in (c.get("nombre_comercial") or "").lower()]
            return results[skip:skip+limit]
        
        query = {}
        if empresa_id:
            query["empresa_id"] = empresa_id
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"razon_social": {"$regex": search, "$options": "i"}},
                {"rfc": {"$regex": search, "$options": "i"}},
                {"nombre_comercial": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = collection.find(query).skip(skip).limit(limit).sort("fecha_alta", -1)
        clientes = await cursor.to_list(length=limit)
        return serialize_mongo_docs(clientes)
    
    async def update_cliente(
        self,
        cliente_id: str,
        update_data: Dict[str, Any],
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualizar un cliente.
        Si empresa_id se proporciona, valida que el cliente pertenezca a esa empresa.
        """
        collection = self._get_collection()
        update_data["fecha_actualizacion"] = datetime.now(timezone.utc)
        
        if collection is None:
            for i, c in enumerate(DEMO_CLIENTES):
                if c["id"] == cliente_id:
                    if empresa_id and c.get("empresa_id") != empresa_id:
                        return None
                    DEMO_CLIENTES[i].update(update_data)
                    return DEMO_CLIENTES[i]
            return None
        
        query = {"id": cliente_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        result = await collection.find_one_and_update(
            query,
            {"$set": update_data},
            return_document=True
        )
        return serialize_mongo_doc(result)
    
    async def delete_cliente(
        self,
        cliente_id: str,
        empresa_id: Optional[str] = None
    ) -> bool:
        """
        Eliminar un cliente (soft delete cambiando status a inactivo).
        """
        result = await self.update_cliente(
            cliente_id,
            {"status": "inactivo"},
            empresa_id
        )
        return result is not None
    
    async def count_clientes(
        self,
        empresa_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """
        Contar clientes con filtros opcionales.
        """
        collection = self._get_collection()
        
        if collection is None:
            results = DEMO_CLIENTES
            if empresa_id:
                results = [c for c in results if c.get("empresa_id") == empresa_id]
            if status:
                results = [c for c in results if c.get("status") == status]
            return len(results)
        
        query = {}
        if empresa_id:
            query["empresa_id"] = empresa_id
        if status:
            query["status"] = status
        
        return await collection.count_documents(query)
    
    async def get_clientes_by_empresa(
        self,
        empresa_id: str,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtener todos los clientes de una empresa específica.
        """
        status = None if include_inactive else "activo"
        return await self.list_clientes(
            empresa_id=empresa_id,
            status=status,
            limit=1000
        )


cliente_service = ClienteService()
