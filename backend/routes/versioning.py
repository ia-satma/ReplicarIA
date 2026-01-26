"""
RUTAS API PARA VERSIONAMIENTO DE EXPEDIENTES
Endpoints para gestión de versiones y bitácora
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.versioning import TipoCambio, Severidad
from services.versioning_service import version_service

router = APIRouter(prefix="/api/versioning", tags=["versioning"])


class CrearProyectoRequest(BaseModel):
    proyecto_id: str
    nombre: str
    rfc: str
    datos_proyecto: Dict[str, Any]
    documentos: List[Dict[str, Any]] = []
    usuario: str


class NuevaVersionRequest(BaseModel):
    datos_proyecto: Dict[str, Any]
    documentos: List[Dict[str, Any]] = []
    motivo: str
    usuario: str
    generar_expediente: bool = True
    ocr_results: Optional[List[Dict]] = None
    red_team_results: Optional[Dict] = None


class RegistrarCambioRequest(BaseModel):
    usuario: str
    tipo: str
    titulo: str
    descripcion: str
    severidad: str = "media"
    campo_afectado: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    documento_id: Optional[str] = None
    documento_nombre: Optional[str] = None


class RegistrarComunicacionRequest(BaseModel):
    usuario: str
    contraparte: str
    tipo_contraparte: str
    asunto: str
    descripcion: str
    referencia: Optional[str] = None
    adjuntos: List[str] = []


@router.post("/proyectos")
async def crear_proyecto(request: CrearProyectoRequest):
    """Crea un nuevo proyecto versionado."""
    try:
        proyecto = await version_service.crear_proyecto_versionado(
            proyecto_id=request.proyecto_id,
            nombre=request.nombre,
            rfc=request.rfc,
            datos_proyecto=request.datos_proyecto,
            documentos=request.documentos,
            usuario=request.usuario
        )
        
        return {
            "success": True,
            "proyecto_id": proyecto.proyecto_id,
            "folio": proyecto.obtener_folio_actual(),
            "version": proyecto.version_actual,
            "mensaje": f"Proyecto creado exitosamente: {proyecto.obtener_folio_actual()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proyectos/{proyecto_id}")
async def obtener_proyecto(proyecto_id: str):
    """Obtiene un proyecto versionado con su resumen."""
    resumen = await version_service.obtener_resumen_proyecto(proyecto_id)
    
    if not resumen:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {"success": True, "proyecto": resumen}


@router.post("/proyectos/{proyecto_id}/versiones")
async def crear_version(proyecto_id: str, request: NuevaVersionRequest):
    """Crea una nueva versión del expediente."""
    try:
        proyecto, nueva_version = await version_service.crear_nueva_version(
            proyecto_id=proyecto_id,
            datos_proyecto=request.datos_proyecto,
            documentos=request.documentos,
            motivo=request.motivo,
            usuario=request.usuario,
            generar_expediente=request.generar_expediente,
            ocr_results=request.ocr_results,
            red_team_results=request.red_team_results
        )
        
        return {
            "success": True,
            "folio": proyecto.obtener_folio_actual(),
            "version": nueva_version.numero_version,
            "cambios_detectados": nueva_version.cambios_desde_anterior,
            "hash": nueva_version.hash_contenido,
            "pdf_path": nueva_version.pdf_path,
            "zip_path": nueva_version.zip_path
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proyectos/{proyecto_id}/versiones")
async def listar_versiones(proyecto_id: str):
    """Lista todas las versiones de un proyecto."""
    proyecto = await version_service.obtener_proyecto(proyecto_id)
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    versiones = []
    for v in proyecto.versiones:
        versiones.append({
            "numero": v.numero_version,
            "folio": v.folio_completo,
            "estado": v.estado,
            "fecha_creacion": v.fecha_creacion.isoformat(),
            "creado_por": v.creado_por,
            "motivo": v.motivo_version,
            "documentos": len(v.snapshot_documentos),
            "risk_score": v.snapshot_risk_score,
            "pdf_generado": v.pdf_path is not None,
            "zip_generado": v.zip_path is not None
        })
    
    return {"success": True, "versiones": versiones, "total": len(versiones)}


@router.get("/proyectos/{proyecto_id}/versiones/{version_a}/comparar/{version_b}")
async def comparar_versiones(proyecto_id: str, version_a: int, version_b: int):
    """Compara dos versiones del expediente."""
    try:
        comparacion = await version_service.comparar_versiones(
            proyecto_id=proyecto_id,
            version_a=version_a,
            version_b=version_b
        )
        return {"success": True, "comparacion": comparacion}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/proyectos/{proyecto_id}/bitacora")
async def registrar_cambio(proyecto_id: str, request: RegistrarCambioRequest):
    """Registra un cambio en la bitácora."""
    try:
        tipo_enum = TipoCambio(request.tipo)
        severidad_enum = Severidad(request.severidad)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo o severidad inválidos")
    
    try:
        entrada = await version_service.registrar_cambio(
            proyecto_id=proyecto_id,
            usuario=request.usuario,
            tipo=tipo_enum,
            titulo=request.titulo,
            descripcion=request.descripcion,
            severidad=severidad_enum,
            campo_afectado=request.campo_afectado,
            valor_anterior=request.valor_anterior,
            valor_nuevo=request.valor_nuevo,
            documento_id=request.documento_id,
            documento_nombre=request.documento_nombre
        )
        
        return {
            "success": True,
            "entrada_id": entrada.id,
            "timestamp": entrada.timestamp.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/proyectos/{proyecto_id}/bitacora/comunicacion")
async def registrar_comunicacion(proyecto_id: str, request: RegistrarComunicacionRequest):
    """Registra una comunicación externa."""
    try:
        entrada = await version_service.registrar_comunicacion(
            proyecto_id=proyecto_id,
            usuario=request.usuario,
            contraparte=request.contraparte,
            tipo_contraparte=request.tipo_contraparte,
            asunto=request.asunto,
            descripcion=request.descripcion,
            referencia=request.referencia,
            adjuntos=request.adjuntos
        )
        
        return {
            "success": True,
            "entrada_id": entrada.id,
            "timestamp": entrada.timestamp.isoformat(),
            "mensaje": f"Comunicación con {request.contraparte} registrada"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/proyectos/{proyecto_id}/bitacora")
async def obtener_bitacora(
    proyecto_id: str,
    tipo: Optional[str] = None,
    severidad_minima: Optional[str] = None,
    limite: int = Query(default=100, le=500)
):
    """Obtiene la bitácora con filtros opcionales."""
    tipo_enum = None
    severidad_enum = None
    
    if tipo:
        try:
            tipo_enum = TipoCambio(tipo)
        except ValueError:
            pass
    
    if severidad_minima:
        try:
            severidad_enum = Severidad(severidad_minima)
        except ValueError:
            pass
    
    entradas = await version_service.obtener_bitacora(
        proyecto_id=proyecto_id,
        tipo=tipo_enum,
        severidad_minima=severidad_enum,
        limite=limite
    )
    
    resultado = []
    for e in entradas:
        resultado.append({
            "id": e.id,
            "timestamp": e.timestamp.isoformat(),
            "usuario": e.usuario,
            "rol_usuario": e.rol_usuario,
            "tipo_cambio": e.tipo_cambio if isinstance(e.tipo_cambio, str) else e.tipo_cambio.value,
            "severidad": e.severidad if isinstance(e.severidad, str) else e.severidad.value,
            "titulo": e.titulo,
            "descripcion": e.descripcion,
            "es_comunicacion_externa": e.es_comunicacion_externa,
            "contraparte": e.contraparte,
            "documento_nombre": e.documento_nombre
        })
    
    return {"success": True, "bitacora": resultado, "total": len(resultado)}


@router.get("/proyectos/{proyecto_id}/bitacora/reporte")
async def exportar_bitacora(
    proyecto_id: str,
    formato: str = Query(default="json", regex="^(json|markdown)$")
):
    """Exporta la bitácora en formato JSON o Markdown."""
    proyecto = await version_service.obtener_proyecto(proyecto_id)
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if formato == "markdown":
        lineas = [
            f"# Bitácora de Cambios",
            f"**Proyecto:** {proyecto.nombre}",
            f"**Folio:** {proyecto.obtener_folio_actual()}",
            f"**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "",
            "---",
            ""
        ]
        
        for entrada in proyecto.bitacora:
            sev = entrada.severidad if isinstance(entrada.severidad, str) else entrada.severidad.value
            tipo = entrada.tipo_cambio if isinstance(entrada.tipo_cambio, str) else entrada.tipo_cambio.value
            
            lineas.append(f"### {entrada.titulo}")
            lineas.append(f"- **Fecha:** {entrada.timestamp.strftime('%d/%m/%Y %H:%M')}")
            lineas.append(f"- **Usuario:** {entrada.usuario}")
            lineas.append(f"- **Tipo:** {tipo}")
            lineas.append(f"- **Severidad:** {sev}")
            lineas.append("")
            lineas.append(entrada.descripcion)
            lineas.append("")
            lineas.append("---")
            lineas.append("")
        
        return {
            "success": True,
            "formato": "markdown",
            "contenido": "\n".join(lineas)
        }
    
    return {
        "success": True,
        "formato": "json",
        "proyecto": {
            "id": proyecto.proyecto_id,
            "nombre": proyecto.nombre,
            "folio": proyecto.obtener_folio_actual()
        },
        "bitacora": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "usuario": e.usuario,
                "tipo_cambio": e.tipo_cambio if isinstance(e.tipo_cambio, str) else e.tipo_cambio.value,
                "severidad": e.severidad if isinstance(e.severidad, str) else e.severidad.value,
                "titulo": e.titulo,
                "descripcion": e.descripcion
            }
            for e in proyecto.bitacora
        ]
    }


@router.get("/proyectos/{proyecto_id}/comunicaciones")
async def obtener_comunicaciones(
    proyecto_id: str,
    contraparte: Optional[str] = None
):
    """Obtiene historial de comunicaciones externas."""
    comunicaciones = await version_service.obtener_comunicaciones(
        proyecto_id=proyecto_id,
        contraparte=contraparte
    )
    
    resultado = []
    for c in comunicaciones:
        resultado.append({
            "id": c.id,
            "timestamp": c.timestamp.isoformat(),
            "usuario": c.usuario,
            "contraparte": c.contraparte,
            "titulo": c.titulo,
            "descripcion": c.descripcion,
            "referencia": c.referencia_comunicacion,
            "adjuntos": c.adjuntos
        })
    
    return {"success": True, "comunicaciones": resultado, "total": len(resultado)}
