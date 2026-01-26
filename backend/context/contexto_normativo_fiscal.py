"""
Contexto Normativo Fiscal - Revisar.IA
Sistema de Auditoría de Intangibles

Este módulo contiene la normativa fiscal mexicana aplicable al sistema,
incluyendo CFF, LISR, NOM-151 y RMF relevantes para servicios intangibles.
"""

from typing import Dict, List, Any

CONTEXTO_NORMATIVO: Dict[str, Any] = {
    
    "CFF": {
        "articulo_5A": {
            "nombre": "Razón de negocios y beneficio económico",
            "texto_clave": "Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente.",
            "aplicacion_sistema": "Todo proyecto de servicio/intangible debe demostrar que tiene una justificación económica real más allá del ahorro o beneficio fiscal. El sistema debe verificar que existe un objetivo económico concreto, medible, con horizonte temporal definido.",
            "criterios_evaluacion": [
                "¿El servicio está vinculado al giro del contribuyente?",
                "¿Existe un objetivo económico específico y cuantificable?",
                "¿El monto es proporcional al beneficio esperado y escala del negocio?",
                "¿Hay un ROI razonablemente esperado documentado?",
                "¿El horizonte temporal del beneficio es congruente con la naturaleza del servicio?"
            ],
            "consecuencias_incumplimiento": "La autoridad puede recaracterizar la operación y negar efectos fiscales favorables, incluyendo deducciones."
        },
        
        "articulo_69B": {
            "nombre": "Operaciones inexistentes y materialidad",
            "texto_clave": "Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes...",
            "aplicacion_sistema": "El sistema debe verificar que existe evidencia concreta de que el servicio se prestó realmente. No basta con tener contrato y CFDI; se requieren entregables, minutas, cronogramas, logs de trabajo, y coherencia entre todos los documentos.",
            "criterios_evaluacion": [
                "¿Existe contrato/SOW con objeto, alcance y entregables claros?",
                "¿Hay entregables tangibles que demuestren la ejecución?",
                "¿Existen minutas o registros de sesiones de trabajo?",
                "¿El CFDI es específico (no 'servicios profesionales varios')?",
                "¿Hay coherencia entre contrato, entregables, CFDI y pago?",
                "¿Se puede reconstruir un timeline lógico de la operación?"
            ],
            "consecuencias_incumplimiento": "Inclusión en lista de operaciones inexistentes, no deducibilidad del gasto, posible delito fiscal."
        },
        
        "articulo_69B_bis": {
            "nombre": "Transmisión indebida de pérdidas fiscales",
            "aplicacion_sistema": "Identificar si los servicios o intangibles forman parte de un esquema para transmitir pérdidas entre partes relacionadas."
        },
        
        "articulo_42": {
            "nombre": "Facultades de comprobación",
            "aplicacion_sistema": "Define las facultades de la autoridad para revisar operaciones. El Defense File debe estar preparado para responder requerimientos de información."
        }
    },
    
    "LISR": {
        "articulo_27": {
            "nombre": "Requisitos de las deducciones",
            "texto_clave": "Las deducciones autorizadas deberán reunir los siguientes requisitos: I. Ser estrictamente indispensables para los fines de la actividad del contribuyente...",
            "aplicacion_sistema": "El gasto en servicios/intangibles debe ser estrictamente indispensable para la actividad preponderante del contribuyente. No basta con que sea 'útil' o 'conveniente'; debe demostrarse que sin él la operación del negocio se vería afectada.",
            "criterios_evaluacion": [
                "¿El servicio se relaciona directamente con la actividad preponderante?",
                "¿Es un gasto que cualquier empresa del mismo giro haría?",
                "¿Existe justificación de por qué no se hace internamente?",
                "¿El resultado del servicio se usa efectivamente en el negocio?"
            ],
            "consecuencias_incumplimiento": "Rechazo de la deducción, ajuste al ISR, actualizaciones, recargos y posibles multas."
        },
        
        "articulo_28_fracciones": {
            "nombre": "Gastos no deducibles relacionados",
            "aplicacion_sistema": "Verificar que el gasto no caiga en supuestos de no deducibilidad como pagos a EFOS, gastos sin requisitos fiscales, etc."
        },
        
        "articulo_76": {
            "nombre": "Obligaciones de contribuyentes",
            "aplicacion_sistema": "Obligaciones de documentación y conservación de información para operaciones con partes relacionadas."
        },
        
        "articulo_179": {
            "nombre": "Precios de transferencia - partes relacionadas nacionales",
            "aplicacion_sistema": "Principio de arm's length para operaciones entre partes relacionadas nacionales."
        },
        
        "articulo_180": {
            "nombre": "Métodos de precios de transferencia",
            "aplicacion_sistema": "Metodologías aplicables para determinar precios de operaciones entre partes relacionadas."
        }
    },
    
    "NOM_151": {
        "nombre": "Conservación de mensajes de datos y digitalización",
        "aplicacion_sistema": "Todos los documentos del Defense File deben tener: integridad verificable (hash SHA-256), fecha cierta (timestamp confiable), y conservación adecuada. El sistema debe calcular y almacenar hashes de integridad para cada documento.",
        "criterios_evaluacion": [
            "¿Los documentos tienen fecha cierta verificable?",
            "¿Se puede demostrar que no han sido alterados?",
            "¿Existe un expediente digital estructurado?",
            "¿Se puede reconstruir la secuencia temporal de eventos?"
        ],
        "requisitos_tecnicos": [
            "Hash SHA-256 para cada documento",
            "Timestamp confiable (NTP sincronizado)",
            "Firma digital cuando aplique",
            "Conservación por período legal (5 años mínimo)"
        ]
    },
    
    "RMF": {
        "intangibles_dificiles_valorar": {
            "nombre": "Reglas para activos intangibles difíciles de valorar",
            "aplicacion_sistema": "Para servicios que generan intangibles (software, estudios, metodologías), se requiere documentación detallada sobre valoración, supuestos utilizados, y metodología. Especialmente relevante en operaciones con partes relacionadas.",
            "documentacion_requerida": [
                "Descripción detallada del intangible",
                "Metodología de valoración aplicada",
                "Supuestos y proyecciones utilizadas",
                "Comparables de mercado si existen",
                "Justificación del precio pactado"
            ]
        },
        
        "esquemas_reportables": {
            "nombre": "Esquemas reportables",
            "aplicacion_sistema": "Identificar si la operación podría constituir un esquema reportable, especialmente en: operaciones con partes relacionadas, transferencias de intangibles, y estructuras que generan beneficios fiscales significativos."
        },
        
        "precios_transferencia": {
            "nombre": "Documentación de precios de transferencia",
            "aplicacion_sistema": "Para operaciones intra-grupo o con partes relacionadas, verificar existencia de estudio de TP, método aplicado, y comparables."
        }
    }
}


