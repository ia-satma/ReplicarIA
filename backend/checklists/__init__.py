"""
Checklists Específicos por Tipología - Revisar.IA

Este módulo proporciona checklists detallados por tipología de servicio,
permitiendo a los agentes dar recomendaciones específicas en lugar de genéricas.

Ejemplo: En lugar de "falta documentación", el agente puede decir
"Falta CMM_F5_02: Modelo paramétrico funcional"
"""

from typing import Dict, Any, List, Optional
from .consultoria_macro_mercado import CHECKLIST_CONSULTORIA_MACRO_MERCADO
from .intragrupo_management_fee import CHECKLIST_INTRAGRUPO_MANAGEMENT_FEE
from .software_saas_desarrollo import CHECKLIST_SOFTWARE_SAAS_DESARROLLO

CHECKLISTS_POR_TIPOLOGIA: Dict[str, Dict[str, Any]] = {
    "CONSULTORIA_MACRO_MERCADO": CHECKLIST_CONSULTORIA_MACRO_MERCADO,
    "INTRAGRUPO_MANAGEMENT_FEE": CHECKLIST_INTRAGRUPO_MANAGEMENT_FEE,
    "SOFTWARE_SAAS_DESARROLLO": CHECKLIST_SOFTWARE_SAAS_DESARROLLO,
}


