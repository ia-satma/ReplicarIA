"""
============================================================
REVISAR.IA - API Routes: Oráculo Estratégico
============================================================
Endpoints para investigación profunda de empresas/proveedores.
ACCESO: Solo superadministradores.

Funciones:
- Investigación empresarial exhaustiva (14 fases)
- Due Diligence de proveedores
- Análisis PESTEL, Porter, ESG
- Documentación de materialidad SAT

INTEGRACIÓN: Puede usar Cloudflare Worker o Claude directo.
============================================================
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/oraculo-estrategico", tags=["Oráculo Estratégico (Admin)"])


# ============================================================
# VERIFICACIÓN DE SUPERADMIN
# ============================================================

async def verificar_superadmin(x_admin_token: Optional[str] = Header(None)):
    """
    Verifica que el request viene de un superadministrador.
    """
    if not x_admin_token:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Este endpoint es solo para superadministradores."
        )
    # TODO: Validar token real
    return x_admin_token


# ============================================================
# ENUMS
# ============================================================

class TipoInvestigacion(str, Enum):
    COMPLETA = "completa"
    EMPRESA = "empresa"
    INDUSTRIA = "industria"
    COMPETIDORES = "competidores"
    PESTEL = "pestel"
    PORTER = "porter"
    ESG = "esg"
    MATERIALIDAD = "materialidad"
    DUE_DILIGENCE = "due_diligence"


class NivelProfundidad(str, Enum):
    RAPIDO = "rapido"      # Solo Claude
    NORMAL = "normal"      # Claude + Perplexity
    PROFUNDO = "profundo"  # Claude + Perplexity + Scraping (14 fases)


# ============================================================
# MODELOS PYDANTIC - INPUTS
# ============================================================

class InvestigarEmpresaInput(BaseModel):
    """Input para investigación de empresa"""
    empresa: str = Field(..., description="Nombre de la empresa a investigar")
    sitio_web: Optional[str] = Field(None, description="URL del sitio web")
    sector: Optional[str] = Field(None, description="Sector/industria")
    rfc: Optional[str] = Field(None, description="RFC de la empresa")
    contexto_adicional: Optional[str] = Field(None, description="Contexto para enfocar investigación")
    tipo_investigacion: TipoInvestigacion = Field(TipoInvestigacion.COMPLETA)
    nivel_profundidad: NivelProfundidad = Field(NivelProfundidad.PROFUNDO)


class DueDiligenceInput(BaseModel):
    """Input para due diligence de proveedor"""
    empresa: str = Field(..., description="Nombre del proveedor")
    rfc: str = Field(..., description="RFC del proveedor")
    sitio_web: Optional[str] = Field(None)
    monto_operacion: Optional[float] = Field(None, description="Monto de la operación en MXN")
    tipo_servicio: Optional[str] = Field(None, description="Tipo de servicio a contratar")
    proyecto_id: Optional[str] = Field(None, description="ID del proyecto relacionado")


class MaterialidadInput(BaseModel):
    """Input para documentación de materialidad SAT"""
    empresa: str = Field(..., description="Nombre del proveedor")
    rfc: str = Field(..., description="RFC del proveedor")
    servicio_contratado: str = Field(..., description="Descripción del servicio")
    monto: float = Field(..., description="Monto de la operación")
    sitio_web: Optional[str] = Field(None)
    documentos_existentes: Optional[List[str]] = Field(default_factory=list)
    proyecto_id: Optional[str] = Field(None)


class AnalisisEspecificoInput(BaseModel):
    """Input para análisis específico (PESTEL, Porter, ESG)"""
    empresa: str
    sector: str
    tipo_analisis: TipoInvestigacion
    pais: str = Field("México")


# ============================================================
# MODELOS PYDANTIC - OUTPUTS
# ============================================================

class InvestigacionResult(BaseModel):
    """Resultado de investigación"""
    success: bool
    empresa: str
    timestamp: str
    tipo_investigacion: str
    nivel_profundidad: str
    resumen_ejecutivo: Optional[str] = None
    perfil_empresa: Optional[Dict[str, Any]] = None
    analisis_industria: Optional[Dict[str, Any]] = None
    analisis_pestel: Optional[Dict[str, Any]] = None
    analisis_porter: Optional[Dict[str, Any]] = None
    analisis_esg: Optional[Dict[str, Any]] = None
    competidores: Optional[List[Dict[str, Any]]] = None
    riesgos: Optional[List[Dict[str, Any]]] = None
    oportunidades: Optional[List[str]] = None
    score_confianza: Optional[int] = None
    fuentes_consultadas: Optional[int] = None
    error: Optional[str] = None


class DueDiligenceResult(BaseModel):
    """Resultado de due diligence"""
    success: bool
    empresa: str
    rfc: str
    timestamp: str
    evaluacion_riesgo: Dict[str, Any]
    banderas_rojas: List[str]
    apto_para_operacion: Dict[str, Any]
    recomendaciones: List[str]
    investigacion_respaldo: Optional[str] = None
    error: Optional[str] = None


class MaterialidadResult(BaseModel):
    """Resultado de documentación de materialidad"""
    success: bool
    empresa: str
    rfc: str
    servicio: str
    monto: float
    timestamp: str
    score_materialidad: int
    pilares_documentados: Dict[str, Any]
    documentos_sugeridos: List[str]
    riesgos_identificados: List[Dict[str, Any]]
    conclusion: str
    error: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/investigar", response_model=InvestigacionResult)
async def investigar_empresa(
    input: InvestigarEmpresaInput,
    background_tasks: BackgroundTasks,
    admin: str = Depends(verificar_superadmin)
):
    """
    🔮 Ejecuta investigación empresarial profunda.

    Dependiendo del nivel de profundidad:
    - RAPIDO: Solo análisis con Claude (~30 segundos)
    - NORMAL: Claude + Perplexity (~1-2 minutos)
    - PROFUNDO: 14 fases completas (~3-5 minutos)
    """
    logger.info(f"Oráculo: Investigando {input.empresa} ({input.tipo_investigacion.value})")

    try:
        # Intentar usar el Worker de Cloudflare si está configurado
        worker_url = os.getenv("ORACULO_WORKER_URL")

        if worker_url and input.nivel_profundidad == NivelProfundidad.PROFUNDO:
            # Usar Cloudflare Worker para investigación profunda
            from services.oraculo_estrategico_service import oraculo_estrategico_service

            resultado = await oraculo_estrategico_service.investigar_completo(
                empresa=input.empresa,
                sitio_web=input.sitio_web,
                sector=input.sector,
                contexto_adicional=input.contexto_adicional
            )

            if resultado.get("success"):
                consolidado = resultado.get("consolidado", {})
                return InvestigacionResult(
                    success=True,
                    empresa=input.empresa,
                    timestamp=datetime.utcnow().isoformat(),
                    tipo_investigacion=input.tipo_investigacion.value,
                    nivel_profundidad=input.nivel_profundidad.value,
                    resumen_ejecutivo=consolidado.get("resumen_ejecutivo"),
                    perfil_empresa=consolidado.get("perfil_empresa"),
                    analisis_industria=consolidado.get("analisis_sector"),
                    analisis_pestel={"contenido": consolidado.get("pestel")},
                    analisis_porter={"contenido": consolidado.get("porter")},
                    analisis_esg={"contenido": consolidado.get("esg")},
                    riesgos=[{"descripcion": r} for r in (consolidado.get("riesgos") or "").split("\n") if r],
                    score_confianza=consolidado.get("score_confianza"),
                    fuentes_consultadas=consolidado.get("fuentes", {}).get("perplexity", 0)
                )
            else:
                raise Exception(resultado.get("error", "Error en Worker"))

        else:
            # Usar investigación local (Claude directo)
            resultado = await _investigar_con_claude_local(input)
            return resultado

    except Exception as e:
        logger.error(f"Error en investigación: {e}")
        return InvestigacionResult(
            success=False,
            empresa=input.empresa,
            timestamp=datetime.utcnow().isoformat(),
            tipo_investigacion=input.tipo_investigacion.value,
            nivel_profundidad=input.nivel_profundidad.value,
            error=str(e)
        )


@router.post("/due-diligence", response_model=DueDiligenceResult)
async def ejecutar_due_diligence(
    input: DueDiligenceInput,
    admin: str = Depends(verificar_superadmin)
):
    """
    🔍 Ejecuta Due Diligence completo de un proveedor.

    Incluye:
    - Investigación empresarial
    - Evaluación de riesgo
    - Identificación de banderas rojas
    - Verificación de capacidad operativa
    - Recomendaciones
    """
    logger.info(f"Oráculo DD: {input.empresa} (RFC: {input.rfc})")

    try:
        from services.oraculo_estrategico_service import oraculo_estrategico_service

        resultado = await oraculo_estrategico_service.due_diligence_proveedor(
            empresa=input.empresa,
            rfc=input.rfc,
            sitio_web=input.sitio_web,
            monto_operacion=input.monto_operacion,
            tipo_servicio=input.tipo_servicio
        )

        if resultado.get("success"):
            dd = resultado.get("due_diligence", {})
            return DueDiligenceResult(
                success=True,
                empresa=input.empresa,
                rfc=input.rfc,
                timestamp=datetime.utcnow().isoformat(),
                evaluacion_riesgo=dd.get("evaluacion_riesgo", {}),
                banderas_rojas=dd.get("banderas_rojas", []),
                apto_para_operacion=dd.get("apto_para_operacion", {}),
                recomendaciones=dd.get("recomendaciones", []),
                investigacion_respaldo=resultado.get("consolidado", {}).get("resumen_ejecutivo")
            )
        else:
            raise Exception(resultado.get("error", "Error en due diligence"))

    except Exception as e:
        logger.error(f"Error en due diligence: {e}")
        return DueDiligenceResult(
            success=False,
            empresa=input.empresa,
            rfc=input.rfc,
            timestamp=datetime.utcnow().isoformat(),
            evaluacion_riesgo={},
            banderas_rojas=[],
            apto_para_operacion={"apto": False, "motivo": str(e)},
            recomendaciones=[],
            error=str(e)
        )


@router.post("/materialidad", response_model=MaterialidadResult)
async def documentar_materialidad(
    input: MaterialidadInput,
    admin: str = Depends(verificar_superadmin)
):
    """
    📋 Genera documentación de materialidad para SAT.

    Documenta los 5 pilares:
    1. Razón de negocios
    2. Capacidad operativa del proveedor
    3. Proporcionalidad económica
    4. Evidencia de ejecución
    5. Consistencia documental
    """
    logger.info(f"Oráculo Materialidad: {input.empresa} - {input.servicio_contratado}")

    try:
        from services.oraculo_estrategico_service import oraculo_estrategico_service

        resultado = await oraculo_estrategico_service.documentar_materialidad(
            empresa=input.empresa,
            rfc=input.rfc,
            servicio_contratado=input.servicio_contratado,
            monto=input.monto,
            sitio_web=input.sitio_web,
            documentos_soporte=input.documentos_existentes
        )

        if resultado.get("success"):
            mat = resultado.get("materialidad_sat", {})
            return MaterialidadResult(
                success=True,
                empresa=input.empresa,
                rfc=input.rfc,
                servicio=input.servicio_contratado,
                monto=input.monto,
                timestamp=datetime.utcnow().isoformat(),
                score_materialidad=mat.get("score_materialidad", 0),
                pilares_documentados=mat.get("pilares_documentados", {}),
                documentos_sugeridos=mat.get("documentos_sugeridos", []),
                riesgos_identificados=mat.get("riesgos_identificados", []),
                conclusion=mat.get("conclusion", "")
            )
        else:
            raise Exception(resultado.get("error", "Error en materialidad"))

    except Exception as e:
        logger.error(f"Error en materialidad: {e}")
        return MaterialidadResult(
            success=False,
            empresa=input.empresa,
            rfc=input.rfc,
            servicio=input.servicio_contratado,
            monto=input.monto,
            timestamp=datetime.utcnow().isoformat(),
            score_materialidad=0,
            pilares_documentados={},
            documentos_sugeridos=[],
            riesgos_identificados=[],
            conclusion="Error en documentación",
            error=str(e)
        )


@router.post("/analisis/{tipo}")
async def analisis_especifico(
    tipo: TipoInvestigacion,
    input: AnalisisEspecificoInput,
    admin: str = Depends(verificar_superadmin)
):
    """
    📊 Ejecuta análisis específico (PESTEL, Porter, ESG, etc.)
    """
    logger.info(f"Oráculo Análisis: {tipo.value} para {input.empresa}")

    try:
        from services.oraculo_estrategico_service import oraculo_estrategico_service

        if tipo == TipoInvestigacion.PESTEL:
            resultado = await oraculo_estrategico_service.analisis_pestel(
                empresa=input.empresa,
                sector=input.sector,
                pais=input.pais
            )
        elif tipo == TipoInvestigacion.PORTER:
            resultado = await oraculo_estrategico_service.analisis_porter(
                empresa=input.empresa,
                sector=input.sector
            )
        elif tipo == TipoInvestigacion.ESG:
            resultado = await oraculo_estrategico_service.analisis_esg(
                empresa=input.empresa
            )
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de análisis no soportado: {tipo}")

        return {
            "success": resultado.get("success", False),
            "tipo_analisis": tipo.value,
            "empresa": input.empresa,
            "sector": input.sector,
            "resultado": resultado,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en análisis {tipo.value}: {e}")
        return {
            "success": False,
            "tipo_analisis": tipo.value,
            "empresa": input.empresa,
            "error": str(e)
        }


@router.get("/historial")
async def obtener_historial(
    empresa_id: Optional[str] = Query(None),
    limite: int = Query(20, ge=1, le=100),
    admin: str = Depends(verificar_superadmin)
):
    """
    📜 Obtiene historial de investigaciones realizadas.
    """
    # TODO: Implementar persistencia de historial
    return {
        "historial": [],
        "total": 0,
        "mensaje": "Historial no implementado aún - investigaciones son en tiempo real"
    }


@router.get("/health")
async def health_check():
    """
    🏥 Verifica estado del servicio Oráculo.
    """
    worker_url = os.getenv("ORACULO_WORKER_URL")

    return {
        "status": "ok",
        "servicio": "oraculo-estrategico",
        "worker_configurado": bool(worker_url),
        "worker_url": worker_url[:50] + "..." if worker_url and len(worker_url) > 50 else worker_url,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

async def _investigar_con_claude_local(input: InvestigarEmpresaInput) -> InvestigacionResult:
    """
    Realiza investigación usando Claude directamente (sin Worker).
    Útil para investigaciones rápidas o cuando el Worker no está disponible.
    """
    try:
        # Intentar con Anthropic
        from services.anthropic_provider import chat_completion_sync, is_configured

        if not is_configured():
            raise Exception("Anthropic no configurado")

        prompt = f"""Investiga la empresa "{input.empresa}" en México.

Sector: {input.sector or 'No especificado'}
Sitio web: {input.sitio_web or 'No proporcionado'}
Contexto: {input.contexto_adicional or 'Ninguno'}

Proporciona:
1. RESUMEN EJECUTIVO (2-3 párrafos)
2. PERFIL DE LA EMPRESA (datos clave)
3. ANÁLISIS DEL SECTOR (contexto competitivo)
4. RIESGOS IDENTIFICADOS
5. OPORTUNIDADES

Responde en español, de forma profesional y concisa."""

        respuesta = chat_completion_sync(
            messages=[{"role": "user", "content": prompt}],
            model="claude-sonnet-4-20250514",
            max_tokens=3000
        )

        return InvestigacionResult(
            success=True,
            empresa=input.empresa,
            timestamp=datetime.utcnow().isoformat(),
            tipo_investigacion=input.tipo_investigacion.value,
            nivel_profundidad=input.nivel_profundidad.value,
            resumen_ejecutivo=respuesta,
            score_confianza=60,  # Menor confianza sin fuentes externas
            fuentes_consultadas=1
        )

    except Exception as e:
        logger.error(f"Error en investigación local: {e}")
        raise
