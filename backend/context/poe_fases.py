"""
POE Fases F0-F9 - Revisar.IA
Sistema de Auditoría de Intangibles

Procedimiento Operativo Estándar para las 10 fases del flujo de auditoría.
Cada fase tiene sus documentos mínimos, agentes obligatorios, condiciones
de avance y bloqueos.
"""

from typing import Dict, List, Any, Optional

POE_FASES: Dict[str, Dict[str, Any]] = {
    
    "F0": {
        "nombre": "Aprobación - Definir BEE y elegibilidad",
        "objetivo": "Validar que el proyecto tiene razón de negocios y beneficio económico esperado suficientes para iniciar.",
        
        "documentos_minimos": [
            {
                "nombre": "SIB con BEE",
                "descripcion": "Service Initiation Brief que incluya: objetivo del servicio, Beneficio Económico Esperado (BEE) con ROI estimado y horizonte temporal, vinculación con Plan Estratégico.",
                "obligatorio": True,
                "tipo_documento": "SIB_BEE"
            },
            {
                "nombre": "Evaluación inicial de riesgo fiscal",
                "descripcion": "Análisis preliminar de A3-Fiscal sobre los 4 pilares y risk_score inicial.",
                "obligatorio": True,
                "tipo_documento": "EVALUACION_RIESGO"
            }
        ],
        
        "agentes_obligatorios": ["A1_SPONSOR", "A3_FISCAL", "SUB_TIPIFICACION"],
        
        "condicion_avance": "BEE definido con objetivo económico específico + evaluación inicial de riesgo fiscal completada + tipología asignada. A1 y A3 deben tener decisión APROBAR o APROBAR_CONDICIONES.",
        
        "bloqueos": [
            "BEE inexistente o con objetivo económico no cuantificable",
            "Falta de vínculo razonable con el negocio",
            "Señales claras de simulación o EFOS en el proveedor",
            "A3-Fiscal con decisión RECHAZAR"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "Proyecto clasificado (tipología asignada), BEE documentado, risk_score inicial calculado, decisión de proceder o no."
    },
    
    "F1": {
        "nombre": "Pre-contratación / SOW inicial",
        "objetivo": "Formalizar el alcance del servicio antes de iniciar ejecución.",
        
        "documentos_minimos": [
            {
                "nombre": "SOW / Orden de trabajo",
                "descripcion": "Documento con: objeto claro, alcance general, lista de entregables esperados, esquema de honorarios/hitos, criterios de aceptación preliminares.",
                "obligatorio": True,
                "tipo_documento": "SOW"
            },
            {
                "nombre": "Registro de fecha cierta/trazabilidad",
                "descripcion": "Mecanismo de timestamp o registro que demuestre cuándo se formalizó el SOW.",
                "obligatorio": True,
                "tipo_documento": "REGISTRO_TIMESTAMP"
            }
        ],
        
        "agentes_obligatorios": ["A4_LEGAL"],
        
        "condicion_avance": "SOW/orden aprobado por Legal con objeto, alcance, entregables y esquema de precio claros. Sin vicios formales graves.",
        
        "bloqueos": [
            "Objeto ambiguo o ininteligible",
            "Ausencia total de esquema de precio/honorarios",
            "Entregables no especificados",
            "Problemas formales graves (partes incorrectas, representante sin facultades)"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "SOW/orden de trabajo formalizado y validado por Legal, listo para confirmación de presupuesto."
    },
    
    "F2": {
        "nombre": "Validación previa al inicio de ejecución",
        "objetivo": "Confirmar que hay presupuesto y que se puede proceder a ejecutar el servicio.",
        
        "documentos_minimos": [
            {
                "nombre": "Confirmación de presupuesto",
                "descripcion": "Validación de Finanzas de que existe presupuesto disponible para el proyecto.",
                "obligatorio": True,
                "tipo_documento": "CONFIRMACION_PRESUPUESTO"
            },
            {
                "nombre": "Revisión humana si aplica",
                "descripcion": "Si el proyecto excede umbrales, documentar la revisión y aprobación humana.",
                "obligatorio": False,
                "tipo_documento": "APROBACION_HUMANA"
            }
        ],
        
        "agentes_obligatorios": ["A5_FINANZAS", "A2_PMO"],
        
        "condicion_avance": "F0 y F1 completados + presupuesto confirmado + revisión humana obtenida si aplica.",
        
        "bloqueos": [
            "Sin presupuesto disponible",
            "Riesgo fiscal alto sin revisión humana que lo asuma/mitigue",
            "F0 o F1 no completados",
            "Roles responsables no han dado 'go'"
        ],
        
        "es_candado_duro": True,
        "candado_descripcion": "NINGÚN PROVEEDOR PUEDE INICIAR TRABAJOS si el proyecto no ha alcanzado F2 COMPLETADA.",
        "resultado_esperado": "Autorización para que el proveedor inicie ejecución del servicio."
    },
    
    "F3": {
        "nombre": "Ejecución inicial / Primera versión del entregable",
        "objetivo": "Registrar el inicio de la ejecución y obtener primera versión del entregable.",
        
        "documentos_minimos": [
            {
                "nombre": "Entregable V1",
                "descripcion": "Primera versión identificable del entregable (borrador, versión preliminar).",
                "obligatorio": True,
                "tipo_documento": "ENTREGABLE"
            },
            {
                "nombre": "Logs/evidencias de actividades",
                "descripcion": "Minutas de kick-off, correos de inicio, cronograma de trabajo.",
                "obligatorio": True,
                "tipo_documento": "EVIDENCIA_EJECUCION"
            }
        ],
        
        "agentes_obligatorios": ["A6_PROVEEDOR"],
        
        "condicion_avance": "Al menos una versión de entregable con rastro documental de inicio de actividades.",
        
        "bloqueos": [
            "No hay entregable identificable",
            "No hay rastro documental de ejecución"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "Evidencia de que el servicio comenzó a ejecutarse, con entregable preliminar."
    },
    
    "F4": {
        "nombre": "Revisión iterativa",
        "objetivo": "Proceso de ajuste del entregable hasta que cumpla criterios de calidad.",
        
        "documentos_minimos": [
            {
                "nombre": "Versiones sucesivas del entregable",
                "descripcion": "V1, V1.2, V2, etc. con registro de cambios.",
                "obligatorio": True,
                "tipo_documento": "ENTREGABLE"
            },
            {
                "nombre": "Registro de ajustes",
                "descripcion": "Documentación de observaciones recibidas y cómo se atendieron.",
                "obligatorio": True,
                "tipo_documento": "REGISTRO_AJUSTES"
            }
        ],
        
        "agentes_obligatorios": ["A1_SPONSOR", "A3_FISCAL", "A5_FINANZAS"],
        
        "condicion_avance": "Entregable cumple criterios estratégicos mínimos, consistencia económica y calidad técnica suficiente según los agentes.",
        
        "bloqueos": [
            "Brechas graves persistentes en uno o más pilares",
            "Incapacidad del proveedor para atender observaciones críticas"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "Entregable refinado que cumple criterios de los agentes, listo para aceptación técnica."
    },
    
    "F5": {
        "nombre": "Entrega final / Aceptación técnica",
        "objetivo": "Formalizar la aceptación del entregable final.",
        
        "documentos_minimos": [
            {
                "nombre": "Entregable final",
                "descripcion": "Versión definitiva del entregable, completa y versionada.",
                "obligatorio": True,
                "tipo_documento": "ENTREGABLE_FINAL"
            },
            {
                "nombre": "Acta de aceptación técnica",
                "descripcion": "Documento donde la unidad usuaria acepta formalmente el entregable.",
                "obligatorio": True,
                "tipo_documento": "ACTA_ACEPTACION"
            }
        ],
        
        "agentes_obligatorios": ["A1_SPONSOR", "SUB_MATERIALIDAD"],
        
        "condicion_avance": "Entregable completo + acta de aceptación técnica firmada + matriz de materialidad actualizada.",
        
        "bloqueos": [
            "Entregable incongruente con SOW",
            "Desacuerdos técnicos sin resolver",
            "Falta de aceptación técnica formal"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "Entregable aceptado, listo para validación fiscal/legal."
    },
    
    "F6": {
        "nombre": "Visto Bueno Fiscal/Legal (VBC)",
        "objetivo": "Obtener aprobación fiscal y legal antes de comprometer el pago.",
        
        "documentos_minimos": [
            {
                "nombre": "Matriz de materialidad completa",
                "descripcion": "Tabla que vincula cada hecho relevante con su evidencia, verificando completitud.",
                "obligatorio": True,
                "tipo_documento": "MATRIZ_MATERIALIDAD"
            },
            {
                "nombre": "Contrato/anexo final",
                "descripcion": "Documento contractual definitivo que refleja la realidad del servicio.",
                "obligatorio": True,
                "tipo_documento": "CONTRATO"
            },
            {
                "nombre": "VBC Fiscal",
                "descripcion": "Documento de A3-Fiscal aprobando el proyecto desde perspectiva tributaria.",
                "obligatorio": True,
                "tipo_documento": "VBC_FISCAL"
            },
            {
                "nombre": "VBC Legal",
                "descripcion": "Documento de A4-Legal aprobando el proyecto desde perspectiva jurídica.",
                "obligatorio": True,
                "tipo_documento": "VBC_LEGAL"
            }
        ],
        
        "agentes_obligatorios": ["A3_FISCAL", "A4_LEGAL", "SUB_MATERIALIDAD"],
        
        "condicion_avance": "Matriz de materialidad completa (>80%) + VBC de Fiscal + VBC de Legal + contrato final alineado con realidad.",
        
        "bloqueos": [
            "Falta de evidencia clave de ejecución",
            "Contradicciones graves entre SIB, SOW, entregables y contrato",
            "Riesgo fiscal que Fiscal califique como inaceptable",
            "A3 o A4 con decisión distinta a APROBAR"
        ],
        
        "es_candado_duro": True,
        "candado_descripcion": "NO SE PUEDE EMITIR CFDI NI AUTORIZAR PAGO sin F6 completada con VBC de Fiscal y Legal.",
        "resultado_esperado": "Proyecto aprobado fiscalmente, listo para facturación y pago."
    },
    
    "F7": {
        "nombre": "Auditoría interna / Control",
        "objetivo": "Verificar que todo el proceso se siguió correctamente.",
        
        "documentos_minimos": [
            {
                "nombre": "Informe de auditoría interna",
                "descripcion": "Revisión de que se siguió el POE, el Defense File está completo, no se omitieron revisiones.",
                "obligatorio": True,
                "tipo_documento": "INFORME_AUDITORIA"
            }
        ],
        
        "agentes_obligatorios": ["A2_PMO"],
        
        "condicion_avance": "Informe de auditoría confirma que el POE se siguió correctamente y Defense File está completo.",
        
        "bloqueos": [
            "Omisiones detectadas en fases previas",
            "Defense File incompleto",
            "Se detecta que se saltaron revisiones humanas obligatorias"
        ],
        
        "es_candado_duro": False,
        "resultado_esperado": "Confirmación de que el proyecto cumple con controles internos."
    },
    
    "F8": {
        "nombre": "CFDI y pago (3-way match)",
        "objetivo": "Ejecutar el pago con validación de 3-way match.",
        
        "documentos_minimos": [
            {
                "nombre": "CFDI específico",
                "descripcion": "Factura con descripción que coincida con contrato y entregables (no genérica).",
                "obligatorio": True,
                "tipo_documento": "CFDI"
            },
            {
                "nombre": "Comprobante de pago",
                "descripcion": "Evidencia de transferencia bancaria.",
                "obligatorio": True,
                "tipo_documento": "COMPROBANTE_PAGO"
            },
            {
                "nombre": "Conciliación contable",
                "descripcion": "Registro contable del gasto.",
                "obligatorio": True,
                "tipo_documento": "CONCILIACION_CONTABLE"
            }
        ],
        
        "agentes_obligatorios": ["A5_FINANZAS"],
        
        "condicion_avance": "CFDI coincide con objeto y monto del contrato + pago realizado por medios trazables + registro contable completo.",
        
        "bloqueos": [
            "CFDI genérico ('servicios profesionales varios')",
            "CFDI incongruente con contrato",
            "Pago pretendido sin VBC o sin F7 completo"
        ],
        
        "es_candado_duro": True,
        "candado_descripcion": "NO SE PUEDE LIBERAR PAGO sin 3-way match validado y VBC previo.",
        "resultado_esperado": "Pago ejecutado y registrado correctamente."
    },
    
    "F9": {
        "nombre": "Post-implementación / Verificación del BEE",
        "objetivo": "Evaluar si el beneficio económico esperado se está materializando.",
        
        "documentos_minimos": [
            {
                "nombre": "Informe de seguimiento BEE",
                "descripcion": "Análisis de si los beneficios esperados se están cumpliendo, con explicación de desviaciones.",
                "obligatorio": True,
                "tipo_documento": "INFORME_BEE"
            }
        ],
        
        "agentes_obligatorios": ["A1_SPONSOR"],
        
        "condicion_avance": "Al menos una revisión ex post documentada.",
        
        "bloqueos": [
            "Ausencia total de revisión ex post en proyectos de alto impacto"
        ],
        
        "es_candado_duro": False,
        "periodicidad": "6, 12 o 24 meses después del cierre según tipo de proyecto",
        "resultado_esperado": "Documentación de si el BEE se cumplió, aprendizajes para futuros proyectos."
    }
}


def obtener_config_fase(fase: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración completa de una fase.
    """
    return POE_FASES.get(fase)


def es_candado_duro(fase: str) -> bool:
    """
    Determina si una fase es un candado duro (gate obligatorio).
    """
    config = POE_FASES.get(fase)
    if config:
        return config.get("es_candado_duro", False)
    return False


def get_bloqueos_fase(fase: str) -> List[str]:
    """
    Obtiene los bloqueos posibles de una fase.
    """
    config = POE_FASES.get(fase)
    if config:
        return config.get("bloqueos", [])
    return []


def get_agentes_obligatorios(fase: str) -> List[str]:
    """
    Obtiene los agentes obligatorios para una fase.
    """
    config = POE_FASES.get(fase)
    if config:
        return config.get("agentes_obligatorios", [])
    return []


def get_documentos_minimos(fase: str) -> List[Dict[str, Any]]:
    """
    Obtiene los documentos mínimos requeridos para una fase.
    """
    config = POE_FASES.get(fase)
    if config:
        return config.get("documentos_minimos", [])
    return []


def get_condicion_avance(fase: str) -> Optional[str]:
    """
    Obtiene la condición de avance para una fase.
    """
    config = POE_FASES.get(fase)
    if config:
        return config.get("condicion_avance")
    return None


def listar_fases() -> List[str]:
    """
    Lista todas las fases en orden.
    """
    return ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]


def get_candados_duros() -> List[str]:
    """
    Obtiene todas las fases que son candados duros.
    """
    return [fase for fase in POE_FASES if POE_FASES[fase].get("es_candado_duro", False)]


def get_fase_siguiente(fase_actual: str) -> Optional[str]:
    """
    Obtiene la siguiente fase después de la actual.
    """
    fases = listar_fases()
    try:
        idx = fases.index(fase_actual)
        if idx < len(fases) - 1:
            return fases[idx + 1]
    except ValueError:
        pass
    return None


def get_fase_anterior(fase_actual: str) -> Optional[str]:
    """
    Obtiene la fase anterior a la actual.
    """
    fases = listar_fases()
    try:
        idx = fases.index(fase_actual)
        if idx > 0:
            return fases[idx - 1]
    except ValueError:
        pass
    return None