def get_checklist_tipologia(tipologia: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el checklist completo para una tipología específica.
    
    Args:
        tipologia: ID de la tipología (ej: "CONSULTORIA_MACRO_MERCADO")
    
    Returns:
        Checklist completo o None si no existe
    """
    return CHECKLISTS_POR_TIPOLOGIA.get(tipologia.upper())


def get_items_fase(tipologia: str, fase: str) -> Optional[List[Dict[str, Any]]]:
    """
    Obtiene los items de checklist para una tipología y fase específicas.
    
    Args:
        tipologia: ID de la tipología (ej: "CONSULTORIA_MACRO_MERCADO")
        fase: ID de la fase (ej: "F0", "F5")
    
    Returns:
        Lista de items o None si no existe
    """
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        return None
    
    fase_upper = fase.upper()
    if fase_upper not in checklist:
        return None
    
    return checklist[fase_upper].get("items", [])


def get_items_obligatorios(tipologia: str, fase: str) -> List[Dict[str, Any]]:
    """
    Obtiene solo los items obligatorios de una fase.
    
    Args:
        tipologia: ID de la tipología
        fase: ID de la fase
    
    Returns:
        Lista de items obligatorios
    """
    items = get_items_fase(tipologia, fase)
    if not items:
        return []
    return [item for item in items if item.get("obligatorio", False)]


def get_item_por_id(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca un item específico por su ID único.
    
    Args:
        item_id: ID del item (ej: "CMM_F5_02")
    
    Returns:
        Item encontrado o None
    """
    for tipologia, checklist in CHECKLISTS_POR_TIPOLOGIA.items():
        for fase_key, fase_data in checklist.items():
            if isinstance(fase_data, dict) and "items" in fase_data:
                for item in fase_data["items"]:
                    if item.get("id") == item_id:
                        return {
                            **item,
                            "tipologia": tipologia,
                            "fase": fase_key
                        }
    return None


def get_items_por_responsable(tipologia: str, responsable: str) -> List[Dict[str, Any]]:
    """
    Obtiene todos los items asignados a un responsable.
    
    Args:
        tipologia: ID de la tipología
        responsable: Rol responsable (SPONSOR, FISCAL, LEGAL, FINANZAS, PROVEEDOR, PMO)
    
    Returns:
        Lista de items del responsable
    """
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        return []
    
    items_responsable = []
    for fase_key, fase_data in checklist.items():
        if isinstance(fase_data, dict) and "items" in fase_data:
            for item in fase_data["items"]:
                if item.get("responsable", "").upper() == responsable.upper():
                    items_responsable.append({
                        **item,
                        "fase": fase_key
                    })
    
    return items_responsable


def validar_items_completos(tipologia: str, fase: str, items_cumplidos: List[str]) -> Dict[str, Any]:
    """
    Valida qué items de un checklist están completos y cuáles faltan.
    
    Args:
        tipologia: ID de la tipología
        fase: ID de la fase
        items_cumplidos: Lista de IDs de items cumplidos
    
    Returns:
        Diccionario con faltantes obligatorios, faltantes opcionales y porcentaje de completitud
    """
    items = get_items_fase(tipologia, fase)
    if not items:
        return {
            "error": f"Tipología '{tipologia}' o fase '{fase}' no encontrada",
            "faltantes_obligatorios": [],
            "faltantes_opcionales": [],
            "completitud_obligatorios": 0,
            "completitud_total": 0
        }
    
    items_cumplidos_set = set(items_cumplidos)
    
    faltantes_obligatorios = []
    faltantes_opcionales = []
    obligatorios_total = 0
    obligatorios_cumplidos = 0
    
    for item in items:
        item_id = item.get("id")
        es_obligatorio = item.get("obligatorio", False)
        
        if es_obligatorio:
            obligatorios_total += 1
            if item_id in items_cumplidos_set:
                obligatorios_cumplidos += 1
            else:
                faltantes_obligatorios.append({
                    "id": item_id,
                    "descripcion": item.get("descripcion"),
                    "responsable": item.get("responsable"),
                    "criterio_aceptacion": item.get("criterio_aceptacion"),
                    "ejemplo_bueno": item.get("ejemplo_bueno")
                })
        else:
            if item_id not in items_cumplidos_set:
                faltantes_opcionales.append({
                    "id": item_id,
                    "descripcion": item.get("descripcion"),
                    "responsable": item.get("responsable")
                })
    
    total_items = len(items)
    total_cumplidos = len([i for i in items if i.get("id") in items_cumplidos_set])
    
    return {
        "fase": fase,
        "tipologia": tipologia,
        "faltantes_obligatorios": faltantes_obligatorios,
        "faltantes_opcionales": faltantes_opcionales,
        "completitud_obligatorios": round(obligatorios_cumplidos / obligatorios_total * 100, 1) if obligatorios_total > 0 else 100,
        "completitud_total": round(total_cumplidos / total_items * 100, 1) if total_items > 0 else 100,
        "puede_avanzar": len(faltantes_obligatorios) == 0
    }


def get_resumen_tipologia(tipologia: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un resumen del checklist de una tipología.
    
    Args:
        tipologia: ID de la tipología
    
    Returns:
        Resumen con totales por fase
    """
    checklist = get_checklist_tipologia(tipologia)
    if not checklist:
        return None
    
    resumen = {
        "tipologia": tipologia,
        "nombre": checklist.get("nombre"),
        "riesgo_inherente": checklist.get("riesgo_inherente", "MEDIO"),
        "revision_humana_obligatoria": checklist.get("revision_humana_obligatoria", False),
        "alertas_especiales": checklist.get("alertas_especiales", []),
        "fases": {}
    }
    
    total_items = 0
    total_obligatorios = 0
    
    for fase_key in ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]:
        if fase_key in checklist and isinstance(checklist[fase_key], dict):
            fase_data = checklist[fase_key]
            items = fase_data.get("items", [])
            obligatorios = len([i for i in items if i.get("obligatorio", False)])
            
            resumen["fases"][fase_key] = {
                "nombre": fase_data.get("nombre", ""),
                "total_items": len(items),
                "obligatorios": obligatorios,
                "opcionales": len(items) - obligatorios
            }
            
            total_items += len(items)
            total_obligatorios += obligatorios
    
    resumen["total_items"] = total_items
    resumen["total_obligatorios"] = total_obligatorios
    
    return resumen


def get_todas_tipologias() -> List[Dict[str, Any]]:
    """
    Obtiene la lista de todas las tipologías disponibles con sus resúmenes.
    
    Returns:
        Lista de resúmenes de tipologías
    """
    tipologias = []
    for tipologia_id in CHECKLISTS_POR_TIPOLOGIA.keys():
        resumen = get_resumen_tipologia(tipologia_id)
        if resumen:
            tipologias.append(resumen)
    return tipologias


def build_checklist_prompt_section(tipologia: str, fase: str) -> str:
    """
    Genera una sección de prompt con el checklist específico para agentes.
    
    Args:
        tipologia: ID de la tipología
        fase: ID de la fase
    
    Returns:
        Texto formateado para incluir en prompt de agente
    """
    items = get_items_fase(tipologia, fase)
    if not items:
        return f"No se encontró checklist para {tipologia} fase {fase}"
    
    checklist = get_checklist_tipologia(tipologia)
    fase_nombre = checklist.get(fase, {}).get("nombre", fase)
    
    lines = [
        f"## CHECKLIST: {checklist.get('nombre')} - {fase_nombre}",
        ""
    ]
    
    for item in items:
        obligatorio_mark = "[OBLIGATORIO]" if item.get("obligatorio") else "[OPCIONAL]"
        lines.extend([
            f"### {item['id']} {obligatorio_mark}",
            f"**Descripción:** {item['descripcion']}",
            f"**Responsable:** {item['responsable']}",
            f"**Criterio de Aceptación:** {item['criterio_aceptacion']}",
            f"**Ejemplo Bueno:** {item.get('ejemplo_bueno', 'N/A')}",
            f"**Ejemplo Malo:** {item.get('ejemplo_malo', 'N/A')}",
            ""
        ])
    
    return "\n".join(lines)
