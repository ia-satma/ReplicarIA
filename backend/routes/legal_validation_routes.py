"""
============================================================
REVISAR.IA - API de Validación Legal
============================================================
Endpoints para validación de operaciones según:
- LISR 27 (Deducciones)
- CFF 69-B (Materialidad)
- CFF 5-A (Razón de negocios)
- LIVA 5 + Anexo 20 (IVA y CFDI)
============================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from services.legal_validation_service import (
    get_legal_validation_service,
    TipoServicio,
    TipoEvidencia,
    CapaValidacion,
    NivelRiesgo
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-validation", tags=["Validación Legal"])


# ============================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================

class TipoServicioEnum(str, Enum):
    CONSULTORIA = "consultoria"
    TECNOLOGIA = "tecnologia"
    MARKETING = "marketing"
    LEGAL = "legal"
    CONTABLE = "contable"
    OUTSOURCING = "outsourcing"
    CAPACITACION = "capacitacion"
    TRANSPORTE = "transporte"
    MANTENIMIENTO = "mantenimiento"
    HONORARIOS = "honorarios"
    ARRENDAMIENTO = "arrendamiento"
    SERVICIOS_GENERALES = "servicios_generales"


class EvidenciaPresentada(BaseModel):
    tipo: str
    archivo_id: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_documento: Optional[datetime] = None


class ValidarOperacionRequest(BaseModel):
    operacion_id: str = Field(..., description="ID único de la operación")
    proveedor_rfc: str = Field(..., description="RFC del proveedor")
    proveedor_nombre: Optional[str] = Field(None, description="Nombre del proveedor")
    monto: float = Field(..., description="Monto de la operación")
    tipo_servicio: TipoServicioEnum = Field(..., description="Tipo de servicio")
    evidencias: List[EvidenciaPresentada] = Field(default_factory=list)
    es_parte_relacionada: bool = Field(False, description="¿Es operación con parte relacionada?")
    proveedor_en_69b: bool = Field(False, description="¿Proveedor aparece en lista 69-B?")
    cfdi_validado: bool = Field(True, description="¿CFDI validado en SAT?")
    tiene_opinion_32d: bool = Field(False, description="¿Tiene opinión 32-D positiva?")
    descripcion_operacion: Optional[str] = None


class ResultadoReglaResponse(BaseModel):
    regla_id: str
    regla_nombre: str
    cumple: bool
    nivel_cumplimiento: float
    evidencias_presentes: List[str]
    evidencias_faltantes: List[str]
    observaciones: str
    recomendaciones: List[str]


class EvaluacionResponse(BaseModel):
    operacion_id: str
    proveedor_rfc: str
    monto: float
    fecha_evaluacion: datetime
    nivel_riesgo: str
    semaforo_color: str
    semaforo_emoji: str
    score_total: float
    score_formal: float
    score_materialidad: float
    score_razon_negocios: float
    resultados_por_regla: List[ResultadoReglaResponse]
    resumen: str
    acciones_correctivas: List[str]


class EvidenciaChecklistItem(BaseModel):
    tipo: str
    descripcion: str
    obligatoria: bool
    fundamentos: List[str]
    reglas_relacionadas: List[str]


class ChecklistResponse(BaseModel):
    tipo_servicio: str
    total_reglas_aplicables: int
    evidencias_requeridas: List[EvidenciaChecklistItem]
    capas_validacion: List[Dict[str, str]]


class ReglaResponse(BaseModel):
    id: str
    nombre: str
    fundamento_legal: str
    capa: str
    descripcion: str
    condicion_logica: str
    evidencias_minimas: List[Dict[str, Any]]
    peso_validacion: float


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/tipos-servicio", response_model=List[Dict[str, str]])
async def listar_tipos_servicio():
    """
    Lista todos los tipos de servicio disponibles para validación.
    """
    return [
        {"id": ts.value, "nombre": ts.value.replace("_", " ").title()}
        for ts in TipoServicio
    ]


@router.get("/tipos-evidencia", response_model=List[Dict[str, str]])
async def listar_tipos_evidencia():
    """
    Lista todos los tipos de evidencia documental.
    """
    descripciones = {
        "contrato": "Contrato o acuerdo de servicios",
        "cfdi": "Comprobante Fiscal Digital por Internet",
        "estado_cuenta": "Estado de cuenta bancario",
        "poliza_contable": "Póliza de registro contable",
        "entregable": "Producto o entregable del servicio",
        "orden_servicio": "Orden de trabajo o SOW",
        "acta": "Acta de reunión o sesión",
        "correo": "Comunicación electrónica",
        "reporte": "Informe o reporte de actividades",
        "consulta_sat": "Consulta de validación en SAT",
        "opinion_32d": "Opinión de cumplimiento 32-D",
        "lista_69b": "Consulta en lista 69-B SAT",
        "estudio_pt": "Estudio de precios de transferencia",
        "memorando": "Memorando interno",
        "minuta": "Minuta de reunión",
        "analisis_cb": "Análisis costo-beneficio"
    }
    return [
        {"id": te.value, "nombre": te.value.replace("_", " ").title(), "descripcion": descripciones.get(te.value, "")}
        for te in TipoEvidencia
    ]


@router.get("/reglas", response_model=List[ReglaResponse])
async def listar_reglas(
    capa: Optional[str] = Query(None, description="Filtrar por capa: formal_fiscal, materialidad, razon_negocios"),
    tipo_servicio: Optional[TipoServicioEnum] = Query(None, description="Filtrar por tipo de servicio")
):
    """
    Lista todas las reglas de validación legal.
    Opcionalmente filtra por capa o tipo de servicio.
    """
    service = get_legal_validation_service()

    if tipo_servicio:
        reglas = service.obtener_reglas_por_servicio(TipoServicio(tipo_servicio.value))
    elif capa:
        try:
            capa_enum = CapaValidacion(capa)
            reglas = service.obtener_reglas_por_capa(capa_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Capa inválida: {capa}")
    else:
        reglas = service.todas_las_reglas

    return [
        ReglaResponse(
            id=r.id,
            nombre=r.nombre,
            fundamento_legal=r.fundamento_legal,
            capa=r.capa.value,
            descripcion=r.descripcion,
            condicion_logica=r.condicion_logica,
            evidencias_minimas=[
                {
                    "tipo": e.tipo.value,
                    "descripcion": e.descripcion,
                    "obligatoria": e.obligatoria,
                    "alternativas": [a.value for a in e.alternativas]
                }
                for e in r.evidencias_minimas
            ],
            peso_validacion=r.peso_validacion
        )
        for r in reglas
    ]


@router.get("/checklist/{tipo_servicio}", response_model=ChecklistResponse)
async def obtener_checklist(tipo_servicio: TipoServicioEnum):
    """
    Obtiene el checklist completo de evidencias requeridas para un tipo de servicio.
    Útil para la UI de captura de documentos.
    """
    service = get_legal_validation_service()

    try:
        ts = TipoServicio(tipo_servicio.value)
        checklist = service.obtener_checklist_completo(ts)
        return ChecklistResponse(**checklist)
    except Exception as e:
        logger.error(f"Error obteniendo checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validar", response_model=EvaluacionResponse)
async def validar_operacion(request: ValidarOperacionRequest):
    """
    Valida una operación contra todas las reglas aplicables.
    Retorna evaluación completa con semáforo de riesgo.

    El semáforo puede ser:
    - 🟢 VERDE: Cumple formales + materialidad + razón de negocios
    - 🟡 AMARILLO: Formales OK, débil en materialidad o razón
    - 🔴 ROJO: Proveedor en riesgo (69-B) o sin evidencia mínima
    """
    service = get_legal_validation_service()

    try:
        # Convertir evidencias a tipos
        evidencias_tipos = [TipoEvidencia(e.tipo) for e in request.evidencias if e.tipo]

        # Ejecutar validación
        evaluacion = service.validar_operacion(
            operacion_id=request.operacion_id,
            proveedor_rfc=request.proveedor_rfc,
            monto=request.monto,
            tipo_servicio=TipoServicio(request.tipo_servicio.value),
            evidencias_presentadas=evidencias_tipos,
            es_parte_relacionada=request.es_parte_relacionada,
            proveedor_en_69b=request.proveedor_en_69b,
            cfdi_validado=request.cfdi_validado,
            tiene_opinion_32d=request.tiene_opinion_32d
        )

        # Mapear semáforo a color y emoji
        semaforo_map = {
            NivelRiesgo.VERDE: {"color": "green", "emoji": "🟢"},
            NivelRiesgo.AMARILLO: {"color": "yellow", "emoji": "🟡"},
            NivelRiesgo.ROJO: {"color": "red", "emoji": "🔴"}
        }

        semaforo = semaforo_map.get(evaluacion.nivel_riesgo, {"color": "gray", "emoji": "⚪"})

        return EvaluacionResponse(
            operacion_id=evaluacion.operacion_id,
            proveedor_rfc=evaluacion.proveedor_rfc,
            monto=evaluacion.monto,
            fecha_evaluacion=evaluacion.fecha_evaluacion,
            nivel_riesgo=evaluacion.nivel_riesgo.value,
            semaforo_color=semaforo["color"],
            semaforo_emoji=semaforo["emoji"],
            score_total=evaluacion.score_total,
            score_formal=evaluacion.score_formal,
            score_materialidad=evaluacion.score_materialidad,
            score_razon_negocios=evaluacion.score_razon_negocios,
            resultados_por_regla=[
                ResultadoReglaResponse(
                    regla_id=r.regla_id,
                    regla_nombre=r.regla_nombre,
                    cumple=r.cumple,
                    nivel_cumplimiento=r.nivel_cumplimiento,
                    evidencias_presentes=r.evidencias_presentes,
                    evidencias_faltantes=r.evidencias_faltantes,
                    observaciones=r.observaciones,
                    recomendaciones=r.recomendaciones
                )
                for r in evaluacion.resultados_por_regla
            ],
            resumen=evaluacion.resumen,
            acciones_correctivas=evaluacion.acciones_correctivas
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Valor inválido: {e}")
    except Exception as e:
        logger.error(f"Error validando operación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validar-rapido")
async def validar_rapido(
    proveedor_rfc: str = Query(..., description="RFC del proveedor"),
    monto: float = Query(..., description="Monto de la operación"),
    tipo_servicio: TipoServicioEnum = Query(..., description="Tipo de servicio"),
    tiene_contrato: bool = Query(False),
    tiene_cfdi: bool = Query(False),
    tiene_pago_banco: bool = Query(False),
    tiene_entregables: bool = Query(False),
    proveedor_en_69b: bool = Query(False)
):
    """
    Validación rápida con parámetros básicos.
    Retorna solo el semáforo y score general.
    """
    service = get_legal_validation_service()

    # Construir lista de evidencias basada en flags
    evidencias = []
    if tiene_contrato:
        evidencias.append(TipoEvidencia.CONTRATO)
    if tiene_cfdi:
        evidencias.append(TipoEvidencia.CFDI)
        evidencias.append(TipoEvidencia.CONSULTA_SAT)
    if tiene_pago_banco:
        evidencias.append(TipoEvidencia.ESTADO_CUENTA)
        evidencias.append(TipoEvidencia.POLIZA_CONTABLE)
    if tiene_entregables:
        evidencias.append(TipoEvidencia.ENTREGABLE)
        evidencias.append(TipoEvidencia.REPORTE)

    evaluacion = service.validar_operacion(
        operacion_id=f"quick-{proveedor_rfc}-{datetime.now().timestamp()}",
        proveedor_rfc=proveedor_rfc,
        monto=monto,
        tipo_servicio=TipoServicio(tipo_servicio.value),
        evidencias_presentadas=evidencias,
        proveedor_en_69b=proveedor_en_69b,
        cfdi_validado=tiene_cfdi
    )

    semaforo_map = {
        NivelRiesgo.VERDE: {"color": "green", "emoji": "🟢", "mensaje": "Bajo riesgo"},
        NivelRiesgo.AMARILLO: {"color": "yellow", "emoji": "🟡", "mensaje": "Riesgo medio - revisar documentación"},
        NivelRiesgo.ROJO: {"color": "red", "emoji": "🔴", "mensaje": "Alto riesgo - acción urgente"}
    }

    semaforo = semaforo_map.get(evaluacion.nivel_riesgo)

    return {
        "nivel_riesgo": evaluacion.nivel_riesgo.value,
        "semaforo": semaforo,
        "score_total": evaluacion.score_total,
        "scores": {
            "formal_fiscal": evaluacion.score_formal,
            "materialidad": evaluacion.score_materialidad,
            "razon_negocios": evaluacion.score_razon_negocios
        },
        "resumen": evaluacion.resumen,
        "acciones_inmediatas": evaluacion.acciones_correctivas[:3] if evaluacion.acciones_correctivas else []
    }


@router.get("/estadisticas-reglas")
async def estadisticas_reglas():
    """
    Retorna estadísticas sobre las reglas de validación.
    Útil para dashboards.
    """
    service = get_legal_validation_service()

    reglas_formal = service.obtener_reglas_por_capa(CapaValidacion.FORMAL_FISCAL)
    reglas_material = service.obtener_reglas_por_capa(CapaValidacion.MATERIALIDAD)
    reglas_razon = service.obtener_reglas_por_capa(CapaValidacion.RAZON_NEGOCIOS)

    return {
        "total_reglas": len(service.todas_las_reglas),
        "por_capa": {
            "formal_fiscal": {
                "cantidad": len(reglas_formal),
                "peso_total": sum(r.peso_validacion for r in reglas_formal),
                "reglas": [{"id": r.id, "nombre": r.nombre} for r in reglas_formal]
            },
            "materialidad": {
                "cantidad": len(reglas_material),
                "peso_total": sum(r.peso_validacion for r in reglas_material),
                "reglas": [{"id": r.id, "nombre": r.nombre} for r in reglas_material]
            },
            "razon_negocios": {
                "cantidad": len(reglas_razon),
                "peso_total": sum(r.peso_validacion for r in reglas_razon),
                "reglas": [{"id": r.id, "nombre": r.nombre} for r in reglas_razon]
            }
        },
        "tipos_servicio_soportados": [ts.value for ts in TipoServicio],
        "tipos_evidencia_soportados": [te.value for te in TipoEvidencia],
        "ponderacion_capas": {
            "formal_fiscal": "35%",
            "materialidad": "40%",
            "razon_negocios": "25%"
        }
    }


@router.get("/fundamentos-legales")
async def listar_fundamentos_legales():
    """
    Lista todos los fundamentos legales utilizados en las reglas.
    Útil para referencia y documentación.
    """
    service = get_legal_validation_service()

    fundamentos = {}
    for regla in service.todas_las_reglas:
        if regla.fundamento_legal not in fundamentos:
            fundamentos[regla.fundamento_legal] = {
                "fundamento": regla.fundamento_legal,
                "reglas_asociadas": [],
                "capa_principal": regla.capa.value
            }
        fundamentos[regla.fundamento_legal]["reglas_asociadas"].append({
            "id": regla.id,
            "nombre": regla.nombre
        })

    return {
        "fundamentos": list(fundamentos.values()),
        "categorias": {
            "lisr": [f for f in fundamentos.values() if "LISR" in f["fundamento"]],
            "cff": [f for f in fundamentos.values() if "CFF" in f["fundamento"]],
            "liva": [f for f in fundamentos.values() if "LIVA" in f["fundamento"]],
            "anexo20": [f for f in fundamentos.values() if "Anexo" in f["fundamento"]]
        }
    }
