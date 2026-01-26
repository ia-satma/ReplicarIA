import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from models.proveedor import (
    Proveedor, RiesgoProveedor, FlagsRiesgo, DocumentosClave,
    NivelRiesgo, EstatusProveedor
)
from services.durezza_database import get_db

logger = logging.getLogger(__name__)

SERVICE_UNAVAILABLE_ERROR = "Servicio de proveedores no disponible - base de datos no conectada"


class ProveedorService:
    def __init__(self):
        self.collection_name = "proveedores"

    def _get_collection(self) -> Tuple[Any, bool]:
        db, demo_mode = get_db()
        if db is None or demo_mode:
            return None, True
        return db[self.collection_name], False

    def is_available(self) -> bool:
        collection, is_demo = self._get_collection()
        return collection is not None and not is_demo

    def create_proveedor(self, proveedor_data: Dict[str, Any], empresa_id: str, usuario_id: str) -> Dict[str, Any]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return {"success": False, "error": SERVICE_UNAVAILABLE_ERROR, "service_unavailable": True}
        
        try:
            proveedor = Proveedor.from_dict(proveedor_data)
            proveedor.empresa_id = empresa_id
            proveedor.usuario_alta = usuario_id
            proveedor.fecha_alta = datetime.utcnow().isoformat()
            proveedor.fecha_ultima_actualizacion = datetime.utcnow().isoformat()
            proveedor.usuario_ultima_actualizacion = usuario_id

            if not proveedor.riesgo:
                proveedor.riesgo = RiesgoProveedor()
            
            self._calcular_riesgo(proveedor)

            result = collection.insert_one(proveedor.to_dict())

            logger.info(f"Proveedor creado: {proveedor.id} para empresa {empresa_id}")
            return {
                "success": True,
                "proveedor_id": proveedor.id,
                "proveedor": proveedor.to_dict()
            }
        except Exception as e:
            logger.error(f"Error creando proveedor: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_proveedor(self, proveedor_id: str, empresa_id: str) -> Optional[Dict[str, Any]]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return None
        
        try:
            doc = collection.find_one({"id": proveedor_id, "empresa_id": empresa_id})
            if doc:
                doc.pop('_id', None)
                return doc
            return None
        except Exception as e:
            logger.error(f"Error obteniendo proveedor: {str(e)}")
            return None

    async def get_proveedores_by_empresa_async(self, empresa_id: str, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Async version that properly handles Motor cursors."""
        collection, is_demo = self._get_collection()
        if collection is None:
            return []
        
        try:
            query = {"empresa_id": empresa_id}
            
            if filtros:
                if filtros.get("estatus"):
                    query["estatus"] = filtros["estatus"]
                if filtros.get("tipo_proveedor"):
                    query["tipo_proveedor"] = filtros["tipo_proveedor"]
                if filtros.get("nivel_riesgo"):
                    query["riesgo.nivel_riesgo"] = filtros["nivel_riesgo"]
                if filtros.get("busqueda"):
                    query["$or"] = [
                        {"razon_social": {"$regex": filtros["busqueda"], "$options": "i"}},
                        {"nombre_comercial": {"$regex": filtros["busqueda"], "$options": "i"}},
                        {"rfc": {"$regex": filtros["busqueda"], "$options": "i"}}
                    ]

            cursor = collection.find(query).sort("fecha_alta", -1)
            docs = await cursor.to_list(length=1000)
            for doc in docs:
                doc.pop('_id', None)
            return docs
        except Exception as e:
            logger.error(f"Error listando proveedores: {str(e)}")
            return []

    def get_proveedores_by_empresa(self, empresa_id: str, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Sync wrapper - deprecated, use get_proveedores_by_empresa_async instead."""
        return []

    def update_proveedor(self, proveedor_id: str, empresa_id: str, updates: Dict[str, Any], usuario_id: str) -> Dict[str, Any]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return {"success": False, "error": SERVICE_UNAVAILABLE_ERROR, "service_unavailable": True}
        
        try:
            existing = collection.find_one({"id": proveedor_id, "empresa_id": empresa_id})
            
            if not existing:
                return {"success": False, "error": "Proveedor no encontrado"}
            
            existing.pop('_id', None)
            proveedor = Proveedor.from_dict(existing)
            
            campos_modificados = []
            for key, value in updates.items():
                if hasattr(proveedor, key):
                    old_value = getattr(proveedor, key)
                    if old_value != value:
                        setattr(proveedor, key, value)
                        campos_modificados.append(key)
            
            proveedor.fecha_ultima_actualizacion = datetime.utcnow().isoformat()
            proveedor.usuario_ultima_actualizacion = usuario_id
            proveedor.version_registro += 1
            
            if campos_modificados:
                proveedor.historial_cambios.append({
                    "fecha": datetime.utcnow().isoformat(),
                    "usuario": usuario_id,
                    "campos_modificados": campos_modificados
                })
            
            self._calcular_riesgo(proveedor)
            
            collection.replace_one(
                {"id": proveedor_id, "empresa_id": empresa_id},
                proveedor.to_dict()
            )
            
            logger.info(f"Proveedor actualizado: {proveedor_id}")
            return {
                "success": True,
                "proveedor": proveedor.to_dict()
            }
        except Exception as e:
            logger.error(f"Error actualizando proveedor: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_proveedor(self, proveedor_id: str, empresa_id: str) -> Dict[str, Any]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return {"success": False, "error": SERVICE_UNAVAILABLE_ERROR, "service_unavailable": True}
        
        try:
            result = collection.delete_one({"id": proveedor_id, "empresa_id": empresa_id})
            
            if result.deleted_count > 0:
                logger.info(f"Proveedor eliminado: {proveedor_id}")
                return {"success": True, "message": "Proveedor eliminado"}
            else:
                return {"success": False, "error": "Proveedor no encontrado"}
        except Exception as e:
            logger.error(f"Error eliminando proveedor: {str(e)}")
            return {"success": False, "error": str(e)}

    def search_proveedores(self, empresa_id: str, termino: str) -> List[Dict[str, Any]]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return []
        
        try:
            query = {
                "empresa_id": empresa_id,
                "$or": [
                    {"razon_social": {"$regex": termino, "$options": "i"}},
                    {"nombre_comercial": {"$regex": termino, "$options": "i"}},
                    {"rfc": {"$regex": termino, "$options": "i"}}
                ]
            }
            cursor = collection.find(query).limit(20)
            results = []
            for doc in cursor:
                doc.pop('_id', None)
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Error buscando proveedores: {str(e)}")
            return []

    def verificar_rfc_existente(self, rfc: str, empresa_id: str, proveedor_id: Optional[str] = None) -> bool:
        collection, is_demo = self._get_collection()
        if collection is None:
            return False
        
        try:
            query = {"rfc": rfc, "empresa_id": empresa_id}
            if proveedor_id:
                query["id"] = {"$ne": proveedor_id}
            return collection.count_documents(query) > 0
        except Exception as e:
            logger.error(f"Error verificando RFC: {str(e)}")
            return False

    def _calcular_riesgo(self, proveedor: Proveedor) -> None:
        if not proveedor.riesgo:
            proveedor.riesgo = RiesgoProveedor()
        
        flags = proveedor.riesgo.flags
        score_fiscal = 0.0
        score_legal = 0.0
        score_operativo = 0.0

        if proveedor.fecha_constitucion:
            try:
                fecha_const = datetime.fromisoformat(proveedor.fecha_constitucion.replace('Z', '+00:00'))
                meses_antiguedad = (datetime.utcnow() - fecha_const.replace(tzinfo=None)).days / 30
                if meses_antiguedad < 6:
                    flags.proveedor_muy_reciente = True
                    flags.proveedor_reciente = True
                    score_fiscal += 25
                elif meses_antiguedad < 12:
                    flags.proveedor_reciente = True
                    score_fiscal += 15
            except:
                pass

        if not proveedor.documentos or not proveedor.documentos.opinion_cumplimiento or not proveedor.documentos.opinion_cumplimiento.archivo_url:
            flags.sin_opinion_cumplimiento = True
            score_fiscal += 20

        if proveedor.documentos and proveedor.documentos.opinion_cumplimiento:
            if proveedor.documentos.opinion_cumplimiento.tipo_opinion == "negativa":
                flags.opinion_negativa = True
                score_fiscal += 40

        if proveedor.requiere_repse:
            if not proveedor.documentos or not proveedor.documentos.repse or not proveedor.documentos.repse.archivo_url:
                flags.sin_repse_si_aplica = True
                score_legal += 30
            elif proveedor.documentos.repse.fecha_vigencia:
                try:
                    fecha_vig = datetime.fromisoformat(proveedor.documentos.repse.fecha_vigencia.replace('Z', '+00:00'))
                    if fecha_vig.replace(tzinfo=None) < datetime.utcnow():
                        flags.repse_vencido = True
                        score_legal += 25
                except:
                    pass

        if proveedor.domicilio_fiscal and proveedor.domicilio_fiscal.es_zona_alto_riesgo:
            flags.domicilio_alto_riesgo = True
            score_fiscal += 15

        if not proveedor.sitio_web and not proveedor.redes_sociales:
            flags.sin_presencia_digital = True
            score_operativo += 10

        if proveedor.contacto_principal and proveedor.sitio_web:
            email = proveedor.contacto_principal.email or ""
            sitio = proveedor.sitio_web or ""
            if "@" in email and sitio:
                email_domain = email.split("@")[1].lower() if "@" in email else ""
                sitio_domain = sitio.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()
                if email_domain and sitio_domain and email_domain != sitio_domain:
                    flags.email_no_coincide_con_dominio = True
                    score_operativo += 5

        proveedor.riesgo.score_fiscal = min(100, score_fiscal)
        proveedor.riesgo.score_legal = min(100, score_legal)
        proveedor.riesgo.score_operativo = min(100, score_operativo)

        proveedor.riesgo.score_general = (
            proveedor.riesgo.score_fiscal * 0.5 +
            proveedor.riesgo.score_legal * 0.3 +
            proveedor.riesgo.score_operativo * 0.2
        )

        if proveedor.riesgo.score_general >= 70:
            proveedor.riesgo.nivel_riesgo = NivelRiesgo.CRITICO.value
        elif proveedor.riesgo.score_general >= 50:
            proveedor.riesgo.nivel_riesgo = NivelRiesgo.ALTO.value
        elif proveedor.riesgo.score_general >= 25:
            proveedor.riesgo.nivel_riesgo = NivelRiesgo.MEDIO.value
        else:
            proveedor.riesgo.nivel_riesgo = NivelRiesgo.BAJO.value

        materialidad = 100.0
        if not proveedor.documentos or not proveedor.documentos.constancia_situacion_fiscal:
            materialidad -= 20
        if not proveedor.documentos or not proveedor.documentos.acta_constitutiva:
            materialidad -= 15
        if not proveedor.documentos or not proveedor.documentos.opinion_cumplimiento:
            materialidad -= 25
        if proveedor.requiere_repse and (not proveedor.documentos or not proveedor.documentos.repse):
            materialidad -= 20
        if not proveedor.sitio_web:
            materialidad -= 10
        if not proveedor.contacto_principal:
            materialidad -= 10

        proveedor.riesgo.score_materialidad_potencial = max(0, materialidad)
        proveedor.riesgo.fecha_ultima_evaluacion = datetime.utcnow().isoformat()

    def recalcular_riesgo(self, proveedor_id: str, empresa_id: str) -> Dict[str, Any]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return {"success": False, "error": SERVICE_UNAVAILABLE_ERROR, "service_unavailable": True}
        
        try:
            proveedor_data = self.get_proveedor(proveedor_id, empresa_id)
            if not proveedor_data:
                return {"success": False, "error": "Proveedor no encontrado"}
            
            proveedor = Proveedor.from_dict(proveedor_data)
            self._calcular_riesgo(proveedor)
            
            collection.replace_one(
                {"id": proveedor_id, "empresa_id": empresa_id},
                proveedor.to_dict()
            )
            
            return {
                "success": True,
                "riesgo": proveedor.riesgo.to_dict()
            }
        except Exception as e:
            logger.error(f"Error recalculando riesgo: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_estadisticas(self, empresa_id: str) -> Dict[str, Any]:
        collection, is_demo = self._get_collection()
        if collection is None:
            return {"error": SERVICE_UNAVAILABLE_ERROR, "service_unavailable": True}
        
        try:
            total = collection.count_documents({"empresa_id": empresa_id})
            activos = collection.count_documents({"empresa_id": empresa_id, "estatus": "activo"})
            pendientes = collection.count_documents({"empresa_id": empresa_id, "estatus": "pendiente_revision"})
            bloqueados = collection.count_documents({"empresa_id": empresa_id, "estatus": "bloqueado"})
            
            riesgo_bajo = collection.count_documents({"empresa_id": empresa_id, "riesgo.nivel_riesgo": "bajo"})
            riesgo_medio = collection.count_documents({"empresa_id": empresa_id, "riesgo.nivel_riesgo": "medio"})
            riesgo_alto = collection.count_documents({"empresa_id": empresa_id, "riesgo.nivel_riesgo": "alto"})
            riesgo_critico = collection.count_documents({"empresa_id": empresa_id, "riesgo.nivel_riesgo": "critico"})

            return {
                "total": total,
                "por_estatus": {
                    "activos": activos,
                    "pendientes": pendientes,
                    "bloqueados": bloqueados
                },
                "por_riesgo": {
                    "bajo": riesgo_bajo,
                    "medio": riesgo_medio,
                    "alto": riesgo_alto,
                    "critico": riesgo_critico
                }
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {"error": str(e)}

    def create_indexes(self) -> None:
        collection, is_demo = self._get_collection()
        if collection is None:
            logger.warning("No se pueden crear índices de proveedores - base de datos no disponible")
            return
        
        try:
            collection.create_index([("empresa_id", 1)])
            collection.create_index([("empresa_id", 1), ("rfc", 1)], unique=True)
            collection.create_index([("empresa_id", 1), ("estatus", 1)])
            collection.create_index([("empresa_id", 1), ("riesgo.nivel_riesgo", 1)])
            collection.create_index([("empresa_id", 1), ("tipo_proveedor", 1)])
            collection.create_index([("empresa_id", 1), ("razon_social", "text"), ("nombre_comercial", "text")])
            logger.info("Índices de proveedores creados correctamente")
        except Exception as e:
            logger.warning(f"Error creando índices de proveedores: {str(e)}")
