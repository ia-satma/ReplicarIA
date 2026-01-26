"""
Revisar.IA - Seed Data
Initial checklist templates for CONSULTORIA_MACRO_MERCADO typology
"""
from typing import List, Dict, Any
from models.durezza_enums import TipologiaProyecto, FaseProyecto, ResponsableChecklist


def get_checklist_seeds() -> List[Dict[str, Any]]:
    seeds = []

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F0.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "SIB con objetivo económico específico y cuantificable",
                "obligatorio": True,
                "tipo_documento_esperado": "SIB_BEE",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Documento con objetivo SMART vinculado a métrica de negocio",
                "ayuda_contextual": "El SIB debe especificar qué problema de negocio resuelve y cómo se medirá el éxito"
            },
            {
                "orden": 2,
                "descripcion": "BEE con ROI estimado y horizonte temporal definido",
                "obligatorio": True,
                "tipo_documento_esperado": "SIB_BEE",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Cálculo de ROI con supuestos documentados y horizonte en meses",
                "ayuda_contextual": "Incluir escenarios pesimista, base y optimista"
            },
            {
                "orden": 3,
                "descripcion": "Vinculación documentada con Plan Estratégico",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Referencia explícita a iniciativa estratégica aprobada",
                "ayuda_contextual": "Debe coincidir con prioridades del plan estratégico vigente"
            },
            {
                "orden": 4,
                "descripcion": "Evaluación inicial de riesgo fiscal completada",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.FISCAL.value,
                "criterio_aceptacion": "Formulario de riesgo fiscal inicial con score preliminar",
                "ayuda_contextual": "Identifica alertas tempranas de deducibilidad"
            }
        ],
        "total_items": 4,
        "items_obligatorios": 4,
        "activo": True
    })

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F1.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "SOW con objeto y alcance específico",
                "obligatorio": True,
                "tipo_documento_esperado": "SOW",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Alcance delimitado sin ambigüedades, con exclusiones explícitas",
                "ayuda_contextual": "El alcance debe ser lo suficientemente específico para ser auditable"
            },
            {
                "orden": 2,
                "descripcion": "Lista de entregables nominales con descripción",
                "obligatorio": True,
                "tipo_documento_esperado": "SOW",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Cada entregable con nombre, descripción y formato esperado",
                "ayuda_contextual": "Entregables tangibles y verificables, no actividades"
            },
            {
                "orden": 3,
                "descripcion": "Esquema de honorarios/hitos de pago",
                "obligatorio": True,
                "tipo_documento_esperado": "SOW",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Desglose de pagos vinculados a entregables específicos",
                "ayuda_contextual": "Evitar pagos 100% anticipados o sin condición de entrega"
            },
            {
                "orden": 4,
                "descripcion": "Criterios de aceptación preliminares",
                "obligatorio": True,
                "tipo_documento_esperado": "ANEXO_TECNICO",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Criterios objetivos para cada entregable principal",
                "ayuda_contextual": "Define cómo se validará la calidad de cada entregable"
            }
        ],
        "total_items": 4,
        "items_obligatorios": 4,
        "activo": True
    })

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F2.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "Confirmación de presupuesto aprobado",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.FINANZAS.value,
                "criterio_aceptacion": "Documento de aprobación presupuestal firmado",
                "ayuda_contextual": "Validar disponibilidad de fondos en centro de costos"
            },
            {
                "orden": 2,
                "descripcion": "Revisión humana si umbral de monto aplica",
                "obligatorio": False,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Firma de aprobador según matriz de autoridad",
                "ayuda_contextual": "Obligatorio si monto > umbral definido por políticas"
            }
        ],
        "total_items": 2,
        "items_obligatorios": 1,
        "activo": True
    })

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F5.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "Informe final integrado del proyecto",
                "obligatorio": True,
                "tipo_documento_esperado": "INFORME",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Informe ejecutivo + técnico con hallazgos y recomendaciones",
                "ayuda_contextual": "Debe responder a los objetivos planteados en el SIB"
            },
            {
                "orden": 2,
                "descripcion": "Modelo paramétrico/cuantitativo entregado",
                "obligatorio": True,
                "tipo_documento_esperado": "MODELO_PARAMETRICO",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Modelo funcional con documentación de uso",
                "ayuda_contextual": "Herramienta que permita replicar análisis"
            },
            {
                "orden": 3,
                "descripcion": "Manual metodológico documentado",
                "obligatorio": True,
                "tipo_documento_esperado": "MANUAL",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Documento que explique metodología aplicada",
                "ayuda_contextual": "Permite transferencia de conocimiento"
            },
            {
                "orden": 4,
                "descripcion": "Acta de aceptación técnica firmada",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.INTERNO.value,
                "criterio_aceptacion": "Firma del sponsor interno validando entregables",
                "ayuda_contextual": "Evidencia de conformidad con los entregables"
            }
        ],
        "total_items": 4,
        "items_obligatorios": 4,
        "activo": True
    })

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F6.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "Matriz de materialidad completa y validada",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.FISCAL.value,
                "criterio_aceptacion": "Todos los hechos relevantes con evidencia vinculada",
                "ayuda_contextual": "Vincula cada hecho fiscal con su soporte documental"
            },
            {
                "orden": 2,
                "descripcion": "Contrato/anexo final firmado",
                "obligatorio": True,
                "tipo_documento_esperado": "CONTRATO",
                "responsable": ResponsableChecklist.LEGAL.value,
                "criterio_aceptacion": "Contrato con firmas de ambas partes",
                "ayuda_contextual": "Versión final incorporando todos los anexos"
            },
            {
                "orden": 3,
                "descripcion": "VBC Fiscal emitido",
                "obligatorio": True,
                "tipo_documento_esperado": "VBC_FISCAL",
                "responsable": ResponsableChecklist.FISCAL.value,
                "criterio_aceptacion": "Visto bueno del área fiscal documentado",
                "ayuda_contextual": "Confirma deducibilidad del gasto"
            },
            {
                "orden": 4,
                "descripcion": "VBC Legal emitido",
                "obligatorio": True,
                "tipo_documento_esperado": "VBC_LEGAL",
                "responsable": ResponsableChecklist.LEGAL.value,
                "criterio_aceptacion": "Visto bueno del área legal documentado",
                "ayuda_contextual": "Confirma cumplimiento de obligaciones contractuales"
            }
        ],
        "total_items": 4,
        "items_obligatorios": 4,
        "activo": True
    })

    seeds.append({
        "tipologia": TipologiaProyecto.CONSULTORIA_MACRO_MERCADO.value,
        "fase": FaseProyecto.F8.value,
        "items": [
            {
                "orden": 1,
                "descripcion": "CFDI con descripción específica del servicio",
                "obligatorio": True,
                "tipo_documento_esperado": "CFDI",
                "responsable": ResponsableChecklist.PROVEEDOR.value,
                "criterio_aceptacion": "Descripción detallada que coincida con SOW",
                "ayuda_contextual": "Evitar descripciones genéricas tipo 'servicios profesionales'"
            },
            {
                "orden": 2,
                "descripcion": "Comprobante de pago bancario",
                "obligatorio": True,
                "tipo_documento_esperado": "COMPROBANTE_PAGO",
                "responsable": ResponsableChecklist.FINANZAS.value,
                "criterio_aceptacion": "Transferencia a cuenta del proveedor registrado",
                "ayuda_contextual": "Cuenta bancaria debe coincidir con la registrada"
            },
            {
                "orden": 3,
                "descripcion": "Conciliación contable completada",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.FINANZAS.value,
                "criterio_aceptacion": "Registro contable correcto en cuenta de gasto",
                "ayuda_contextual": "Verificar cuenta contable apropiada"
            },
            {
                "orden": 4,
                "descripcion": "3-way match validado (PO-Recepción-Factura)",
                "obligatorio": True,
                "tipo_documento_esperado": "OTRO",
                "responsable": ResponsableChecklist.FINANZAS.value,
                "criterio_aceptacion": "Coincidencia entre orden, recepción y factura",
                "ayuda_contextual": "Control interno fundamental para auditoría"
            }
        ],
        "total_items": 4,
        "items_obligatorios": 4,
        "activo": True
    })

    return seeds


