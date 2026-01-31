"""
subagent_routes.py - API Routes para Ejecución de Subagentes

Endpoints para ejecutar los subagentes especializados:
- S1_TIPIFICACION: Clasificar tipo de servicio
- S2_MATERIALIDAD: Evaluar evidencia de materialidad
- S3_RIESGOS: Calcular score de riesgo fiscal
- Análisis completo coordinado

Fecha: 2026-01-31
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subagents", tags=["Subagents Execution"])


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class TipificacionRequest(BaseModel):
    descripcion_servicio: str = Field(..., min_length=10)
    monto: float = Field(..., ge=0)
    proveedor: Dict[str, Any] = Field(default={})
    contexto_adicional: Optional[Dict] = None


class MaterialidadRequest(BaseModel):
    documentos: List[Dict[str, Any]] = Field(...)
    tipo_servicio: Optional[str] = None
    monto: float = Field(..., ge=0)
    fechas: Optional[Dict[str, str]] = None


class RiesgosRequest(BaseModel):
    proyecto: Dict[str, Any] = Field(...)
    materialidad_score: float = Field(..., ge=0, le=100)
    proveedor: Dict[str, Any] = Field(...)
    tipo_servicio: Optional[str] = None


class AnalisisCompletoRequest(BaseModel):
    proyecto: Dict[str, Any] = Field(...)
    documentos: List[Dict[str, Any]] = Field(...)
    proveedor: Dict[str, Any] = Field(...)


# ============================================================================
# ENDPOINTS DE SUBAGENTES
# ============================================================================

@router.post("/tipificacion")
async def ejecutar_tipificacion(request: TipificacionRequest):
    """
    Ejecutar S1_TIPIFICACION - Clasificar tipo de servicio intangible.

    Clasifica el servicio según su naturaleza y determina los requisitos
    de materialidad correspondientes.
    """
    try:
        from ..services.subagent_executor import get_subagent_executor
        executor = await get_subagent_executor()

        result = await executor.ejecutar_tipificacion(
            descripcion_servicio=request.descripcion_servicio,
            monto=request.monto,
            proveedor=request.proveedor,
            contexto_adicional=request.contexto_adicional
        )

        return {
            "success": True,
            "subagent": "S1_TIPIFICACION",
            "result": {
                "tipo_servicio": result.tipo_servicio.value,
                "subtipo": result.subtipo,
                "confianza": result.confianza,
                "requisitos_materialidad": result.requisitos_materialidad,
                "documentos_esperados": result.documentos_esperados,
                "risk_level": result.risk_level.value,
                "justificacion": result.justificacion
            }
        }

    except Exception as e:
        logger.error(f"Error in tipificacion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/materialidad")
async def ejecutar_materialidad(request: MaterialidadRequest):
    """
    Ejecutar S2_MATERIALIDAD - Evaluar evidencia de materialidad.

    Evalúa la evidencia de materialidad según el criterio del SAT:
    - ANTES: Evidencia previa a la ejecución
    - DURANTE: Evidencia de ejecución
    - DESPUÉS: Evidencia de conclusión y entrega
    """
    try:
        from ..services.subagent_executor import get_subagent_executor, TipoServicio
        executor = await get_subagent_executor()

        tipo = None
        if request.tipo_servicio:
            try:
                tipo = TipoServicio(request.tipo_servicio)
            except ValueError:
                tipo = TipoServicio.OTRO

        result = await executor.ejecutar_materialidad(
            documentos=request.documentos,
            tipo_servicio=tipo,
            monto=request.monto,
            fechas=request.fechas
        )

        return {
            "success": True,
            "subagent": "S2_MATERIALIDAD",
            "result": {
                "score_materialidad": result.score_materialidad,
                "evidencia_antes": result.evidencia_antes,
                "evidencia_durante": result.evidencia_durante,
                "evidencia_despues": result.evidencia_despues,
                "gaps": result.gaps,
                "fortalezas": result.fortalezas,
                "recomendaciones": result.recomendaciones,
                "nivel_confianza": result.nivel_confianza
            }
        }

    except Exception as e:
        logger.error(f"Error in materialidad: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/riesgos")
async def ejecutar_riesgos(request: RiesgosRequest):
    """
    Ejecutar S3_RIESGOS - Calcular score de riesgo fiscal.

    Calcula el score de riesgo fiscal considerando múltiples factores.
    """
    try:
        from ..services.subagent_executor import get_subagent_executor, TipoServicio
        executor = await get_subagent_executor()

        tipo = None
        if request.tipo_servicio:
            try:
                tipo = TipoServicio(request.tipo_servicio)
            except ValueError:
                tipo = None

        result = await executor.ejecutar_riesgos(
            proyecto=request.proyecto,
            materialidad_score=request.materialidad_score,
            proveedor=request.proveedor,
            tipo_servicio=tipo
        )

        return {
            "success": True,
            "subagent": "S3_RIESGOS",
            "result": {
                "risk_score": result.risk_score,
                "risk_level": result.risk_level.value,
                "factores_riesgo": result.factores_riesgo,
                "mitigaciones": result.mitigaciones,
                "probabilidad_rechazo": result.probabilidad_rechazo,
                "impacto_fiscal": result.impacto_fiscal,
                "recomendacion_general": result.recomendacion_general
            }
        }

    except Exception as e:
        logger.error(f"Error in riesgos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analisis-completo")
async def ejecutar_analisis_completo(request: AnalisisCompletoRequest):
    """
    Ejecutar análisis completo con todos los subagentes.

    Coordina la ejecución de S1, S2 y S3 para un análisis integral
    del proyecto.
    """
    try:
        from ..services.subagent_executor import get_subagent_executor
        executor = await get_subagent_executor()

        result = await executor.ejecutar_analisis_completo(
            proyecto=request.proyecto,
            documentos=request.documentos,
            proveedor=request.proveedor
        )

        return {
            "success": True,
            "analysis": result
        }

    except Exception as e:
        logger.error(f"Error in analisis completo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE INFORMACIÓN
# ============================================================================

@router.get("/tipos-servicio")
async def get_tipos_servicio():
    """Obtener lista de tipos de servicio disponibles."""
    from ..services.subagent_executor import TipoServicio

    return {
        "success": True,
        "tipos": [
            {
                "value": t.value,
                "name": t.name,
                "description": _get_tipo_description(t)
            }
            for t in TipoServicio
        ]
    }


@router.get("/niveles-riesgo")
async def get_niveles_riesgo():
    """Obtener descripción de niveles de riesgo."""
    from ..services.subagent_executor import NivelRiesgo

    descriptions = {
        NivelRiesgo.BAJO: "Deducción segura. Score 0-30.",
        NivelRiesgo.MEDIO: "Deducción viable con documentación adecuada. Score 31-60.",
        NivelRiesgo.ALTO: "Riesgo significativo. Requiere fortalecimiento. Score 61-80.",
        NivelRiesgo.CRITICO: "No proceder hasta resolver factores críticos. Score 81-100."
    }

    return {
        "success": True,
        "niveles": [
            {
                "value": n.value,
                "name": n.name,
                "description": descriptions[n],
                "score_range": _get_score_range(n)
            }
            for n in NivelRiesgo
        ]
    }


def _get_tipo_description(tipo) -> str:
    """Obtener descripción de un tipo de servicio."""
    descriptions = {
        "INVESTIGACION": "Estudios de mercado, análisis competitivo, investigación de industria",
        "DESARROLLO": "Desarrollo de productos, innovación, prototipos",
        "CONSULTORIA": "Asesoría estratégica, diagnósticos, planes de mejora",
        "AUDITORIA": "Revisiones, dictámenes, verificaciones",
        "CAPACITACION": "Cursos, talleres, programas de formación",
        "ASESORIA_LEGAL": "Servicios jurídicos, contratos, litigios",
        "ASESORIA_FISCAL": "Planeación fiscal, cumplimiento tributario",
        "SOFTWARE": "Desarrollo de sistemas, implementaciones tecnológicas",
        "MARKETING": "Publicidad, branding, campañas digitales",
        "TECNOLOGIA": "Infraestructura IT, cloud, implementaciones",
        "OTRO": "Otros servicios intangibles"
    }
    return descriptions.get(tipo.value, "Servicio intangible")


def _get_score_range(nivel) -> Dict[str, int]:
    """Obtener rango de scores para un nivel de riesgo."""
    ranges = {
        "BAJO": {"min": 0, "max": 30},
        "MEDIO": {"min": 31, "max": 60},
        "ALTO": {"min": 61, "max": 80},
        "CRITICO": {"min": 81, "max": 100}
    }
    return ranges.get(nivel.value, {"min": 0, "max": 100})
