"""
SERVICIO DE VERSIONAMIENTO DE EXPEDIENTES
Maneja la creación de versiones, bitácora y comparaciones
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json
import difflib

from models.versioning import (
    ProyectoVersionado,
    VersionExpediente,
    EntradaBitacora,
    TipoCambio,
    Severidad,
    generar_folio_base,
    generar_hash_contenido,
    crear_entrada_bitacora
)

try:
    from services.defense_file.defense_file_generator import (
        defense_file_generator,
        DefenseFileConfig
    )
    HAS_DEFENSE_GENERATOR = True
except ImportError:
    HAS_DEFENSE_GENERATOR = False


class VersionService:
    """Servicio principal de versionamiento"""
    
    def __init__(self, db=None):
        self.db = db
        self._proyectos_cache: Dict[str, ProyectoVersionado] = {}
    
    async def crear_proyecto_versionado(
        self,
        proyecto_id: str,
        nombre: str,
        rfc: str,
        datos_proyecto: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        usuario: str,
        empresa_id: Optional[str] = None
    ) -> ProyectoVersionado:
        """Crea un nuevo proyecto con versionamiento y aislamiento multi-tenant."""
        folio_base = generar_folio_base(rfc, proyecto_id)
        
        empresa_id = empresa_id or datos_proyecto.get("empresa_id")
        
        proyecto = ProyectoVersionado(
            proyecto_id=proyecto_id,
            empresa_id=empresa_id,
            nombre=nombre,
            folio_base=folio_base,
            version_actual=1,
            creado_por=usuario
        )
        
        version_inicial = await self._crear_version(
            proyecto=proyecto,
            datos_proyecto=datos_proyecto,
            documentos=documentos,
            motivo="Creación inicial del expediente",
            usuario=usuario
        )
        
        proyecto.versiones.append(version_inicial)
        
        entrada = crear_entrada_bitacora(
            usuario=usuario,
            tipo=TipoCambio.CREACION,
            titulo="Expediente creado",
            descripcion=f"Se creó el expediente {folio_base} con {len(documentos)} documentos iniciales.",
            severidad=Severidad.ALTA,
            empresa_id=empresa_id
        )
        proyecto.bitacora.append(entrada)
        
        cache_key = f"{empresa_id}:{proyecto_id}" if empresa_id else proyecto_id
        self._proyectos_cache[cache_key] = proyecto
        
        return proyecto
    
    async def obtener_proyecto(self, proyecto_id: str, empresa_id: Optional[str] = None) -> Optional[ProyectoVersionado]:
        """Obtiene un proyecto versionado con validación de empresa"""
        if empresa_id:
            cache_key = f"{empresa_id}:{proyecto_id}"
            if cache_key in self._proyectos_cache:
                return self._proyectos_cache[cache_key]
        
        if proyecto_id in self._proyectos_cache:
            proyecto = self._proyectos_cache[proyecto_id]
            if empresa_id and proyecto.empresa_id and proyecto.empresa_id.lower().strip() != empresa_id.lower().strip():
                return None
            return proyecto
        
        for key, proyecto in self._proyectos_cache.items():
            if proyecto.proyecto_id == proyecto_id:
                if empresa_id and proyecto.empresa_id and proyecto.empresa_id.lower().strip() != empresa_id.lower().strip():
                    return None
                return proyecto
        
        return None
    
    async def crear_nueva_version(
        self,
        proyecto_id: str,
        datos_proyecto: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        motivo: str,
        usuario: str,
        generar_expediente: bool = True,
        ocr_results: List[Dict] = None,
        red_team_results: Dict = None
    ) -> Tuple[ProyectoVersionado, VersionExpediente]:
        """Crea una nueva versión del expediente."""
        proyecto = await self.obtener_proyecto(proyecto_id)
        
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")
        
        version_anterior = proyecto.obtener_ultima_version()
        nueva_version_num = proyecto.version_actual + 1
        
        cambios = []
        if version_anterior:
            cambios = self._detectar_cambios(
                version_anterior.snapshot_proyecto,
                datos_proyecto,
                version_anterior.snapshot_documentos,
                documentos
            )
        
        nueva_version = await self._crear_version(
            proyecto=proyecto,
            datos_proyecto=datos_proyecto,
            documentos=documentos,
            motivo=motivo,
            usuario=usuario,
            numero_version=nueva_version_num,
            ocr_results=ocr_results,
            red_team_results=red_team_results,
            generar_expediente=generar_expediente
        )
        
        nueva_version.cambios_desde_anterior = cambios
        
        proyecto.version_actual = nueva_version_num
        proyecto.versiones.append(nueva_version)
        proyecto.fecha_ultima_modificacion = datetime.now()
        
        entrada = crear_entrada_bitacora(
            usuario=usuario,
            tipo=TipoCambio.REGENERACION_EXPEDIENTE,
            titulo=f"Nueva versión v{nueva_version_num}",
            descripcion=f"{motivo}\n\nCambios detectados:\n" + "\n".join(f"• {c}" for c in cambios[:10]),
            severidad=Severidad.ALTA,
            empresa_id=proyecto.empresa_id
        )
        proyecto.bitacora.append(entrada)
        
        cache_key = f"{proyecto.empresa_id}:{proyecto_id}" if proyecto.empresa_id else proyecto_id
        self._proyectos_cache[cache_key] = proyecto
        
        return proyecto, nueva_version
    
    async def _crear_version(
        self,
        proyecto: ProyectoVersionado,
        datos_proyecto: Dict[str, Any],
        documentos: List[Dict[str, Any]],
        motivo: str,
        usuario: str,
        numero_version: int = 1,
        ocr_results: List[Dict] = None,
        red_team_results: Dict = None,
        generar_expediente: bool = True
    ) -> VersionExpediente:
        """Crea una versión individual"""
        
        folio_completo = f"{proyecto.folio_base}-v{numero_version}"
        
        hash_contenido = generar_hash_contenido({
            'proyecto': datos_proyecto,
            'documentos': documentos,
            'timestamp': datetime.now().isoformat()
        })
        
        version = VersionExpediente(
            numero_version=numero_version,
            folio_completo=folio_completo,
            snapshot_proyecto=datos_proyecto.copy(),
            snapshot_documentos=[d.copy() for d in documentos],
            snapshot_risk_score=datos_proyecto.get('risk_score'),
            snapshot_red_team=red_team_results,
            hash_contenido=hash_contenido,
            motivo_version=motivo,
            creado_por=usuario,
            estado="borrador"
        )
        
        if generar_expediente and HAS_DEFENSE_GENERATOR:
            try:
                result = await defense_file_generator.generate(
                    project_data={**datos_proyecto, 'folio': folio_completo},
                    documents=documentos,
                    ocr_results=ocr_results or [],
                    red_team_results=red_team_results or {}
                )
                version.pdf_path = result.pdf_path
                version.zip_path = result.zip_path
            except Exception as e:
                print(f"Error generando expediente: {e}")
        
        return version
    
    async def registrar_cambio(
        self,
        proyecto_id: str,
        usuario: str,
        tipo: TipoCambio,
        titulo: str,
        descripcion: str,
        empresa_id: Optional[str] = None,
        **kwargs
    ) -> EntradaBitacora:
        """Registra un cambio en la bitácora del proyecto con aislamiento multi-tenant."""
        proyecto = await self.obtener_proyecto(proyecto_id, empresa_id)
        
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")
        
        project_empresa_id = empresa_id or proyecto.empresa_id
        
        entrada = crear_entrada_bitacora(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            empresa_id=project_empresa_id,
            **kwargs
        )
        
        proyecto.bitacora.append(entrada)
        proyecto.fecha_ultima_modificacion = datetime.now()
        
        return entrada
    
    async def registrar_comunicacion(
        self,
        proyecto_id: str,
        usuario: str,
        contraparte: str,
        tipo_contraparte: str,
        asunto: str,
        descripcion: str,
        referencia: str = None,
        adjuntos: List[str] = None
    ) -> EntradaBitacora:
        """Registra una comunicación con una contraparte externa."""
        tipo_cambio = {
            'proveedor': TipoCambio.COMUNICACION_PROVEEDOR,
            'cliente': TipoCambio.COMUNICACION_CLIENTE,
        }.get(tipo_contraparte.lower(), TipoCambio.OTRO)
        
        return await self.registrar_cambio(
            proyecto_id=proyecto_id,
            usuario=usuario,
            tipo=tipo_cambio,
            titulo=f"Comunicación con {contraparte}",
            descripcion=f"**Asunto:** {asunto}\n\n{descripcion}",
            es_comunicacion_externa=True,
            contraparte=contraparte,
            referencia_comunicacion=referencia,
            adjuntos=adjuntos or [],
            severidad=Severidad.MEDIA
        )
    
    async def registrar_correccion_vulnerabilidad(
        self,
        proyecto_id: str,
        usuario: str,
        vulnerabilidad_id: str,
        descripcion_original: str,
        accion_tomada: str,
        evidencia: str = None
    ) -> EntradaBitacora:
        """Registra la corrección de una vulnerabilidad detectada por Red Team."""
        return await self.registrar_cambio(
            proyecto_id=proyecto_id,
            usuario=usuario,
            tipo=TipoCambio.CORRECCION_VULNERABILIDAD,
            titulo=f"Vulnerabilidad corregida: {vulnerabilidad_id}",
            descripcion=f"""**Vulnerabilidad original:**
{descripcion_original}

