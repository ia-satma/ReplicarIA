# backend/config/agentes_config.py
"""
Configuración estructurada de agentes para el sistema multi-tenant.
Define contextos requeridos, documentos RAG, fases activas y capacidades de bloqueo.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum

class TipoContexto(str, Enum):
    OBLIGATORIO = "obligatorio"
    DESEABLE = "deseable"

class ContextoRequerido(BaseModel):
    nombre: str
    tipo: TipoContexto
    fuente: str  # "empresa", "proyecto", "normativo", "rag"
    descripcion: str

class ConfiguracionAgente(BaseModel):
    id: str
    nombre: str
    rol: str
    descripcion: str
    fases_activas: List[str]  # ["F0", "F1", "F2", ...]
    
    # Contexto que necesita para deliberar
    contexto_requerido: List[ContextoRequerido]
    
    # Documentos RAG que consulta
    documentos_rag: List[str]
    
    # Output schema
    output_fields: List[str]
    
    # Puede bloquear avance de fase?
    puede_bloquear: bool = False
    fases_bloqueo: List[str] = []

# Configuración de todos los agentes
AGENTES_CONFIG: Dict[str, ConfiguracionAgente] = {
    
    "A1_ESTRATEGIA": ConfiguracionAgente(
        id="A1_ESTRATEGIA",
        nombre="Agente de Estrategia",
        rol="Sponsor / Evaluador de Razón de Negocios",
        descripcion="Evalúa si el proyecto tiene razón de negocios genuina y BEE documentado",
        fases_activas=["F0", "F4", "F5", "F9"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="vision_pilares",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="empresa",
                descripcion="Visión y pilares estratégicos de la empresa"
            ),
            ContextoRequerido(
                nombre="okrs_vigentes",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="empresa",
                descripcion="OKRs del periodo actual"
            ),
            ContextoRequerido(
                nombre="plan_estrategico_anual",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="empresa",
                descripcion="Plan estratégico del ejercicio"
            ),
            ContextoRequerido(
                nombre="tipologia_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Clasificación del tipo de servicio"
            ),
            ContextoRequerido(
                nombre="bee_propuesto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Beneficio económico esperado del proyecto"
            ),
            ContextoRequerido(
                nombre="panorama_industria",
                tipo=TipoContexto.DESEABLE,
                fuente="empresa",
                descripcion="Contexto macroeconómico y sectorial"
            )
        ],
        documentos_rag=[
            "001_vision_pilares",
            "002_planeacion_okrs",
            "003_panorama_industria",
            "004_plan_estrategico_anual",
            "005_matriz_alineacion_bee"
        ],
        output_fields=[
            "decision",          # APROBAR | APROBAR_CONDICIONES | RECHAZAR
            "razon_negocios",    # Análisis de razón de negocios
            "alineacion_estrategica",  # Vinculación con pilares/OKRs
            "bee_evaluacion",    # Evaluación del BEE propuesto
            "risk_score_parcial",
            "condiciones",
            "recomendaciones"
        ],
        puede_bloquear=True,
        fases_bloqueo=["F0"]
    ),
    
    "A2_PMO": ConfiguracionAgente(
        id="A2_PMO",
        nombre="Agente PMO",
        rol="Orquestador del Proceso F0-F9",
        descripcion="Controla el flujo de fases, verifica checklists y candados",
        fases_activas=["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="estado_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Fase actual y estado de documentos"
            ),
            ContextoRequerido(
                nombre="checklist_fase",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Items requeridos para la fase actual"
            ),
            ContextoRequerido(
                nombre="decisiones_agentes",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Dictámenes previos de otros agentes"
            ),
            ContextoRequerido(
                nombre="umbrales_revision",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Reglas de revisión humana"
            )
        ],
        documentos_rag=[
            "001_poe_f0_f9_manual",
            "002_plantillas_po_consolidation",
            "003_guia_coordinacion_multiagente",
            "004_checklist_tipologia"
        ],
        output_fields=[
            "puede_avanzar",
            "fase_actual",
            "fase_siguiente",
            "items_pendientes",
            "bloqueos_activos",
            "requiere_revision_humana",
            "consolidation_report"
        ],
        puede_bloquear=True,
        fases_bloqueo=["F2", "F6", "F8"]  # Candados duros
    ),
    
    "A3_FISCAL": ConfiguracionAgente(
        id="A3_FISCAL",
        nombre="Agente Fiscal",
        rol="Especialista en Cumplimiento Fiscal",
        descripcion="Evalúa los 4 pilares fiscales y emite VBC Fiscal",
        fases_activas=["F0", "F1", "F4", "F6"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="marco_normativo",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="CFF 5-A, 69-B, LISR 27"
            ),
            ContextoRequerido(
                nombre="tipologia_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Tipo de servicio y riesgo inherente"
            ),
            ContextoRequerido(
                nombre="bee_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Beneficio económico documentado"
            ),
            ContextoRequerido(
                nombre="proveedor_info",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Datos del proveedor y alertas EFOS"
            ),
            ContextoRequerido(
                nombre="matriz_materialidad",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Estado de evidencias de ejecución"
            ),
            ContextoRequerido(
                nombre="casos_auditoria",
                tipo=TipoContexto.DESEABLE,
                fuente="rag",
                descripcion="Experiencias previas con SAT"
            )
        ],
        documentos_rag=[
            "001_guia_razon_negocios_5a",
            "002_guia_materialidad_69b",
            "003_estricta_indispensabilidad_27",
            "004_cff_extracto",
            "005_lisr_extracto",
            "006_casos_auditoria_sat",
            "007_lista_69b_politica",
            "008_criterios_efos"
        ],
        output_fields=[
            "decision",
            "vbc_fiscal",           # EMITIDO | CONDICIONADO | RECHAZADO
            "risk_score_total",
            "risk_score_por_pilar", # {razon_negocios, beneficio_economico, materialidad, trazabilidad}
            "nivel_riesgo",
            "alertas_efos",
            "condiciones",
            "fundamentacion_legal"
        ],
        puede_bloquear=True,
        fases_bloqueo=["F0", "F6"]
    ),
    
    "A4_LEGAL": ConfiguracionAgente(
        id="A4_LEGAL",
        nombre="Agente Legal",
        rol="Especialista en Contratos y Trazabilidad",
        descripcion="Revisa contratos, SOW y emite VBC Legal",
        fases_activas=["F1", "F6"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="contrato_sow",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Contrato y/o SOW del servicio"
            ),
            ContextoRequerido(
                nombre="tipologia_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Tipo de servicio"
            ),
            ContextoRequerido(
                nombre="entregables_definidos",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Lista de entregables comprometidos"
            ),
            ContextoRequerido(
                nombre="clausulas_requeridas",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Cláusulas mínimas por tipología"
            )
        ],
        documentos_rag=[
            "001_plantilla_contrato",
            "002_guia_nom151_trazabilidad",
            "003_clausulas_materialidad",
            "004_guia_revision_sow",
            "005_terminos_pago_penalizaciones",
            "006_proteccion_datos_confidencialidad"
        ],
        output_fields=[
            "decision",
            "vbc_legal",
            "revision_contrato",
            "revision_sow",
            "clausulas_faltantes",
            "riesgos_contractuales",
            "recomendaciones"
        ],
        puede_bloquear=True,
        fases_bloqueo=["F1", "F6"]
    ),
    
    "A5_FINANZAS": ConfiguracionAgente(
        id="A5_FINANZAS",
        nombre="Agente Finanzas",
        rol="Director Financiero / Controller",
        descripcion="Evalúa proporción económica, presupuesto y 3-way match",
        fases_activas=["F2", "F4", "F8"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="presupuesto_area",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="empresa",
                descripcion="Presupuesto disponible del área"
            ),
            ContextoRequerido(
                nombre="monto_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Costo del servicio"
            ),
            ContextoRequerido(
                nombre="bee_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="ROI esperado"
            ),
            ContextoRequerido(
                nombre="benchmarks_sector",
                tipo=TipoContexto.DESEABLE,
                fuente="rag",
                descripcion="Referencias de mercado"
            ),
            ContextoRequerido(
                nombre="cfdi_contrato",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Datos para 3-way match (solo en F8)"
            )
        ],
        documentos_rag=[
            "001_politicas_presupuestales",
            "002_benchmarks_roi_sector",
            "003_guia_3way_match",
            "004_analisis_financieros_previos",
            "005_limites_autorizacion_monto"
        ],
        output_fields=[
            "decision",
            "presupuesto_disponible",
            "proporcion_evaluacion",   # RAZONABLE | ALTO | DESPROPORCIONADO
            "roi_esperado",
            "three_way_match",         # Solo en F8
            "autorizacion_requerida",
            "condiciones"
        ],
        puede_bloquear=True,
        fases_bloqueo=["F2", "F8"]
    ),
    
    "A6_PROVEEDOR": ConfiguracionAgente(
        id="A6_PROVEEDOR",
        nombre="Agente Proveedor",
        rol="Ejecutor del Servicio",
        descripcion="Gestiona entregables y evidencias de ejecución",
        fases_activas=["F3", "F4", "F5"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="sow_vigente",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Alcance y entregables comprometidos"
            ),
            ContextoRequerido(
                nombre="checklist_entregables",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Entregables requeridos por tipología"
            ),
            ContextoRequerido(
                nombre="documentos_cargados",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Evidencias ya subidas"
            )
        ],
        documentos_rag=[
            "001_guia_entregables_tipologia",
            "002_plantilla_acta_aceptacion",
            "003_checklist_evidencia_ejecucion",
            "004_formato_minutas_trabajo"
        ],
        output_fields=[
            "entregables_status",
            "evidencias_cargadas",
            "evidencias_faltantes",
            "completitud_materialidad",
            "alertas"
        ],
        puede_bloquear=False
    ),
    
    "A7_DEFENSA": ConfiguracionAgente(
        id="A7_DEFENSA",
        nombre="Agente Defense File",
        rol="Consolidador del Expediente de Defensa",
        descripcion="Evalúa defendibilidad y completitud del expediente",
        fases_activas=["F6", "F7", "F9"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="defense_file_actual",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Documentos en el expediente"
            ),
            ContextoRequerido(
                nombre="decisiones_agentes",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Todos los dictámenes previos"
            ),
            ContextoRequerido(
                nombre="matriz_materialidad",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Estado de evidencias"
            ),
            ContextoRequerido(
                nombre="precedentes_tfja",
                tipo=TipoContexto.DESEABLE,
                fuente="rag",
                descripcion="Criterios de tribunales"
            )
        ],
        documentos_rag=[
            "001_guia_defense_file",
            "002_criterios_defendibilidad_tfja",
            "003_checklist_documentos_criticos",
            "004_precedentes_tfja",
            "005_guia_refuerzo_probatorio"
        ],
        output_fields=[
            "indice_defendibilidad",   # 0-100
            "nivel_defendibilidad",    # DÉBIL | MODERADO | BUENO | EXCELENTE
            "documentos_criticos_status",
            "brechas_identificadas",
            "recomendaciones_refuerzo",
            "argumentos_defensa"
        ],
        puede_bloquear=False
    ),
    
    # === SUBAGENTES ===
    
    "S1_TIPIFICACION": ConfiguracionAgente(
        id="S1_TIPIFICACION",
        nombre="Subagente Tipificación",
        rol="Clasificador de Tipología de Servicio",
        descripcion="Asigna la tipología correcta al proyecto",
        fases_activas=["F0"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="descripcion_servicio",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Descripción del servicio propuesto"
            ),
            ContextoRequerido(
                nombre="catalogo_tipologias",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Tipologías disponibles y criterios"
            )
        ],
        documentos_rag=["003_tipologias_servicio"],
        output_fields=[
            "tipologia_asignada",
            "nivel_confianza",
            "tipologias_alternativas",
            "riesgo_inherente"
        ],
        puede_bloquear=False
    ),
    
    "S2_MATERIALIDAD": ConfiguracionAgente(
        id="S2_MATERIALIDAD",
        nombre="Subagente Materialidad",
        rol="Constructor de Matriz de Materialidad",
        descripcion="Construye y monitorea la matriz hecho-evidencia",
        fases_activas=["F5", "F6"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="tipologia_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Tipo de servicio"
            ),
            ContextoRequerido(
                nombre="documentos_cargados",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Evidencias disponibles"
            ),
            ContextoRequerido(
                nombre="checklist_materialidad",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Items requeridos por tipología"
            )
        ],
        documentos_rag=[
            "002_guia_materialidad_69b",
            "003_checklist_evidencia_ejecucion"
        ],
        output_fields=[
            "matriz_materialidad",
            "porcentaje_completitud",
            "items_ok",
            "items_faltantes",
            "items_inconsistentes",
            "nivel_materialidad"
        ],
        puede_bloquear=False
    ),
    
    "S3_RIESGOS": ConfiguracionAgente(
        id="S3_RIESGOS",
        nombre="Subagente Riesgos Especiales",
        rol="Detector de Riesgos EFOS/TP/Esquemas",
        descripcion="Identifica señales de riesgo especial",
        fases_activas=["F0", "F2", "F6"],
        contexto_requerido=[
            ContextoRequerido(
                nombre="proveedor_info",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Datos del proveedor"
            ),
            ContextoRequerido(
                nombre="tipologia_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Tipo de servicio"
            ),
            ContextoRequerido(
                nombre="monto_proyecto",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="proyecto",
                descripcion="Costo del servicio"
            ),
            ContextoRequerido(
                nombre="criterios_efos",
                tipo=TipoContexto.OBLIGATORIO,
                fuente="normativo",
                descripcion="Señales de alerta EFOS"
            )
        ],
        documentos_rag=[
            "007_lista_69b_politica",
            "008_criterios_efos",
            "005_politica_anti_efos"
        ],
        output_fields=[
            "riesgos_detectados",
            "nivel_riesgo_efos",
            "nivel_riesgo_tp",
            "nivel_riesgo_esquema",
            "alertas",
            "acciones_requeridas"
        ],
        puede_bloquear=False
    )
}


# Función helper para obtener configuración
def get_agente_config(agente_id: str) -> ConfiguracionAgente:
    if agente_id not in AGENTES_CONFIG:
        raise ValueError(f"Agente {agente_id} no configurado")
    return AGENTES_CONFIG[agente_id]

def get_contexto_obligatorio(agente_id: str) -> List[str]:
    config = get_agente_config(agente_id)
    return [c.nombre for c in config.contexto_requerido if c.tipo == TipoContexto.OBLIGATORIO]

def get_documentos_rag(agente_id: str) -> List[str]:
    return get_agente_config(agente_id).documentos_rag

def get_agentes_por_fase(fase: str) -> List[str]:
    """Retorna los IDs de agentes activos en una fase específica"""
    return [
        agente_id for agente_id, config in AGENTES_CONFIG.items()
        if fase in config.fases_activas
    ]

def get_agentes_bloqueadores(fase: str) -> List[str]:
    """Retorna los IDs de agentes que pueden bloquear una fase específica"""
    return [
        agente_id for agente_id, config in AGENTES_CONFIG.items()
        if config.puede_bloquear and fase in config.fases_bloqueo
    ]

def get_all_agente_ids() -> List[str]:
    """Retorna todos los IDs de agentes configurados"""
    return list(AGENTES_CONFIG.keys())

def get_agentes_principales() -> List[str]:
    """Retorna solo los agentes principales (no subagentes)"""
    return [aid for aid in AGENTES_CONFIG.keys() if not aid.startswith("S")]

def get_subagentes() -> List[str]:
    """Retorna solo los subagentes"""
    return [aid for aid in AGENTES_CONFIG.keys() if aid.startswith("S")]
