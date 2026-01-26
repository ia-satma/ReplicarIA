"""
Definición de contexto requerido por cada agente.
Especifica qué campos son OBLIGATORIOS vs DESEABLES para que cada
agente pueda deliberar correctamente.
"""

from typing import Dict, List
from enum import Enum


class NivelRequerimiento(str, Enum):
    OBLIGATORIO = "obligatorio"
    DESEABLE = "deseable"
    NO_NECESITA = "no_necesita"


CONTEXTO_POR_AGENTE: Dict[str, Dict] = {
    
    "A1_SPONSOR": {
        "descripcion": "Valida alineación estratégica y razón de negocios",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.descripcion",
                "proyecto.objetivo_declarado",
                "proyecto.monto",
                "proyecto.tipologia",
                "empresa.giro_principal",
                "empresa.plan_estrategico_resumen"
            ],
            "deseable": [
                "proyecto.area_solicitante",
                "proyecto.sponsor_nombre",
                "historico.proyectos_similares",
                "empresa.objetivos_anuales"
            ],
            "no_necesita": [
                "proveedor.datos_bancarios",
                "documentos.cfdi",
                "proyecto.three_way_match"
            ]
        },
        "output_esperado": [
            "validacion_razon_negocios",
            "alineacion_estrategica",
            "recomendacion"
        ]
    },
    
    "A2_PMO": {
        "descripcion": "Valida viabilidad operativa y gestión del proyecto",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.descripcion",
                "proyecto.monto",
                "proyecto.cronograma_estimado",
                "proyecto.entregables_esperados",
                "proyecto.fase_actual"
            ],
            "deseable": [
                "proyecto.riesgos_identificados",
                "proyecto.dependencias",
                "historico.proyectos_area",
                "recursos.disponibilidad"
            ],
            "no_necesita": [
                "proveedor.rfc",
                "documentos.estudio_tp",
                "empresa.estructura_accionaria"
            ]
        },
        "output_esperado": [
            "viabilidad_operativa",
            "riesgos_ejecucion",
            "recomendacion_cronograma"
        ]
    },
    
    "A3_FISCAL": {
        "descripcion": "Evalúa cumplimiento fiscal y riesgo tributario",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.descripcion",
                "proyecto.monto",
                "proyecto.tipologia",
                "proveedor.rfc",
                "proveedor.tipo_relacion",
                "proveedor.alerta_efos",
                "documentos.sib_bee",
                "documentos.contrato"
            ],
            "deseable": [
                "proveedor.historial_operaciones",
                "documentos.sow",
                "documentos.entregables",
                "historico.risk_scores_similares",
                "contexto_normativo.cff_5a",
                "contexto_normativo.cff_69b"
            ],
            "no_necesita": [
                "empresa.organigrama",
                "proyecto.minutas_internas"
            ]
        },
        "output_esperado": [
            "conclusion_por_pilar",
            "checklist_evidencia_exigible",
            "risk_score_calculado",
            "decision",
            "justificacion"
        ],
        "validaciones_especiales": {
            "checklist_evidencia_exigible": {"min_items": 3},
            "conclusion_por_pilar": {"pilares_requeridos": ["razon_negocios", "beneficio_economico", "materialidad", "trazabilidad"]}
        }
    },
    
    "A4_LEGAL": {
        "descripcion": "Evalúa cumplimiento legal y contractual",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.descripcion",
                "proyecto.monto",
                "proveedor.razon_social",
                "proveedor.tipo_relacion",
                "documentos.contrato",
                "documentos.anexos_tecnicos"
            ],
            "deseable": [
                "documentos.sow",
                "documentos.acta_aceptacion",
                "proveedor.representante_legal",
                "historico.contratos_proveedor"
            ],
            "no_necesita": [
                "proyecto.roi_esperado",
                "empresa.estados_financieros"
            ]
        },
        "output_esperado": [
            "validacion_contractual",
            "riesgos_legales",
            "clausulas_faltantes",
            "recomendacion"
        ]
    },
    
    "A5_FINANZAS": {
        "descripcion": "Evalúa impacto financiero y presupuestal",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.monto",
                "proyecto.moneda",
                "proyecto.forma_pago",
                "empresa.presupuesto_area",
                "empresa.flujo_caja_disponible"
            ],
            "deseable": [
                "proyecto.roi_esperado",
                "proyecto.payback_esperado",
                "historico.gastos_similares",
                "empresa.tipo_cambio_presupuestado"
            ],
            "no_necesita": [
                "proveedor.alerta_efos",
                "documentos.entregables_tecnicos"
            ]
        },
        "output_esperado": [
            "impacto_presupuestal",
            "disponibilidad_recursos",
            "recomendacion_financiera"
        ]
    },
    
    "A6_PROVEEDOR": {
        "descripcion": "Evalúa capacidad y riesgo del proveedor",
        "contexto_requerido": {
            "obligatorio": [
                "proveedor.rfc",
                "proveedor.razon_social",
                "proveedor.tipo_relacion",
                "proveedor.alerta_efos",
                "proveedor.fecha_constitucion",
                "proyecto.tipologia",
                "proyecto.monto"
            ],
            "deseable": [
                "proveedor.empleados_estimados",
                "proveedor.certificaciones",
                "proveedor.clientes_referencia",
                "historico.operaciones_proveedor",
                "proveedor.estados_financieros"
            ],
            "no_necesita": [
                "empresa.plan_estrategico",
                "proyecto.minutas"
            ]
        },
        "output_esperado": [
            "evaluacion_capacidad",
            "riesgo_proveedor",
            "alertas_detectadas",
            "recomendacion"
        ]
    },
    
    "A7_DEFENSA": {
        "descripcion": "Genera Defense File y evalúa defendibilidad",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.id",
                "proyecto.nombre",
                "proyecto.tipologia",
                "proyecto.monto",
                "proyecto.risk_score_total",
                "proyecto.risk_score_razon_negocios",
                "proyecto.risk_score_beneficio_economico",
                "proyecto.risk_score_materialidad",
                "proyecto.risk_score_trazabilidad",
                "deliberaciones.todas",
                "documentos.todos",
                "matriz_materialidad",
                "vbc.fiscal",
                "vbc.legal"
            ],
            "deseable": [
                "historial.fases",
                "minutas.todas",
                "correspondencia.relevante"
            ],
            "no_necesita": []
        },
        "output_esperado": [
            "defense_file_completo",
            "indice_defendibilidad",
            "evaluacion_por_criterio",
            "argumentos_defensa",
            "puntos_vulnerables",
            "recomendaciones_refuerzo"
        ]
    },
    
    "A8_AUDITOR": {
        "descripcion": "Audita documentos y verifica cumplimiento",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.id",
                "proyecto.nombre",
                "proyecto.tipologia",
                "documentos.todos",
                "defense_file.estructura",
                "deliberaciones.consolidado"
            ],
            "deseable": [
                "checklist.completitud",
                "validaciones_ocr",
                "historial.ajustes"
            ],
            "no_necesita": [
                "empresa.plan_estrategico",
                "proveedor.datos_bancarios"
            ]
        },
        "output_esperado": [
            "resultado_auditoria",
            "documentos_faltantes",
            "ajustes_requeridos",
            "score_cumplimiento"
        ]
    },
    
    "SUB_TIPIFICACION": {
        "descripcion": "Clasifica proyectos en tipología correcta",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.nombre",
                "proyecto.descripcion",
                "proyecto.objetivo_declarado",
                "proveedor.tipo_relacion",
                "proyecto.monto"
            ],
            "deseable": [
                "documentos.sow_preliminar",
                "proyecto.entregables_esperados"
            ],
            "no_necesita": [
                "deliberaciones.previas",
                "documentos.cfdi"
            ]
        },
        "output_esperado": [
            "tipologia_asignada",
            "confianza_clasificacion",
            "justificacion",
            "alertas_tipologia"
        ]
    },
    
    "SUB_MATERIALIDAD": {
        "descripcion": "Monitorea matriz de materialidad",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.id",
                "proyecto.tipologia",
                "proyecto.fase_actual",
                "documentos.cargados",
                "checklist.tipologia_fase"
            ],
            "deseable": [
                "deliberaciones.previas",
                "defense_file.actual"
            ],
            "no_necesita": [
                "empresa.datos_generales",
                "proveedor.datos_bancarios"
            ]
        },
        "output_esperado": [
            "matriz_materialidad",
            "completitud_porcentaje",
            "brechas_criticas",
            "puede_emitir_vbc"
        ]
    },
    
    "SUB_RIESGOS_ESPECIALES": {
        "descripcion": "Detecta EFOS, TP, esquemas reportables",
        "contexto_requerido": {
            "obligatorio": [
                "proyecto.id",
                "proyecto.descripcion",
                "proyecto.monto",
                "proyecto.tipologia",
                "proveedor.rfc",
                "proveedor.tipo_relacion",
                "proveedor.alerta_efos",
                "proveedor.historial_riesgo_score"
            ],
            "deseable": [
                "lista_69b_sat",
                "proyectos.similares_proveedor"
            ],
            "no_necesita": [
                "empresa.organigrama",
                "documentos.minutas"
            ]
        },
        "output_esperado": [
            "alertas_detectadas",
            "nivel_riesgo_global",
            "puede_continuar",
            "requiere_revision_humana_inmediata"
        ]
    }
}