def obtener_normativa(ley: str, articulo: str = None) -> Dict[str, Any]:
    """
    Obtiene la normativa fiscal especificada.
    
    Args:
        ley: Código de la ley (CFF, LISR, NOM_151, RMF)
        articulo: Artículo específico (opcional)
    
    Returns:
        Diccionario con la normativa o None si no existe
    """
    if ley not in CONTEXTO_NORMATIVO:
        return None
    
    if articulo is None:
        return CONTEXTO_NORMATIVO[ley]
    
    return CONTEXTO_NORMATIVO[ley].get(articulo)


def obtener_criterios_evaluacion(ley: str, articulo: str) -> List[str]:
    """
    Obtiene los criterios de evaluación para un artículo específico.
    """
    normativa = obtener_normativa(ley, articulo)
    if normativa and "criterios_evaluacion" in normativa:
        return normativa["criterios_evaluacion"]
    return []


def obtener_normativa_por_pilar(pilar: str) -> Dict[str, Any]:
    """
    Obtiene la normativa aplicable según el pilar de evaluación.
    
    Args:
        pilar: RAZON_NEGOCIO, BENEFICIO_ECONOMICO, MATERIALIDAD, TRAZABILIDAD
    
    Returns:
        Diccionario con la normativa relevante al pilar
    """
    mapeo_pilares = {
        "RAZON_NEGOCIO": {
            "principal": CONTEXTO_NORMATIVO["CFF"]["articulo_5A"],
            "complementaria": [
                CONTEXTO_NORMATIVO["LISR"]["articulo_27"]
            ]
        },
        "BENEFICIO_ECONOMICO": {
            "principal": CONTEXTO_NORMATIVO["CFF"]["articulo_5A"],
            "complementaria": [
                CONTEXTO_NORMATIVO["LISR"]["articulo_27"],
                CONTEXTO_NORMATIVO["RMF"]["intangibles_dificiles_valorar"]
            ]
        },
        "MATERIALIDAD": {
            "principal": CONTEXTO_NORMATIVO["CFF"]["articulo_69B"],
            "complementaria": [
                CONTEXTO_NORMATIVO["NOM_151"]
            ]
        },
        "TRAZABILIDAD": {
            "principal": CONTEXTO_NORMATIVO["NOM_151"],
            "complementaria": [
                CONTEXTO_NORMATIVO["CFF"]["articulo_69B"]
            ]
        }
    }
    
    return mapeo_pilares.get(pilar)
