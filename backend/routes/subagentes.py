"""
Rutas de API para Subagentes Especializados - Revisar.IA

Endpoints para:
- SUB_TIPIFICACION: Clasificación de proyectos
- SUB_MATERIALIDAD: Monitoreo de matriz de materialidad
- SUB_RIESGOS_ESPECIALES: Detección de riesgos especiales
- A7_DEFENSA: Generación de Defense File
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agents import (
    SUBAGENT_CONFIGS,
    clasificar_proyecto,
    evaluar_materialidad,
    detectar_riesgos,
    evaluar_defendibilidad,
    get_subagentes,
    get_agentes_para_fase,
    get_agentes_que_bloquean
)

router = APIRouter(prefix="/api/subagentes", tags=["Subagentes Revisar.IA"])


class ProyectoInput(BaseModel):
    nombre: str
    descripcion: str
    objetivo_declarado: Optional[str] = ""
    monto: float = 0
    entregables_esperados: List[str] = []
    roi_esperado: Optional[float] = None
    tipologia: Optional[str] = None
    fase_actual: str = "F0"
    risk_score_total: int = 0


class ProveedorInput(BaseModel):
    rfc: Optional[str] = None
    tipo_relacion: str = "TERCERO_INDEPENDIENTE"
    alerta_efos: bool = False
    historial_riesgo_score: int = 0
    empleados: int = 10


class DocumentoInput(BaseModel):
    id: Optional[str] = None
    nombre: str
    tipo: str
    version: Optional[str] = None
    fecha_carga: Optional[str] = None


class ClasificarProyectoRequest(BaseModel):
    proyecto: ProyectoInput
    proveedor: ProveedorInput


class EvaluarMaterialidadRequest(BaseModel):
    proyecto: ProyectoInput
    documentos: List[DocumentoInput] = []
    fase_actual: str = "F0"


class DetectarRiesgosRequest(BaseModel):
    proyecto: ProyectoInput
    proveedor: ProveedorInput
    contexto: Dict[str, Any] = {}


class EvaluarDefendibilidadRequest(BaseModel):
    proyecto: ProyectoInput
    documentos: List[DocumentoInput] = []
    deliberaciones: Dict[str, Any] = {}
    matriz_materialidad: Dict[str, Any] = {}
    vbc_fiscal: Optional[Dict[str, Any]] = None
    vbc_legal: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_subagentes_info() -> Dict[str, Any]:
    """Lista todos los subagentes disponibles y sus configuraciones"""
    subagentes = get_subagentes()
    bloqueadores = get_agentes_que_bloquean()
    
    return {
        "total_subagentes": len(SUBAGENT_CONFIGS),
        "subagentes": [
            {
                "id": config["id"],
                "nombre": config["nombre"],
                "fases": config.get("fases_participacion", []),
                "puede_bloquear": config.get("puede_bloquear_avance", False)
            }
            for config in SUBAGENT_CONFIGS.values()
        ],
        "subagentes_bloqueadores": [s["id"] for s in bloqueadores]
    }


@router.get("/por-fase/{fase}")
async def get_subagentes_por_fase(fase: str) -> Dict[str, Any]:
    """Obtiene los subagentes que participan en una fase específica"""
    agentes = get_agentes_para_fase(fase.upper())
    
    return {
        "fase": fase.upper(),
        "agentes_participantes": [
            {
                "id": a["id"],
                "nombre": a["nombre"],
                "puede_bloquear": a.get("puede_bloquear_avance", False)
            }
            for a in agentes
        ],
        "total": len(agentes)
    }


@router.get("/config/{agente_id}")
async def get_config_subagente(agente_id: str) -> Dict[str, Any]:
    """Obtiene la configuración completa de un subagente"""
    config = SUBAGENT_CONFIGS.get(agente_id.upper())
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Subagente '{agente_id}' no encontrado. Opciones: {list(SUBAGENT_CONFIGS.keys())}"
        )
    
    return {
        "id": config["id"],
        "nombre": config["nombre"],
        "rol": config["rol"],
        "contexto_requerido": config.get("contexto_requerido", {}),
        "fases_participacion": config.get("fases_participacion", []),
        "puede_bloquear_avance": config.get("puede_bloquear_avance", False),
        "output_schema": config.get("output_schema", {})
    }


@router.post("/tipificacion/clasificar")
async def clasificar_proyecto_endpoint(request: ClasificarProyectoRequest) -> Dict[str, Any]:
    """
    SUB_TIPIFICACION: Clasifica un proyecto en su tipología correcta.
    
    Determina qué checklist aplica y si requiere validación humana.
    """
    resultado = clasificar_proyecto(
        request.proyecto.model_dump(),
        request.proveedor.model_dump()
    )
    
    return {
        "subagente": "SUB_TIPIFICACION",
        "proyecto": request.proyecto.nombre,
        "resultado": resultado
    }


@router.post("/materialidad/evaluar")
async def evaluar_materialidad_endpoint(request: EvaluarMaterialidadRequest) -> Dict[str, Any]:
    """
    SUB_MATERIALIDAD: Evalúa la matriz de materialidad del proyecto.
    
    Verifica que cada hecho relevante tenga evidencia documental.
    Calcula porcentaje de completitud y determina si puede emitirse VBC.
    """
    documentos = [d.model_dump() for d in request.documentos]
    
    resultado = evaluar_materialidad(
        request.proyecto.model_dump(),
        documentos,
        request.fase_actual
    )
    
    return {
        "subagente": "SUB_MATERIALIDAD",
        "proyecto": request.proyecto.nombre,
        "fase_evaluada": request.fase_actual,
        "resultado": resultado
    }


@router.post("/riesgos/detectar")
async def detectar_riesgos_endpoint(request: DetectarRiesgosRequest) -> Dict[str, Any]:
    """
    SUB_RIESGOS_ESPECIALES: Detecta riesgos especiales en un proyecto.
    
    Analiza EFOS, partes relacionadas, esquemas reportables, TP pendiente, monto alto.
    Determina si el proyecto puede continuar y qué condiciones debe cumplir.
    """
    resultado = detectar_riesgos(
        request.proyecto.model_dump(),
        request.proveedor.model_dump(),
        request.contexto
    )
    
    return {
        "subagente": "SUB_RIESGOS_ESPECIALES",
        "proyecto": request.proyecto.nombre,
        "resultado": resultado
    }


@router.post("/defensa/evaluar")
async def evaluar_defensa_endpoint(request: EvaluarDefendibilidadRequest) -> Dict[str, Any]:
    """
    A7_DEFENSA: Evalúa la defendibilidad del expediente del proyecto.
    
    Genera Defense File estructurado con:
    - Índice de defendibilidad (0-100)
    - Evaluación por criterio (razón negocios, BEE, materialidad, trazabilidad, coherencia)
    - Documentos clave presentes/faltantes
    - Argumentos de defensa
    - Puntos vulnerables
    - Recomendaciones de refuerzo
    """
    documentos = [d.model_dump() for d in request.documentos]
    
    resultado = evaluar_defendibilidad(
        request.proyecto.model_dump(),
        documentos,
        request.deliberaciones,
        request.matriz_materialidad,
        request.vbc_fiscal,
        request.vbc_legal
    )
    
    return {
        "subagente": "A7_DEFENSA",
        "proyecto": request.proyecto.nombre,
        "resultado": resultado
    }


@router.get("/ejemplo/tipificacion")
async def ejemplo_tipificacion() -> Dict[str, Any]:
    """
    Ejemplo de clasificación de proyecto para el dashboard.
    Devuelve un resultado de ejemplo de tipificación.
    """
    return {
        "subagente": "SUB_TIPIFICACION",
        "proyecto": "Ejemplo Demo",
        "resultado": {
            "tipologia": "CONSULTORIA_MACRO_MERCADO",
            "tipologia_nombre": "Consultoría en Macroeconomía y Mercado",
            "descripcion": "Estudios de mercado, análisis macroeconómico y proyecciones",
            "requiere_validacion_humana": True,
            "umbral_monto": 500000,
            "checklist_aplicable": "CHECKLIST_CONSULTORIA",
            "riesgo_base": "MEDIO",
            "agentes_requeridos": ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS", "LEGAL"],
            "confianza": 0.92
        }
    }


@router.get("/ejemplo/riesgos-criticos")
async def ejemplo_riesgos_criticos() -> Dict[str, Any]:
    """
    Ejemplo de detección de riesgos para el dashboard.
    Devuelve un resultado de ejemplo con riesgos críticos.
    """
    return {
        "subagente": "SUB_RIESGOS_ESPECIALES",
        "proyecto": "Ejemplo Demo",
        "resultado": {
            "riesgos_detectados": [
                {
                    "tipo": "PARTES_RELACIONADAS",
                    "descripcion": "Proveedor con posible relación con directivos",
                    "severidad": "ALTA",
                    "mitigable": True,
                    "recomendacion": "Solicitar declaración de independencia"
                },
                {
                    "tipo": "DESPROPORCION_MONTO",
                    "descripcion": "Monto superior al promedio del servicio",
                    "severidad": "MEDIA",
                    "mitigable": True,
                    "recomendacion": "Obtener cotizaciones comparativas"
                }
            ],
            "nivel_riesgo_global": "MEDIO-ALTO",
            "puede_continuar": True,
            "requiere_escalamiento": False,
            "candados_afectados": ["F2", "F6"]
        }
    }

