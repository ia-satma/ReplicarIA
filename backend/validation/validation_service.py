"""
Servicio de Validación de Outputs de Agentes - Revisar.IA

Funciones para validar, corregir y calcular completitud de outputs de agentes.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError
import json

from .agent_schemas import AGENT_OUTPUT_SCHEMAS


def validar_output_agente(agente_id: str, output: Any) -> Dict[str, Any]:
    """
    Función principal: Validar output de agente contra su schema.
    
    Args:
        agente_id: ID del agente (A1_SPONSOR, A3_FISCAL, etc.)
        output: Output del agente (dict o string JSON)
    
    Returns:
        Diccionario con resultado de validación
    """
    schema = AGENT_OUTPUT_SCHEMAS.get(agente_id)
    
    if not schema:
        return {
            "valido": False,
            "errores": [f"No existe schema de validación para agente {agente_id}"],
            "output_original": output
        }
    
    try:
        if isinstance(output, str):
            datos = json.loads(output)
        else:
            datos = output
        
        resultado = schema.model_validate(datos)
        
        return {
            "valido": True,
            "errores": [],
            "output_validado": resultado.model_dump()
        }
        
    except json.JSONDecodeError as e:
        return {
            "valido": False,
            "errores": [f"Error parsing JSON: {str(e)}"],
            "output_original": output
        }
    except ValidationError as e:
        errores = []
        for error in e.errors():
            path = ".".join(str(p) for p in error["loc"])
            errores.append(f"{path}: {error['msg']}")
        
        return {
            "valido": False,
            "errores": errores,
            "output_original": datos if 'datos' in dir() else output
        }


def validar_y_corregir(agente_id: str, output: Any) -> Dict[str, Any]:
    """
    Validar y aplicar correcciones automáticas cuando sea posible.
    
    Args:
        agente_id: ID del agente
        output: Output del agente
    
    Returns:
        Resultado de validación con correcciones aplicadas
    """
    resultado = validar_output_agente(agente_id, output)
    
    if resultado["valido"]:
        return resultado
    
    try:
        if isinstance(output, str):
            datos = json.loads(output)
        else:
            datos = output.copy() if isinstance(output, dict) else output
    except (json.JSONDecodeError, TypeError, AttributeError):
        return resultado
    
    correcciones_aplicadas = []
    
    campos_array = [
        "checklist_evidencia_exigible",
        "condiciones_para_vbc",
        "riesgos_subsistentes",
        "condiciones_estrategicas_avance",
        "checklist_contractual",
        "alertas_riesgo_especial",
        "ajustes_requeridos",
        "clausulas_obligatorias_faltantes",
        "indicadores_exito",
        "bloqueos_activos",
        "entregables_cargados",
        "minutas_sesiones",
        "pendientes"
    ]
    
    for campo in campos_array:
        if campo in datos and not isinstance(datos[campo], list):
            datos[campo] = []
            correcciones_aplicadas.append(f"Convertido {campo} a array vacío")
    
    campos_numericos = [
        "risk_score_total",
        "riesgo_puntos_razon_negocios",
        "riesgo_puntos_beneficio_economico",
        "riesgo_puntos_trazabilidad",
        "riesgo_puntos"
    ]
    
    def corregir_numerico(obj: dict, campo: str, correcciones: list):
        if campo in obj and isinstance(obj[campo], str):
            try:
                obj[campo] = int(obj[campo])
                correcciones.append(f"Convertido {campo} de string a número")
            except (ValueError, TypeError):
                pass  # String not convertible to int, skip
    
    for campo in campos_numericos:
        corregir_numerico(datos, campo, correcciones_aplicadas)
    
    if "conclusion_por_pilar" in datos and isinstance(datos["conclusion_por_pilar"], dict):
        for pilar in ["razon_negocios", "beneficio_economico", "materialidad", "trazabilidad"]:
            if pilar in datos["conclusion_por_pilar"]:
                corregir_numerico(datos["conclusion_por_pilar"][pilar], "riesgo_puntos", correcciones_aplicadas)
    
    campos_booleanos = [
        "requiere_validacion_humana",
        "requiere_revision_humana",
        "puede_avanzar_fase",
        "presupuesto_disponible",
        "requiere_evaluacion_f9",
        "obligatorio",
        "cumplido"
    ]
    
    def corregir_booleano(obj: dict, campo: str, correcciones: list):
        if campo in obj and isinstance(obj[campo], str):
            obj[campo] = obj[campo].lower() == "true"
            correcciones.append(f"Convertido {campo} de string a boolean")
    
    for campo in campos_booleanos:
        corregir_booleano(datos, campo, correcciones_aplicadas)
    
    resultado_final = validar_output_agente(agente_id, datos)
    
    return {
        **resultado_final,
        "correcciones_aplicadas": correcciones_aplicadas
    }


def generar_template_vacio(agente_id: str) -> Optional[Dict[str, Any]]:
    """
    Genera un template vacío para un agente.
    
    Args:
        agente_id: ID del agente
    
    Returns:
        Template vacío o None si no existe el agente
    """
    templates = {
        "A1_SPONSOR": {
            "decision": "PENDIENTE",
            "analisis_razon_negocios": {
                "vinculacion_con_giro": "",
                "objetivo_economico": "",
                "conclusion": "NO_CONFORME"
            },
            "analisis_bee": {
                "objetivo_especifico": "",
                "roi_esperado": None,
                "horizonte_meses": None,
                "indicadores_exito": [],
                "evaluacion": "NO_CONFORME"
            },
            "condiciones_estrategicas_avance": [],
            "requisitos_para_sow": [],
            "riesgo_puntos_razon_negocios": 0,
            "riesgo_puntos_beneficio_economico": 0
        },
        
        "A2_PMO": {
            "estado_global_proyecto": "PENDIENTE",
            "fase_actual": "F0",
            "checklist_estado": [],
            "decisiones_agentes_resumen": {},
            "bloqueos_activos": [],
            "requiere_revision_humana": False,
            "razon_revision_humana": None,
            "siguiente_accion": "",
            "puede_avanzar_fase": False
        },
        
        "A3_FISCAL": {
            "decision": "PENDIENTE",
            "conclusion_por_pilar": {
                "razon_negocios": {"status": "NO_CONFORME", "detalle": " " * 50, "riesgo_puntos": 0},
                "beneficio_economico": {"status": "NO_CONFORME", "detalle": " " * 50, "riesgo_puntos": 0},
                "materialidad": {"status": "NO_CONFORME", "detalle": " " * 50, "riesgo_puntos": 0},
                "trazabilidad": {"status": "NO_CONFORME", "detalle": " " * 50, "riesgo_puntos": 0}
            },
            "risk_score_total": 0,
            "checklist_evidencia_exigible": [],
            "alertas_riesgo_especial": [],
            "condiciones_para_vbc": [],
            "riesgos_subsistentes": [],
            "requiere_validacion_humana": False,
            "justificacion_validacion_humana": None
        },
        
        "A4_LEGAL": {
            "decision": "SOLICITAR_AJUSTES",
            "checklist_contractual": [],
            "ajustes_requeridos": [],
            "clausulas_obligatorias_faltantes": [],
            "riesgo_puntos_trazabilidad": 0
        },
        
        "A5_FINANZAS": {
            "decision": "SOLICITAR_AJUSTES",
            "analisis_proporcion": {
                "costo_vs_ventas_porcentaje": 0,
                "evaluacion_proporcion": "RAZONABLE",
                "presupuesto_disponible": False,
                "centro_costo": ""
            },
            "evaluacion_bee": {
                "roi_evaluacion": "",
                "horizonte_evaluacion": "",
                "conclusion": "NO_CONFORME"
            },
            "condiciones_financieras": [],
            "impacto_no_deducibilidad": "",
            "requiere_evaluacion_f9": False
        },
        
        "A6_PROVEEDOR": {
            "entregables_cargados": [],
            "minutas_sesiones": [],
            "estado_avance": "",
            "pendientes": []
        }
    }
    
    return templates.get(agente_id)


def calcular_completitud(agente_id: str, output: Any) -> Dict[str, Any]:
    """
    Calcula el porcentaje de completitud de un output.
    
    Args:
        agente_id: ID del agente
        output: Output del agente
    
    Returns:
        Diccionario con métricas de completitud
    """
    try:
        if isinstance(output, str):
            datos = json.loads(output)
        else:
            datos = output
    except (json.JSONDecodeError, TypeError):
        return {
            "campos_totales": 0,
            "campos_llenos": 0,
            "porcentaje_completitud": 0
        }
    
    campos_totales = 0
    campos_llenos = 0
    
    def contar_campos(obj: Any):
        nonlocal campos_totales, campos_llenos
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                campos_totales += 1
                
                if value is None or value == "":
                    pass
                elif isinstance(value, list):
                    if len(value) > 0:
                        campos_llenos += 1
                        for item in value:
                            if isinstance(item, dict):
                                contar_campos(item)
                elif isinstance(value, dict):
                    campos_llenos += 1
                    contar_campos(value)
                else:
                    campos_llenos += 1
    
    contar_campos(datos)
    
    porcentaje = round((campos_llenos / campos_totales * 100), 1) if campos_totales > 0 else 0
    
    return {
        "campos_totales": campos_totales,
        "campos_llenos": campos_llenos,
        "porcentaje_completitud": porcentaje
    }


def obtener_campos_faltantes(agente_id: str, output: Any) -> List[str]:
    """
    Identifica los campos que faltan o están vacíos.
    
    Args:
        agente_id: ID del agente
        output: Output del agente
    
    Returns:
        Lista de campos faltantes
    """
    resultado = validar_output_agente(agente_id, output)
    
    if resultado["valido"]:
        return []
    
    return resultado.get("errores", [])
