"""
Servicio de Gestión de Fases - Revisar.IA

Implementa la lógica de flujo F0-F9 y los tres candados duros:
- CANDADO F2: No iniciar ejecución sin aprobación completa
- CANDADO F6: No emitir CFDI/pago sin VBC de Fiscal y Legal
- CANDADO F8: No liberar pago sin 3-way match validado
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from config.reglas_tipologia import validar_checklist_fase, get_checklist_obligatorio

ORDEN_FASES = ['F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9']

CANDADOS_DUROS = ['F2', 'F6', 'F8']

FASES_CONFIG = {
    "F0": {
        "nombre": "Aprobación - Definir BEE",
        "agentes_obligatorios": ["A1_SPONSOR", "A3_FISCAL"],
        "es_candado_duro": False
    },
    "F1": {
        "nombre": "Pre-contratación / SOW",
        "agentes_obligatorios": ["A4_LEGAL"],
        "es_candado_duro": False
    },
    "F2": {
        "nombre": "Validación previa al inicio",
        "agentes_obligatorios": ["A5_FINANZAS"],
        "es_candado_duro": True,
        "descripcion_candado": "No puede iniciarse ejecución sin aprobación completa"
    },
    "F3": {
        "nombre": "Ejecución inicial",
        "agentes_obligatorios": ["A6_PROVEEDOR"],
        "es_candado_duro": False
    },
    "F4": {
        "nombre": "Revisión iterativa",
        "agentes_obligatorios": ["A1_SPONSOR", "A6_PROVEEDOR"],
        "es_candado_duro": False
    },
    "F5": {
        "nombre": "Entrega final / Aceptación técnica",
        "agentes_obligatorios": ["A1_SPONSOR"],
        "es_candado_duro": False
    },
    "F6": {
        "nombre": "VBC Fiscal/Legal",
        "agentes_obligatorios": ["A3_FISCAL", "A4_LEGAL"],
        "es_candado_duro": True,
        "descripcion_candado": "No puede emitirse CFDI/pago sin VBC de Fiscal y Legal"
    },
    "F7": {
        "nombre": "Auditoría interna",
        "agentes_obligatorios": ["A2_PMO"],
        "es_candado_duro": False
    },
    "F8": {
        "nombre": "CFDI y pago",
        "agentes_obligatorios": ["A5_FINANZAS"],
        "es_candado_duro": True,
        "descripcion_candado": "No puede liberarse pago sin 3-way match validado"
    },
    "F9": {
        "nombre": "Post-implementación",
        "agentes_obligatorios": ["A1_SPONSOR"],
        "es_candado_duro": False
    }
}


def es_candado_duro(fase: str) -> bool:
    """Verifica si una fase es un candado duro"""
    return fase in CANDADOS_DUROS


def get_siguiente_fase(fase_actual: str) -> Optional[str]:
    """Obtiene la siguiente fase en el flujo"""
    if fase_actual not in ORDEN_FASES:
        return None
    index = ORDEN_FASES.index(fase_actual)
    if index >= len(ORDEN_FASES) - 1:
        return None
    return ORDEN_FASES[index + 1]


def get_fase_anterior(fase_actual: str) -> Optional[str]:
    """Obtiene la fase anterior en el flujo"""
    if fase_actual not in ORDEN_FASES:
        return None
    index = ORDEN_FASES.index(fase_actual)
    if index <= 0:
        return None
    return ORDEN_FASES[index - 1]


def get_config_fase(fase: str) -> Optional[Dict[str, Any]]:
    """Obtiene la configuración de una fase"""
    return FASES_CONFIG.get(fase)


def verificar_candado_f2(proyecto: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    CANDADO F2: No iniciar ejecución sin aprobación completa
    
    Verifica:
    1. F0 y F1 deben estar completadas
    2. Presupuesto debe estar confirmado (A5)
    3. Si requiere revisión humana por umbral, debe estar obtenida
    4. A1 y A3 deben haber aprobado en F0
    """
    resultado = {
        "liberado": False,
        "bloqueos": [],
        "fase": "F2",
        "tipo_candado": "INICIO_EJECUCION"
    }
    
    fases_completadas = context.get("fases_completadas", [])
    deliberaciones = context.get("deliberaciones", {})
    
    if "F0" not in fases_completadas:
        resultado["bloqueos"].append("CANDADO F2: F0 (Aprobación BEE) no está completada")
    
    if "F1" not in fases_completadas:
        resultado["bloqueos"].append("CANDADO F2: F1 (SOW) no está completada")
    
    delib_finanzas = deliberaciones.get("F2", {}).get("A5_FINANZAS")
    if not delib_finanzas or delib_finanzas.get("decision") != "APROBAR":
        resultado["bloqueos"].append("CANDADO F2: Finanzas no ha confirmado presupuesto")
    
    monto = proyecto.get("monto", 0)
    risk_score = proyecto.get("risk_score_total", 0)
    
    if monto >= 5_000_000 or risk_score >= 60:
        if not proyecto.get("revision_humana_obtenida", False):
            resultado["bloqueos"].append(
                f"CANDADO F2: Proyecto requiere revisión humana (monto=${monto:,.0f}, risk_score={risk_score}) y no se ha obtenido"
            )
    
    delib_a1_f0 = deliberaciones.get("F0", {}).get("A1_SPONSOR")
    delib_a3_f0 = deliberaciones.get("F0", {}).get("A3_FISCAL")
    
    if not delib_a1_f0 or delib_a1_f0.get("decision") not in ["APROBAR", "APROBAR_CONDICIONES"]:
        resultado["bloqueos"].append("CANDADO F2: A1-Sponsor no ha aprobado el proyecto")
    
    if not delib_a3_f0 or delib_a3_f0.get("decision") not in ["APROBAR", "APROBAR_CONDICIONES"]:
        resultado["bloqueos"].append("CANDADO F2: A3-Fiscal no ha aprobado el proyecto")
    
    resultado["liberado"] = len(resultado["bloqueos"]) == 0
    return resultado