**Acción tomada:**
{accion_tomada}

**Evidencia de corrección:**
{evidencia or 'No especificada'}""",
            severidad=Severidad.ALTA,
            campo_afectado=vulnerabilidad_id
        )
    
    async def obtener_bitacora(
        self,
        proyecto_id: str,
        tipo: TipoCambio = None,
        severidad_minima: Severidad = None,
        desde: datetime = None,
        hasta: datetime = None,
        limite: int = 100
    ) -> List[EntradaBitacora]:
        """Obtiene entradas de bitácora con filtros opcionales."""
        proyecto = await self.obtener_proyecto(proyecto_id)
        
        if not proyecto:
            return []
        
        entradas = proyecto.bitacora.copy()
        
        if tipo:
            entradas = [e for e in entradas if e.tipo_cambio == tipo]
        
        if severidad_minima:
            niveles = {
                Severidad.INFO: 0,
                Severidad.BAJA: 1,
                Severidad.MEDIA: 2,
                Severidad.ALTA: 3,
                Severidad.CRITICA: 4
            }
            nivel_min = niveles.get(severidad_minima, 0)
            entradas = [e for e in entradas if niveles.get(e.severidad, 0) >= nivel_min]
        
        if desde:
            entradas = [e for e in entradas if e.timestamp >= desde]
        
        if hasta:
            entradas = [e for e in entradas if e.timestamp <= hasta]
        
        entradas.sort(key=lambda e: e.timestamp, reverse=True)
        
        return entradas[:limite]
    
    async def obtener_comunicaciones(
        self,
        proyecto_id: str,
        contraparte: str = None
    ) -> List[EntradaBitacora]:
        """Obtiene historial de comunicaciones externas."""
        proyecto = await self.obtener_proyecto(proyecto_id)
        
        if not proyecto:
            return []
        
        comunicaciones = [
            e for e in proyecto.bitacora
            if e.es_comunicacion_externa
        ]
        
        if contraparte:
            comunicaciones = [
                e for e in comunicaciones
                if e.contraparte and contraparte.lower() in e.contraparte.lower()
            ]
        
        comunicaciones.sort(key=lambda e: e.timestamp, reverse=True)
        
        return comunicaciones
    
    def _detectar_cambios(
        self,
        datos_anterior: Dict[str, Any],
        datos_nuevo: Dict[str, Any],
        docs_anterior: List[Dict[str, Any]],
        docs_nuevo: List[Dict[str, Any]]
    ) -> List[str]:
        """Detecta cambios entre dos versiones."""
        cambios = []
        
        for key in set(list(datos_anterior.keys()) + list(datos_nuevo.keys())):
            val_ant = datos_anterior.get(key)
            val_new = datos_nuevo.get(key)
            
            if val_ant != val_new:
                if val_ant is None:
                    cambios.append(f"Campo '{key}' agregado: {val_new}")
                elif val_new is None:
                    cambios.append(f"Campo '{key}' eliminado")
                else:
                    cambios.append(f"Campo '{key}' modificado: {val_ant} → {val_new}")
        
        nombres_ant = {d.get('nombre', d.get('name', '')) for d in docs_anterior}
        nombres_new = {d.get('nombre', d.get('name', '')) for d in docs_nuevo}
        
        for nombre in nombres_new - nombres_ant:
            cambios.append(f"Documento agregado: {nombre}")
        
        for nombre in nombres_ant - nombres_new:
            cambios.append(f"Documento eliminado: {nombre}")
        
        return cambios
    
    async def comparar_versiones(
        self,
        proyecto_id: str,
        version_a: int,
        version_b: int
    ) -> Dict[str, Any]:
        """Compara dos versiones del expediente."""
        proyecto = await self.obtener_proyecto(proyecto_id)
        
        if not proyecto:
            raise ValueError(f"Proyecto {proyecto_id} no encontrado")
        
        ver_a = proyecto.obtener_version(version_a)
        ver_b = proyecto.obtener_version(version_b)
        
        if not ver_a or not ver_b:
            raise ValueError("Una o ambas versiones no existen")
        
        cambios_datos = self._detectar_cambios(
            ver_a.snapshot_proyecto,
            ver_b.snapshot_proyecto,
            ver_a.snapshot_documentos,
            ver_b.snapshot_documentos
        )
        
        diff_risk = None
        if ver_a.snapshot_risk_score and ver_b.snapshot_risk_score:
            diff_risk = ver_b.snapshot_risk_score - ver_a.snapshot_risk_score
        
        return {
            "version_a": {
                "numero": ver_a.numero_version,
                "folio": ver_a.folio_completo,
                "fecha": ver_a.fecha_creacion.isoformat(),
                "creado_por": ver_a.creado_por,
                "motivo": ver_a.motivo_version
            },
            "version_b": {
                "numero": ver_b.numero_version,
                "folio": ver_b.folio_completo,
                "fecha": ver_b.fecha_creacion.isoformat(),
                "creado_por": ver_b.creado_por,
                "motivo": ver_b.motivo_version
            },
            "cambios": cambios_datos,
            "total_cambios": len(cambios_datos),
            "diferencia_risk_score": diff_risk,
            "documentos_version_a": len(ver_a.snapshot_documentos),
            "documentos_version_b": len(ver_b.snapshot_documentos)
        }
    
    async def obtener_resumen_proyecto(
        self,
        proyecto_id: str
    ) -> Dict[str, Any]:
        """Obtiene resumen completo del proyecto versionado."""
        proyecto = await self.obtener_proyecto(proyecto_id)
        
        if not proyecto:
            return None
        
        ultima_version = proyecto.obtener_ultima_version()
        
        cambios_por_tipo = {}
        for entrada in proyecto.bitacora:
            tipo = entrada.tipo_cambio
            if isinstance(tipo, TipoCambio):
                tipo = tipo.value
            cambios_por_tipo[tipo] = cambios_por_tipo.get(tipo, 0) + 1
        
        cambios_por_severidad = {}
        for entrada in proyecto.bitacora:
            sev = entrada.severidad
            if isinstance(sev, Severidad):
                sev = sev.value
            cambios_por_severidad[sev] = cambios_por_severidad.get(sev, 0) + 1
        
        return {
            "proyecto_id": proyecto.proyecto_id,
            "nombre": proyecto.nombre,
            "folio_actual": proyecto.obtener_folio_actual(),
            "version_actual": proyecto.version_actual,
            "estado": proyecto.estado_expediente,
            "fecha_creacion": proyecto.fecha_creacion.isoformat(),
            "fecha_ultima_modificacion": proyecto.fecha_ultima_modificacion.isoformat(),
            "creado_por": proyecto.creado_por,
            "total_versiones": len(proyecto.versiones),
            "total_entradas_bitacora": len(proyecto.bitacora),
            "cambios_por_tipo": cambios_por_tipo,
            "cambios_por_severidad": cambios_por_severidad,
            "ultima_version": {
                "numero": ultima_version.numero_version,
                "estado": ultima_version.estado,
                "risk_score": ultima_version.snapshot_risk_score,
                "documentos": len(ultima_version.snapshot_documentos),
                "pdf_generado": ultima_version.pdf_path is not None,
                "zip_generado": ultima_version.zip_path is not None
            } if ultima_version else None
        }


version_service = VersionService()