def get_agent_config_seeds() -> List[Dict[str, Any]]:
    from models.durezza_enums import TipoAgente
    
    seeds = [
        {
            "agente": TipoAgente.A1_SPONSOR.value,
            "nombre_display": "Agente Sponsor",
            "descripcion_rol": "Valida la razón de negocios y el vínculo con objetivos estratégicos",
            "contexto_requerido": ["proyecto.nombre", "proyecto.descripcion", "proyecto.bee_objetivo", "proyecto.vinculo_plan_estrategico"],
            "normativa_relevante": [],
            "fases_donde_participa": ["F0", "F1", "F5"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.A2_PMO.value,
            "nombre_display": "Agente PMO",
            "descripcion_rol": "Gestiona el flujo del proyecto y coordina entre agentes",
            "contexto_requerido": ["proyecto.id", "proyecto.fase_actual", "proyecto.estado_global"],
            "normativa_relevante": [],
            "fases_donde_participa": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
            "puede_bloquear_avance": False,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.A3_FISCAL.value,
            "nombre_display": "Agente Fiscal",
            "descripcion_rol": "Evalúa deducibilidad fiscal y cumplimiento normativo tributario",
            "contexto_requerido": ["proyecto.monto", "proyecto.tipologia", "proveedor.rfc", "proveedor.tipo_relacion"],
            "normativa_relevante": ["CFF_5A", "CFF_69B", "LISR_27", "LISR_28", "RMF"],
            "fases_donde_participa": ["F0", "F1", "F5", "F6", "F8"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": True,
            "requiere_validacion_humana_default": True
        },
        {
            "agente": TipoAgente.A4_LEGAL.value,
            "nombre_display": "Agente Legal",
            "descripcion_rol": "Revisa aspectos contractuales y cumplimiento legal",
            "contexto_requerido": ["proyecto.nombre", "proveedor.nombre_razon_social", "proveedor.tipo_relacion"],
            "normativa_relevante": ["CCF", "LFPC", "NOM_151"],
            "fases_donde_participa": ["F1", "F6"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": True,
            "requiere_validacion_humana_default": True
        },
        {
            "agente": TipoAgente.A5_FINANZAS.value,
            "nombre_display": "Agente Finanzas",
            "descripcion_rol": "Valida aspectos presupuestales y financieros",
            "contexto_requerido": ["proyecto.monto", "proyecto.moneda", "proyecto.bee_roi_esperado"],
            "normativa_relevante": [],
            "fases_donde_participa": ["F2", "F8"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.A6_PROVEEDOR.value,
            "nombre_display": "Agente Proveedor",
            "descripcion_rol": "Evalúa riesgos asociados al proveedor",
            "contexto_requerido": ["proveedor.rfc", "proveedor.tipo_relacion", "proveedor.alerta_efos", "proveedor.historial_riesgo_score"],
            "normativa_relevante": ["CFF_69B"],
            "fases_donde_participa": ["F0", "F1"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.A7_DEFENSA.value,
            "nombre_display": "Agente Defensa",
            "descripcion_rol": "Construye y valida el defense file probatorio",
            "contexto_requerido": ["proyecto.id", "defense_file.documentos", "defense_file.matriz_materialidad"],
            "normativa_relevante": ["CFF_5A", "CFF_42", "LISR_27"],
            "fases_donde_participa": ["F5", "F6", "F9"],
            "puede_bloquear_avance": False,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.SUB_TIPIFICACION.value,
            "nombre_display": "Sub-Agente Tipificación",
            "descripcion_rol": "Clasifica el tipo de proyecto y determina checklist aplicable",
            "contexto_requerido": ["proyecto.descripcion", "proyecto.tipologia"],
            "normativa_relevante": [],
            "fases_donde_participa": ["F0"],
            "puede_bloquear_avance": False,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.SUB_MATERIALIDAD.value,
            "nombre_display": "Sub-Agente Materialidad",
            "descripcion_rol": "Evalúa la materialidad de la evidencia documental",
            "contexto_requerido": ["defense_file.documentos", "defense_file.matriz_materialidad"],
            "normativa_relevante": ["CFF_5A"],
            "fases_donde_participa": ["F5", "F6"],
            "puede_bloquear_avance": False,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": False
        },
        {
            "agente": TipoAgente.SUB_RIESGOS_ESPECIALES.value,
            "nombre_display": "Sub-Agente Riesgos Especiales",
            "descripcion_rol": "Identifica riesgos especiales como partes relacionadas y REFIPRES",
            "contexto_requerido": ["proveedor.tipo_relacion", "proveedor.jurisdiccion", "proyecto.monto"],
            "normativa_relevante": ["LISR_76", "LISR_179", "LISR_180"],
            "fases_donde_participa": ["F0", "F1"],
            "puede_bloquear_avance": True,
            "puede_aprobar_final": False,
            "requiere_validacion_humana_default": True
        }
    ]
    
    return seeds
