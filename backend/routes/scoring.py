"""
Rutas de API para Scoring y Casos Modelo - Revisar.IA
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from scoring import (
    FEW_SHOT_EXAMPLES,
    RISK_SCORING_MATRIX,
    get_ejemplo,
    get_todos_ejemplos,
    calcular_risk_score,
    get_descripcion_criterio,
    get_matriz_completa,
    explicar_diferencia_scores,
    build_few_shot_section,
    build_risk_scoring_instructions
)

router = APIRouter(prefix="/api/scoring", tags=["Scoring Revisar.IA"])


class EvaluacionPilar(BaseModel):
    vinculacion_giro: int = 0
    objetivo_economico: int = 0
    coherencia_monto: int = 0


class EvaluacionBeneficio(BaseModel):
    identificacion_beneficios: int = 0
    modelo_roi: int = 0
    horizonte_temporal: int = 0


class EvaluacionMaterialidad(BaseModel):
    formalizacion: int = 0
    evidencias_ejecucion: int = 0
    coherencia_documentos: int = 0


class EvaluacionTrazabilidad(BaseModel):
    conservacion: int = 0
    integridad: int = 0
    timeline: int = 0


class EvaluacionCompleta(BaseModel):
    razon_negocios: EvaluacionPilar
    beneficio_economico: EvaluacionBeneficio
    materialidad: EvaluacionMaterialidad
    trazabilidad: EvaluacionTrazabilidad


@router.get("/few-shot")
async def get_all_few_shot_examples() -> Dict[str, Any]:
    """Obtiene todos los casos modelo (few-shot examples)"""
    return {
        "total": len(FEW_SHOT_EXAMPLES),
        "decisiones": list(FEW_SHOT_EXAMPLES.keys()),
        "ejemplos": FEW_SHOT_EXAMPLES
    }


@router.get("/few-shot/{decision}")
async def get_few_shot_example(decision: str) -> Dict[str, Any]:
    """Obtiene un caso modelo específico por tipo de decisión"""
    ejemplo = get_ejemplo(decision)
    if not ejemplo:
        raise HTTPException(
            status_code=404, 
            detail=f"Decisión '{decision}' no encontrada. Opciones: APROBAR, SOLICITAR_AJUSTES, RECHAZAR"
        )
    return ejemplo


@router.get("/matriz")
async def get_scoring_matrix() -> Dict[str, Any]:
    """Obtiene la matriz de scoring completa con los 12 criterios"""
    return get_matriz_completa()


@router.get("/matriz/{pilar}")
async def get_scoring_pilar(pilar: str) -> Dict[str, Any]:
    """Obtiene los criterios de un pilar específico"""
    pilar_upper = pilar.upper()
    pilar_config = RISK_SCORING_MATRIX.get(pilar_upper)
    if not pilar_config or pilar_upper == "descripcion":
        raise HTTPException(
            status_code=404,
            detail=f"Pilar '{pilar}' no encontrado. Opciones: RAZON_NEGOCIOS, BENEFICIO_ECONOMICO, MATERIALIDAD, TRAZABILIDAD"
        )
    return {
        "pilar": pilar_upper,
        "config": pilar_config
    }


@router.post("/calcular")
async def calcular_score(evaluacion: EvaluacionCompleta) -> Dict[str, Any]:
    """
    Calcula el risk_score objetivo basado en la evaluación de los 12 criterios.
    
    Rangos de puntaje:
    - 0-39: BAJO riesgo
    - 40-59: MEDIO riesgo  
    - 60-79: ALTO riesgo (requiere revisión humana)
    - 80-100: CRÍTICO (considerar rechazo)
    """
    try:
        resultado = calcular_risk_score({
            "razon_negocios": evaluacion.razon_negocios.model_dump(),
            "beneficio_economico": evaluacion.beneficio_economico.model_dump(),
            "materialidad": evaluacion.materialidad.model_dump(),
            "trazabilidad": evaluacion.trazabilidad.model_dump()
        })
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/criterio/{pilar}/{criterio}/{puntos}")
async def get_criterio_descripcion(pilar: str, criterio: str, puntos: int) -> Dict[str, Any]:
    """
    Obtiene la descripción y ejemplo para un puntaje específico de un criterio.
    
    Pilares: RAZON_NEGOCIOS, BENEFICIO_ECONOMICO, MATERIALIDAD, TRAZABILIDAD
    """
    descripcion = get_descripcion_criterio(pilar.upper(), criterio, puntos)
    if not descripcion:
        raise HTTPException(
            status_code=404,
            detail=f"Criterio '{criterio}' no encontrado en pilar '{pilar}'"
        )
    return {
        "pilar": pilar.upper(),
        "criterio": criterio,
        "puntos": puntos,
        "descripcion": descripcion
    }


@router.get("/explicar/{score_alto}/{score_bajo}")
async def explicar_diferencia(
    score_alto: int, 
    score_bajo: int,
    rn_alto: int = 0, be_alto: int = 0, mat_alto: int = 0, tra_alto: int = 0,
    rn_bajo: int = 0, be_bajo: int = 0, mat_bajo: int = 0, tra_bajo: int = 0
) -> Dict[str, Any]:
    """
    Explica la diferencia entre dos risk_scores.
    
    Ejemplo: /api/scoring/explicar/68/22?rn_alto=15&be_alto=18&mat_alto=20&tra_alto=15&rn_bajo=3&be_bajo=5&mat_bajo=8&tra_bajo=6
    """
    desglose_alto = {
        "razon_negocios": rn_alto,
        "beneficio_economico": be_alto,
        "materialidad": mat_alto,
        "trazabilidad": tra_alto
    }
    desglose_bajo = {
        "razon_negocios": rn_bajo,
        "beneficio_economico": be_bajo,
        "materialidad": mat_bajo,
        "trazabilidad": tra_bajo
    }
    
    explicacion = explicar_diferencia_scores(score_alto, score_bajo, desglose_alto, desglose_bajo)
    
    return {
        "score_alto": score_alto,
        "score_bajo": score_bajo,
        "diferencia": score_alto - score_bajo,
        "explicacion": explicacion
    }


@router.get("/instrucciones")
async def get_scoring_instructions() -> Dict[str, str]:
    """Obtiene las instrucciones de scoring para usar en prompts de agentes"""
    return {
        "instrucciones": build_risk_scoring_instructions()
    }


@router.get("/few-shot-prompt")
async def get_few_shot_prompt(incluir_todos: bool = True) -> Dict[str, str]:
    """Obtiene la sección few-shot formateada para incluir en prompts"""
    return {
        "section": build_few_shot_section(incluir_todos)
    }


@router.get("/resumen-casos")
async def get_resumen_casos() -> Dict[str, Any]:
    """Obtiene un resumen de los 3 casos modelo con sus características clave"""
    return {
        "casos": [
            {
                "decision": "APROBAR",
                "nombre": FEW_SHOT_EXAMPLES["APROBAR"]["metadata"]["nombre"],
                "tipologia": FEW_SHOT_EXAMPLES["APROBAR"]["metadata"]["tipologia"],
                "monto": FEW_SHOT_EXAMPLES["APROBAR"]["metadata"]["monto"],
                "risk_score": FEW_SHOT_EXAMPLES["APROBAR"]["risk_score"]["total"],
                "caracteristicas": [
                    "Razón de negocios vinculada claramente al giro",
                    "ROI documentado con metodología",
                    "Entregables tangibles y específicos",
                    "Timeline reconstruible con fechas"
                ]
            },
            {
                "decision": "SOLICITAR_AJUSTES",
                "nombre": FEW_SHOT_EXAMPLES["SOLICITAR_AJUSTES"]["metadata"]["nombre"],
                "tipologia": FEW_SHOT_EXAMPLES["SOLICITAR_AJUSTES"]["metadata"]["tipologia"],
                "monto": FEW_SHOT_EXAMPLES["SOLICITAR_AJUSTES"]["metadata"]["monto"],
                "risk_score": FEW_SHOT_EXAMPLES["SOLICITAR_AJUSTES"]["risk_score"]["total"],
                "caracteristicas": [
                    "Objetivo genérico sin métricas concretas",
                    "Sin ROI cuantificado",
                    "SOW sin entregables específicos",
                    "Sin contrato formalizado"
                ]
            },
            {
                "decision": "RECHAZAR",
                "nombre": FEW_SHOT_EXAMPLES["RECHAZAR"]["metadata"]["nombre"],
                "tipologia": FEW_SHOT_EXAMPLES["RECHAZAR"]["metadata"]["tipologia"],
                "monto": FEW_SHOT_EXAMPLES["RECHAZAR"]["metadata"]["monto"],
                "risk_score": FEW_SHOT_EXAMPLES["RECHAZAR"]["risk_score"]["total"],
                "caracteristicas": [
                    "Sin razón de negocios identificable",
                    "Solo beneficio fiscal aparente",
                    "Sin evidencia de ejecución",
                    "Señales de EFOS/simulación"
                ]
            }
        ]
    }
