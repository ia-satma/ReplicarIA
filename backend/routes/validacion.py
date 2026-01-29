"""
Rutas de API para Validación de Outputs de Agentes - Revisar.IA
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Auth dependency for protected routes
from services.auth_service import get_current_user

from validation import (
    AGENT_OUTPUT_SCHEMAS,
    validar_output_agente,
    validar_y_corregir,
    generar_template_vacio,
    calcular_completitud,
    obtener_campos_faltantes
)

router = APIRouter(prefix="/api/validacion", tags=["Validación Revisar.IA"])


class ValidarOutputRequest(BaseModel):
    agente_id: str
    output: Dict[str, Any]


class DeliberacionRequest(BaseModel):
    proyecto_id: str
    fase: str
    agente: str
    decision: str
    analisis_completo: Optional[str] = None
    analisis_estructurado: Dict[str, Any]


@router.get("/schemas")
async def get_schemas_disponibles() -> Dict[str, Any]:
    """Lista todos los schemas de validación disponibles"""
    schemas_info = {}
    for agente_id in AGENT_OUTPUT_SCHEMAS.keys():
        template = generar_template_vacio(agente_id)
        schemas_info[agente_id] = {
            "campos_requeridos": list(template.keys()) if template else [],
            "template": template
        }
    
    return {
        "total_agentes": len(AGENT_OUTPUT_SCHEMAS),
        "agentes": list(AGENT_OUTPUT_SCHEMAS.keys()),
        "schemas": schemas_info
    }


@router.get("/template/{agente_id}")
async def get_template_agente(agente_id: str) -> Dict[str, Any]:
    """Obtiene el template vacío para un agente específico"""
    agente_upper = agente_id.upper()
    template = generar_template_vacio(agente_upper)
    
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Agente '{agente_id}' no encontrado. Opciones: {list(AGENT_OUTPUT_SCHEMAS.keys())}"
        )
    
    return {
        "agente": agente_upper,
        "template": template,
        "instruccion": "Complete todos los campos antes de enviar la deliberación"
    }


@router.post("/validar")
async def validar_output(request: ValidarOutputRequest, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Valida el output de un agente contra su schema.
    
    Retorna errores si el output no cumple con el schema.
    """
    resultado = validar_output_agente(request.agente_id.upper(), request.output)
    
    if not resultado["valido"]:
        return {
            "valido": False,
            "errores": resultado["errores"],
            "mensaje": f"El output del agente {request.agente_id} no es válido",
            "output_recibido": resultado.get("output_original")
        }
    
    completitud = calcular_completitud(request.agente_id.upper(), resultado["output_validado"])
    
    return {
        "valido": True,
        "errores": [],
        "output_validado": resultado["output_validado"],
        "completitud": completitud
    }


