"""
Rutas de API para Checklists por Tipología - Revisar.IA
Incluye endpoints para comunicación con proveedores
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from checklists import (
    CHECKLISTS_POR_TIPOLOGIA,
    get_checklist_tipologia,
    get_items_fase,
    get_items_obligatorios,
    get_item_por_id,
    get_items_por_responsable,
    validar_items_completos,
    get_resumen_tipologia,
    get_todas_tipologias,
    build_checklist_prompt_section
)

from services.notificacion_proveedor_service import notificacion_proveedor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/checklists", tags=["Checklists Revisar.IA"])


class ValidacionRequest(BaseModel):
    tipologia: str
    fase: str
    items_cumplidos: List[str]


@router.get("/tipologias")
async def get_tipologias_disponibles() -> Dict[str, Any]:
    """Obtiene todas las tipologías con checklists disponibles"""
    tipologias = get_todas_tipologias()
    return {
        "total": len(tipologias),
        "tipologias": tipologias
    }


@router.get("/tipologia/{tipologia}")
async def get_checklist_completo(tipologia: str) -> Dict[str, Any]:
    """Obtiene el checklist completo de una tipología"""
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' no encontrada. Opciones: {list(CHECKLISTS_POR_TIPOLOGIA.keys())}"
        )
    return checklist


@router.get("/tipologia/{tipologia}/resumen")
async def get_resumen(tipologia: str) -> Dict[str, Any]:
    """Obtiene un resumen del checklist de una tipología"""
    resumen = get_resumen_tipologia(tipologia)
    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' no encontrada"
        )
    return resumen


@router.get("/tipologia/{tipologia}/fase/{fase}")
async def get_items_de_fase(tipologia: str, fase: str) -> Dict[str, Any]:
    """Obtiene los items de checklist para una tipología y fase específicas"""
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' no encontrada"
        )
    
    items = get_items_fase(tipologia, fase)
    if items is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fase '{fase}' no encontrada para tipología '{tipologia}'"
        )
    
    fase_upper = fase.upper()
    fase_data = checklist.get(fase_upper, {})
    
    return {
        "tipologia": tipologia,
        "fase": fase_upper,
        "nombre_fase": fase_data.get("nombre", ""),
        "total_items": len(items),
        "obligatorios": len([i for i in items if i.get("obligatorio", False)]),
        "items": items
    }


@router.get("/tipologia/{tipologia}/fase/{fase}/obligatorios")
async def get_obligatorios_de_fase(tipologia: str, fase: str) -> Dict[str, Any]:
    """Obtiene solo los items obligatorios de una fase"""
    items = get_items_obligatorios(tipologia, fase)
    if not items and items != []:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' o fase '{fase}' no encontrada"
        )
    
    return {
        "tipologia": tipologia,
        "fase": fase.upper(),
        "total_obligatorios": len(items),
        "items": items
    }


@router.get("/item/{item_id}")
async def get_item_especifico(item_id: str) -> Dict[str, Any]:
    """Busca un item específico por su ID único (ej: CMM_F5_02)"""
    item = get_item_por_id(item_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item '{item_id}' no encontrado"
        )
    return item


@router.get("/tipologia/{tipologia}/responsable/{responsable}")
async def get_items_de_responsable(tipologia: str, responsable: str) -> Dict[str, Any]:
    """Obtiene todos los items asignados a un responsable"""
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' no encontrada"
        )
    
    items = get_items_por_responsable(tipologia, responsable)
    
    return {
        "tipologia": tipologia,
        "responsable": responsable.upper(),
        "total_items": len(items),
        "items": items
    }


@router.post("/validar")
async def validar_completitud(request: ValidacionRequest) -> Dict[str, Any]:
    """
    Valida qué items de un checklist están completos y cuáles faltan.
    
    Retorna faltantes obligatorios, opcionales, y si puede avanzar a siguiente fase.
    """
    resultado = validar_items_completos(
        request.tipologia,
        request.fase,
        request.items_cumplidos
    )
    
    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    
    return resultado


@router.get("/prompt/{tipologia}/{fase}")
async def get_prompt_section(tipologia: str, fase: str) -> Dict[str, str]:
    """Genera una sección de prompt con el checklist específico para agentes"""
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        raise HTTPException(
            status_code=404,
            detail=f"Tipología '{tipologia}' no encontrada"
        )
    
    prompt = build_checklist_prompt_section(tipologia, fase)
    return {"prompt_section": prompt}


@router.get("/faltantes-ejemplo/{tipologia}/{fase}")
async def get_ejemplo_faltantes(tipologia: str, fase: str) -> Dict[str, Any]:
    """
    Ejemplo de cómo un agente debe reportar items faltantes.
    Muestra el formato específico que deben usar los agentes.
    """
    items = get_items_obligatorios(tipologia, fase)
    if not items:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron items para {tipologia} fase {fase}"
        )
    
    ejemplo_faltantes = []
    for item in items[:3]:
        ejemplo_faltantes.append({
            "item_id": item["id"],
            "descripcion": item["descripcion"],
            "accion_requerida": f"Proporcionar: {item['criterio_aceptacion']}",
            "responsable": item["responsable"],
            "ejemplo_correcto": item.get("ejemplo_bueno", "N/A")
        })
    
    return {
        "tipologia": tipologia,
        "fase": fase.upper(),
        "instruccion_agente": "Cuando encuentres items faltantes, reporta en este formato:",
        "ejemplo_reporte": {
            "decision": "SOLICITAR_AJUSTES",
            "items_faltantes": ejemplo_faltantes,
            "mensaje": f"Faltan los siguientes documentos obligatorios para la fase {fase}: " + 
                       ", ".join([f["item_id"] for f in ejemplo_faltantes])
        },
        "nota": "NO reportar: 'Falta documentación'. SÍ reportar: 'Falta CMM_F5_02: Modelo paramétrico funcional'"
    }


class ChecklistProveedorRequest(BaseModel):
    tipologia: str
    fase_actual: str
    items_cumplidos: List[str] = []


class EnviarChecklistRequest(BaseModel):
    email_proveedor: str
    tipologia: Optional[str] = None
    fase_actual: Optional[str] = None
    items_cumplidos: Optional[List[str]] = []
    items_pendientes: Optional[List[Dict[str, Any]]] = []
    tipo_mensaje: str = "pendientes"


projects_router = APIRouter(tags=["Proyectos - Checklist Proveedor"])


@projects_router.get("/{proyecto_id}/checklist-proveedor")
async def get_checklist_proveedor(
    proyecto_id: str,
    tipologia: str = None,
    fase_actual: str = "F5"
) -> Dict[str, Any]:
    """
    Obtiene el checklist de items pendientes para el proveedor de un proyecto.
    
    Retorna los documentos y entregables que debe proporcionar el proveedor,
    agrupados por fase y con indicador de cumplimiento.
    """
    if not tipologia:
        tipologia = "CONSULTORIA_MACRO_MERCADO"
    
    try:
        checklist_data = notificacion_proveedor_service.generar_checklist_para_proveedor(
            tipologia=tipologia,
            fase_actual=fase_actual,
            items_cumplidos=[],
            incluir_fases_anteriores=True
        )
        
        return {
            "success": True,
            "proyecto_id": proyecto_id,
            "checklist": checklist_data.get("items_pendientes", []) + checklist_data.get("items_completados", []),
            "items_cumplidos": [i["id"] for i in checklist_data.get("items_completados", [])],
            "resumen": checklist_data.get("resumen", {}),
            "progreso_porcentaje": checklist_data.get("progreso_porcentaje", 0),
            "puede_avanzar": checklist_data.get("puede_avanzar", False)
        }
    except Exception as e:
        logger.error(f"Error obteniendo checklist proveedor: {e}")
        items_proveedor = get_items_por_responsable(tipologia, "PROVEEDOR")
        return {
            "success": True,
            "proyecto_id": proyecto_id,
            "checklist": items_proveedor,
            "items_cumplidos": [],
            "resumen": {"total": len(items_proveedor), "completados": 0, "pendientes": len(items_proveedor)},
            "progreso_porcentaje": 0,
            "puede_avanzar": False
        }


@projects_router.post("/{proyecto_id}/enviar-checklist")
async def enviar_checklist_proveedor(
    proyecto_id: str,
    request: EnviarChecklistRequest
) -> Dict[str, Any]:
    """
    Envía el checklist de pendientes al proveedor por email.
    
    Genera un email profesional con los documentos faltantes y lo envía
    al correo del proveedor especificado.
    """
    if not request.email_proveedor:
        raise HTTPException(
            status_code=400,
            detail="Se requiere email_proveedor para enviar el checklist"
        )
    
    tipologia = request.tipologia or "CONSULTORIA_MACRO_MERCADO"
    fase_actual = request.fase_actual or "F5"
    
    try:
        resultado = await notificacion_proveedor_service.enviar_checklist_proveedor(
            email_proveedor=request.email_proveedor,
            proyecto_id=proyecto_id,
            proyecto_nombre=f"Proyecto {proyecto_id}",
            proyecto_folio=f"PROJ-{proyecto_id[:8].upper()}",
            tipologia=tipologia,
            fase_actual=fase_actual,
            items_cumplidos=request.items_cumplidos or [],
            tipo_mensaje=request.tipo_mensaje
        )
        
        return {
            "success": resultado.get("success", False),
            "mensaje": resultado.get("mensaje", ""),
            "email_destino": request.email_proveedor,
            "items_notificados": resultado.get("items_notificados", 0),
            "proyecto_id": proyecto_id
        }
    except Exception as e:
        logger.error(f"Error enviando checklist: {e}")
        return {
            "success": False,
            "mensaje": f"Error al enviar: {str(e)}",
            "email_destino": request.email_proveedor,
            "items_notificados": 0,
            "proyecto_id": proyecto_id
        }


@router.get("/proveedor/{tipologia}")
async def get_checklist_proveedor_por_tipologia(
    tipologia: str,
    fase_actual: str = "F5",
    incluir_anteriores: bool = True
) -> Dict[str, Any]:
    """
    Genera checklist completo para proveedor de una tipología específica.
    
    Útil para preparar comunicaciones o generar reportes de pendientes.
    """
    resultado = notificacion_proveedor_service.generar_checklist_para_proveedor(
        tipologia=tipologia,
        fase_actual=fase_actual,
        items_cumplidos=[],
        incluir_fases_anteriores=incluir_anteriores
    )
    
    return {
        "success": True,
        **resultado
    }