def verificar_candado_f6(proyecto: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    CANDADO F6: No emitir VBC ni autorizar pago sin evidencia completa
    
    Verifica:
    1. F5 debe estar completada (entrega aceptada)
    2. Matriz de materialidad debe tener > 80% completitud
    3. VBC Fiscal debe estar emitido
    4. VBC Legal debe estar emitido
    5. A3 y A4 deben tener decisión APROBAR en F6
    6. Si es intra-grupo, verificar estudio TP vigente
    """
    resultado = {
        "liberado": False,
        "bloqueos": [],
        "fase": "F6",
        "tipo_candado": "VBC_FISCAL_LEGAL"
    }
    
    fases_completadas = context.get("fases_completadas", [])
    deliberaciones = context.get("deliberaciones", {})
    defense_file = context.get("defense_file", {})
    proveedor = context.get("proveedor", {})
    documentos = context.get("documentos", [])
    
    if "F5" not in fases_completadas:
        resultado["bloqueos"].append("CANDADO F6: F5 (Aceptación técnica) no está completada")
    
    completitud = defense_file.get("matriz_materialidad_completitud", 0)
    if completitud < 80:
        resultado["bloqueos"].append(
            f"CANDADO F6: Matriz de materialidad incompleta ({completitud}% vs 80% requerido)"
        )
    
    if not defense_file.get("vbc_fiscal_emitido", False):
        resultado["bloqueos"].append("CANDADO F6: VBC Fiscal no ha sido emitido")
    
    if not defense_file.get("vbc_legal_emitido", False):
        resultado["bloqueos"].append("CANDADO F6: VBC Legal no ha sido emitido")
    
    delib_a3_f6 = deliberaciones.get("F6", {}).get("A3_FISCAL")
    delib_a4_f6 = deliberaciones.get("F6", {}).get("A4_LEGAL")
    
    if not delib_a3_f6 or delib_a3_f6.get("decision") != "APROBAR":
        resultado["bloqueos"].append("CANDADO F6: A3-Fiscal no ha dado aprobación final")
    
    if not delib_a4_f6 or delib_a4_f6.get("decision") != "APROBAR":
        resultado["bloqueos"].append("CANDADO F6: A4-Legal no ha dado aprobación final")
    
    tipo_relacion = proveedor.get("tipo_relacion", "TERCERO_INDEPENDIENTE")
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        tiene_tp = any(d.get("tipo") == "ESTUDIO_TP" for d in documentos)
        if not tiene_tp:
            resultado["bloqueos"].append("CANDADO F6: Operación con parte relacionada sin estudio de TP")
    
    resultado["liberado"] = len(resultado["bloqueos"]) == 0
    return resultado


def verificar_candado_f8(proyecto: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    CANDADO F8: No liberar pago sin 3-way match
    
    Verifica:
    1. F6 y F7 deben estar completadas
    2. CFDI debe existir y tener descripción específica
    3. 3-way match: Contrato vs CFDI vs Monto
    4. A5-Finanzas debe aprobar en F8
    """
    resultado = {
        "liberado": False,
        "bloqueos": [],
        "fase": "F8",
        "tipo_candado": "PAGO_3WAY_MATCH"
    }
    
    fases_completadas = context.get("fases_completadas", [])
    deliberaciones = context.get("deliberaciones", {})
    documentos = context.get("documentos", [])
    
    if "F6" not in fases_completadas:
        resultado["bloqueos"].append("CANDADO F8: F6 (VBC) no está completada")
    
    if "F7" not in fases_completadas:
        resultado["bloqueos"].append("CANDADO F8: F7 (Auditoría interna) no está completada")
    
    cfdi = next((d for d in documentos if d.get("tipo") == "CFDI"), None)
    contrato = next((d for d in documentos if d.get("tipo") == "CONTRATO"), None)
    
    if not cfdi:
        resultado["bloqueos"].append("CANDADO F8: No se ha cargado CFDI")
    else:
        descripcion_cfdi = cfdi.get("metadata", {}).get("descripcion", "").lower()
        palabras_genericas = [
            "servicios profesionales varios",
            "servicios generales",
            "honorarios profesionales",
            "asesoría general",
            "servicios de consultoría"
        ]
        
        es_generico = any(palabra in descripcion_cfdi for palabra in palabras_genericas)
        if es_generico:
            resultado["bloqueos"].append(
                "CANDADO F8: CFDI tiene descripción genérica - debe ser específico"
            )
    
    if cfdi and contrato:
        monto_cfdi = cfdi.get("metadata", {}).get("monto", 0)
        monto_contrato = contrato.get("metadata", {}).get("monto", proyecto.get("monto", 0))
        
        if monto_contrato > 0:
            diferencia = abs(monto_cfdi - monto_contrato) / monto_contrato
            if diferencia > 0.05:
                resultado["bloqueos"].append(
                    f"CANDADO F8: 3-way match fallido - CFDI: ${monto_cfdi:,.0f} vs Contrato: ${monto_contrato:,.0f}"
                )
    
    delib_a5_f8 = deliberaciones.get("F8", {}).get("A5_FINANZAS")
    if not delib_a5_f8 or delib_a5_f8.get("decision") != "APROBAR":
        resultado["bloqueos"].append("CANDADO F8: A5-Finanzas no ha validado el 3-way match")
    
    resultado["liberado"] = len(resultado["bloqueos"]) == 0
    return resultado


def verificar_avance_fase_completo(
    proyecto: Dict[str, Any],
    fase_destino: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verifica si un proyecto puede avanzar a la siguiente fase.
    Incluye: candados duros + checklist por tipología.
    """
    tipologia = proyecto.get("tipologia", "")
    fase_actual = proyecto.get("fase_actual", "F0")
    bloqueos = []
    
    if fase_destino == "F2":
        resultado = verificar_candado_f2(proyecto, context)
        if not resultado.get("liberado", False):
            bloqueos.extend(resultado.get("bloqueos", []))
    elif fase_destino == "F6":
        resultado = verificar_candado_f6(proyecto, context)
        if not resultado.get("liberado", False):
            bloqueos.extend(resultado.get("bloqueos", []))
    elif fase_destino == "F8":
        resultado = verificar_candado_f8(proyecto, context)
        if not resultado.get("liberado", False):
            bloqueos.extend(resultado.get("bloqueos", []))
    
    if tipologia:
        documentos = context.get("documentos", [])
        resultado_checklist = validar_checklist_fase(
            tipologia_id=tipologia,
            fase=fase_actual,
            documentos_cargados=documentos
        )
        
        if not resultado_checklist.get("cumple", True):
            for faltante in resultado_checklist.get("faltantes", []):
                bloqueos.append(
                    f"[CHECKLIST {tipologia}] Falta: {faltante['documento']} - "
                    f"Criterio: {faltante.get('criterio', 'N/A')}"
                )
    
    return {
        "puede_avanzar": len(bloqueos) == 0,
        "bloqueos": bloqueos,
        "fase_actual": fase_actual,
        "fase_destino": fase_destino,
        "tipologia": tipologia,
        "checklist_validado": True
    }


def puede_avanzar_fase(proyecto: Dict[str, Any], fase_actual: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función principal: Verificar si proyecto puede avanzar de fase
    
    Args:
        proyecto: Datos del proyecto
        fase_actual: Fase actual del proyecto
        context: Contexto con deliberaciones, documentos, defense_file, etc.
    
    Returns:
        Diccionario con resultado de verificación
    """
    resultado = {
        "puede_avanzar": False,
        "fase_actual": fase_actual,
        "fase_siguiente": get_siguiente_fase(fase_actual),
        "bloqueos": [],
        "advertencias": [],
        "checklist_pendiente": [],
        "requiere_revision_humana": False,
        "es_candado_duro": es_candado_duro(fase_actual)
    }
    
    config_fase = get_config_fase(fase_actual)
    if not config_fase:
        resultado["bloqueos"].append(f"Fase {fase_actual} no tiene configuración definida")
        return resultado
    
    agentes_requeridos = config_fase.get("agentes_obligatorios", [])
    deliberaciones = context.get("deliberaciones", {}).get(fase_actual, {})
    
    for agente_id in agentes_requeridos:
        delib = deliberaciones.get(agente_id)
        
        if not delib:
            resultado["bloqueos"].append(f"Falta dictamen de {agente_id} para fase {fase_actual}")
        elif delib.get("decision") == "RECHAZAR":
            resultado["bloqueos"].append(f"{agente_id} ha RECHAZADO el proyecto")
        elif delib.get("decision") == "SOLICITAR_AJUSTES":
            resultado["advertencias"].append(f"{agente_id} solicita ajustes - revisar condiciones")
        elif delib.get("decision") == "PENDIENTE":
            resultado["bloqueos"].append(f"{agente_id} aún no ha emitido decisión")
    
    if fase_actual == "F2":
        candado = verificar_candado_f2(proyecto, context)
        if not candado["liberado"]:
            resultado["bloqueos"].extend(candado["bloqueos"])
    
    if fase_actual == "F6":
        candado = verificar_candado_f6(proyecto, context)
        if not candado["liberado"]:
            resultado["bloqueos"].extend(candado["bloqueos"])
    
    if fase_actual == "F8":
        candado = verificar_candado_f8(proyecto, context)
        if not candado["liberado"]:
            resultado["bloqueos"].extend(candado["bloqueos"])
    
    monto = proyecto.get("monto", 0)
    risk_score = proyecto.get("risk_score_total", 0)
    tipologia = proyecto.get("tipologia", "")
    
    if monto >= 5_000_000:
        resultado["requiere_revision_humana"] = True
        resultado["razon_revision_humana"] = f"Monto >= $5M (${monto:,.0f})"
    elif risk_score >= 60:
        resultado["requiere_revision_humana"] = True
        resultado["razon_revision_humana"] = f"Risk score >= 60 ({risk_score})"
    elif tipologia in ["INTRAGRUPO_MANAGEMENT_FEE", "REESTRUCTURAS"]:
        resultado["requiere_revision_humana"] = True
        resultado["razon_revision_humana"] = f"Tipología de alto riesgo: {tipologia}"
    
    resultado["puede_avanzar"] = (
        len(resultado["bloqueos"]) == 0 and 
        len(resultado["checklist_pendiente"]) == 0
    )
    
    return resultado


def avanzar_fase(proyecto: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intenta avanzar el proyecto a la siguiente fase
    
    Args:
        proyecto: Datos del proyecto
        context: Contexto con deliberaciones, documentos, etc.
    
    Returns:
        Resultado del intento de avance
    """
    fase_actual = proyecto.get("fase_actual", "F0")
    verificacion = puede_avanzar_fase(proyecto, fase_actual, context)
    
    if not verificacion["puede_avanzar"]:
        return {
            "exito": False,
            "mensaje": "No se puede avanzar de fase",
            "bloqueos": verificacion["bloqueos"],
            "checklist_pendiente": verificacion["checklist_pendiente"],
            "advertencias": verificacion["advertencias"]
        }
    
    siguiente_fase = verificacion["fase_siguiente"]
    
    if not siguiente_fase:
        return {
            "exito": False,
            "mensaje": "El proyecto ya está en la última fase (F9)"
        }
    
    return {
        "exito": True,
        "mensaje": f"Proyecto puede avanzar a fase {siguiente_fase}",
        "fase_anterior": fase_actual,
        "fase_nueva": siguiente_fase,
        "advertencias": verificacion["advertencias"]
    }


def get_estado_proyecto(proyecto: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Obtiene el estado completo del proyecto en el flujo de fases
    """
    fase_actual = proyecto.get("fase_actual", "F0")
    config_fase = get_config_fase(fase_actual)
    
    verificacion = puede_avanzar_fase(proyecto, fase_actual, context)
    
    estado_candados = {
        "F2": None,
        "F6": None,
        "F8": None
    }
    
    estado_candados["F2"] = verificar_candado_f2(proyecto, context)
    estado_candados["F6"] = verificar_candado_f6(proyecto, context)
    estado_candados["F8"] = verificar_candado_f8(proyecto, context)
    
    return {
        "proyecto_id": proyecto.get("id"),
        "fase_actual": fase_actual,
        "nombre_fase": config_fase.get("nombre") if config_fase else None,
        "es_candado_duro": es_candado_duro(fase_actual),
        "puede_avanzar": verificacion["puede_avanzar"],
        "bloqueos": verificacion["bloqueos"],
        "advertencias": verificacion["advertencias"],
        "requiere_revision_humana": verificacion["requiere_revision_humana"],
        "fase_siguiente": get_siguiente_fase(fase_actual),
        "estado_candados": estado_candados
    }


def get_resumen_candados() -> Dict[str, Any]:
    """Obtiene un resumen de los tres candados duros del sistema"""
    return {
        "candados_duros": [
            {
                "fase": "F2",
                "nombre": "Inicio de Ejecución",
                "descripcion": "No puede iniciarse ejecución sin aprobación completa",
                "requisitos": [
                    "F0 y F1 completadas",
                    "Presupuesto confirmado por A5-Finanzas",
                    "A1-Sponsor y A3-Fiscal aprobaron en F0",
                    "Revisión humana si monto >= $5M o risk_score >= 60"
                ],
                "riesgo_sin_control": "Costos hundidos - trabajos sin aprobación"
            },
            {
                "fase": "F6",
                "nombre": "VBC Fiscal/Legal",
                "descripcion": "No puede emitirse CFDI sin VBC de Fiscal y Legal",
                "requisitos": [
                    "F5 (Aceptación técnica) completada",
                    "Matriz de materialidad >= 80%",
                    "VBC Fiscal emitido",
                    "VBC Legal emitido",
                    "A3-Fiscal y A4-Legal aprobaron en F6",
                    "Estudio TP si es operación intra-grupo"
                ],
                "riesgo_sin_control": "Riesgo fiscal - facturas sin sustento"
            },
            {
                "fase": "F8",
                "nombre": "Liberación de Pago",
                "descripcion": "No puede liberarse pago sin 3-way match validado",
                "requisitos": [
                    "F6 y F7 completadas",
                    "CFDI con descripción específica (no genérica)",
                    "3-way match: Contrato = CFDI = Pago (tolerancia 5%)",
                    "A5-Finanzas validó 3-way match"
                ],
                "riesgo_sin_control": "Riesgo de fraude - pagos sin validación"
            }
        ],
        "flujo_completo": ORDEN_FASES,
        "fases_config": FASES_CONFIG
    }