@router.post("/validar-y-corregir")
async def validar_y_corregir_output(request: ValidarOutputRequest, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Valida el output y aplica correcciones automáticas cuando es posible.
    
    Correcciones automáticas:
    - Strings a números
    - Strings a booleanos
    - Valores no-array a arrays vacíos
    """
    resultado = validar_y_corregir(request.agente_id.upper(), request.output)
    
    completitud = calcular_completitud(
        request.agente_id.upper(), 
        resultado.get("output_validado", resultado.get("output_original"))
    )
    
    return {
        "valido": resultado["valido"],
        "errores": resultado["errores"],
        "output_validado": resultado.get("output_validado"),
        "output_original": resultado.get("output_original") if not resultado["valido"] else None,
        "correcciones_aplicadas": resultado.get("correcciones_aplicadas", []),
        "completitud": completitud
    }


@router.post("/completitud")
async def calcular_completitud_output(request: ValidarOutputRequest, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Calcula el porcentaje de completitud de un output"""
    completitud = calcular_completitud(request.agente_id.upper(), request.output)
    
    es_suficiente = completitud["porcentaje_completitud"] >= 50
    
    return {
        "agente": request.agente_id.upper(),
        **completitud,
        "es_suficiente": es_suficiente,
        "mensaje": "Output aceptable" if es_suficiente else "Output muy incompleto (< 50%)"
    }


@router.post("/deliberacion/validar")
async def validar_deliberacion(request: DeliberacionRequest, current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Valida una deliberación completa antes de guardarla.
    
    Verifica:
    1. Output estructurado válido
    2. Completitud >= 50%
    3. Campos obligatorios presentes
    """
    agente = request.agente.upper()
    
    resultado = validar_y_corregir(agente, request.analisis_estructurado)
    
    if not resultado["valido"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Output de agente inválido",
                "errores": resultado["errores"],
                "sugerencia": f"Revisa el schema esperado para el agente {agente}",
                "output_recibido": resultado.get("output_original")
            }
        )
    
    completitud = calcular_completitud(agente, resultado["output_validado"])
    
    if completitud["porcentaje_completitud"] < 50:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Output de agente incompleto",
                "completitud": completitud,
                "mensaje": "El análisis debe tener al menos 50% de campos completados"
            }
        )
    
    risk_score_calculado = None
    if agente == "A3_FISCAL":
        output = resultado["output_validado"]
        if "conclusion_por_pilar" in output:
            pilares = output["conclusion_por_pilar"]
            risk_score_calculado = (
                pilares["razon_negocios"]["riesgo_puntos"] +
                pilares["beneficio_economico"]["riesgo_puntos"] +
                pilares["materialidad"]["riesgo_puntos"] +
                pilares["trazabilidad"]["riesgo_puntos"]
            )
    
    requiere_validacion_humana = resultado["output_validado"].get("requiere_validacion_humana", False)
    
    return {
        "valido": True,
        "proyecto_id": request.proyecto_id,
        "fase": request.fase,
        "agente": agente,
        "decision": request.decision,
        "output_validado": resultado["output_validado"],
        "completitud": completitud,
        "correcciones_aplicadas": resultado.get("correcciones_aplicadas", []),
        "risk_score_calculado": risk_score_calculado,
        "requiere_validacion_humana": requiere_validacion_humana,
        "mensaje": "Deliberación válida y lista para guardar"
    }


@router.get("/ejemplo/a3-fiscal-invalido")
async def get_ejemplo_invalido() -> Dict[str, Any]:
    """
    Retorna un ejemplo de output A3_FISCAL inválido.
    Útil para probar que la validación rechaza outputs incompletos.
    """
    output_invalido = {
        "decision": "APROBAR"
    }
    
    resultado = validar_output_agente("A3_FISCAL", output_invalido)
    
    return {
        "descripcion": "Ejemplo de output A3_FISCAL que DEBE SER RECHAZADO",
        "output_enviado": output_invalido,
        "resultado_validacion": resultado,
        "explicacion": "Falta conclusion_por_pilar, risk_score_total, checklist_evidencia_exigible, etc."
    }


@router.get("/ejemplo/a3-fiscal-valido")
async def get_ejemplo_valido() -> Dict[str, Any]:
    """
    Retorna un ejemplo de output A3_FISCAL válido.
    Útil para probar que la validación acepta outputs completos.
    """
    output_valido = {
        "decision": "APROBAR",
        "conclusion_por_pilar": {
            "razon_negocios": {
                "status": "CONFORME",
                "detalle": "El estudio de mercado está directamente vinculado con el giro inmobiliario de la empresa y sus planes de expansión.",
                "riesgo_puntos": 3
            },
            "beneficio_economico": {
                "status": "CONFORME",
                "detalle": "ROI documentado de 2.5x con metodología clara. El beneficio esperado es razonable para el tipo de estudio.",
                "riesgo_puntos": 5
            },
            "materialidad": {
                "status": "CONFORME",
                "detalle": "Contrato firmado, entregables específicos definidos (informe, modelo paramétrico, dashboard), cronograma con hitos.",
                "riesgo_puntos": 3
            },
            "trazabilidad": {
                "status": "CONFORME",
                "detalle": "Expediente estructurado con versionamiento, timeline reconstruible, integridad documental verificable.",
                "riesgo_puntos": 5
            }
        },
        "risk_score_total": 16,
        "checklist_evidencia_exigible": [
            {"item": "SIB con objetivo definido", "obligatorio": True, "estado": "ENTREGADO", "fase_requerida": "F0"},
            {"item": "BEE con ROI estimado", "obligatorio": True, "estado": "ENTREGADO", "fase_requerida": "F0"},
            {"item": "Contrato firmado", "obligatorio": True, "estado": "ENTREGADO", "fase_requerida": "F2"}
        ],
        "alertas_riesgo_especial": [],
        "condiciones_para_vbc": [],
        "riesgos_subsistentes": [],
        "requiere_validacion_humana": False,
        "justificacion_validacion_humana": None
    }
    
    resultado = validar_output_agente("A3_FISCAL", output_valido)
    completitud = calcular_completitud("A3_FISCAL", output_valido)
    
    return {
        "descripcion": "Ejemplo de output A3_FISCAL que DEBE SER ACEPTADO",
        "output_enviado": output_valido,
        "resultado_validacion": resultado,
        "completitud": completitud,
        "explicacion": "Todos los campos obligatorios presentes con valores válidos"
    }