def get_contexto_requerido(agente_id: str) -> Dict:
    """Obtiene la configuración de contexto para un agente"""
    return CONTEXTO_POR_AGENTE.get(agente_id, {})


def get_campos_obligatorios(agente_id: str) -> List[str]:
    """Obtiene lista de campos obligatorios para un agente"""
    config = CONTEXTO_POR_AGENTE.get(agente_id, {})
    return config.get("contexto_requerido", {}).get("obligatorio", [])


def get_campos_deseables(agente_id: str) -> List[str]:
    """Obtiene lista de campos deseables para un agente"""
    config = CONTEXTO_POR_AGENTE.get(agente_id, {})
    return config.get("contexto_requerido", {}).get("deseable", [])


def validar_contexto_completo(agente_id: str, contexto: Dict) -> Dict:
    """
    Valida si el contexto tiene todos los campos obligatorios.
    
    Returns:
        {
            "completo": bool,
            "campos_faltantes": list,
            "campos_presentes": list,
            "porcentaje_completitud": float
        }
    """
    obligatorios = get_campos_obligatorios(agente_id)
    
    campos_faltantes = []
    campos_presentes = []
    
    for campo in obligatorios:
        valor = contexto
        try:
            for parte in campo.split('.'):
                valor = valor.get(parte) if isinstance(valor, dict) else None
            
            if valor is not None and valor != "" and valor != []:
                campos_presentes.append(campo)
            else:
                campos_faltantes.append(campo)
        except:
            campos_faltantes.append(campo)
    
    total = len(obligatorios)
    presentes = len(campos_presentes)
    
    return {
        "completo": len(campos_faltantes) == 0,
        "campos_faltantes": campos_faltantes,
        "campos_presentes": campos_presentes,
        "porcentaje_completitud": (presentes / total * 100) if total > 0 else 100
    }
