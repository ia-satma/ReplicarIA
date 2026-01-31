"""
SUB_MATERIALIDAD - Subagente de Monitoreo de Materialidad

Monitorea continuamente la matriz de materialidad del proyecto, verificando
que cada hecho relevante tenga evidencia documental asociada. Calcula el
porcentaje de completitud y alerta cuando hay brechas críticas.
"""

from typing import Dict, Any, List, Optional

SUB_MATERIALIDAD_CONFIG = {
    "id": "SUB_MATERIALIDAD",
    "nombre": "Subagente de Monitoreo de Materialidad",
    
    "rol": """Monitorear continuamente la matriz de materialidad del proyecto, 
    verificando que cada hecho relevante (contratación, ejecución, entrega, pago) 
    tenga evidencia documental asociada. Calcular el porcentaje de completitud 
    y alertar cuando hay brechas críticas.""",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.tipologia",
            "proyecto.fase_actual",
            "documentos_cargados",
            "checklist_tipologia_fase"
        ],
        "deseable": [
            "deliberaciones_previas",
            "defense_file_actual"
        ]
    },
    
    "fases_participacion": ["F5", "F6"],
    "puede_bloquear_avance": True,
    
    "hechos_relevantes_por_fase": {
        "F0": ["SIB con BEE documentado", "Evaluación inicial de riesgo", "Vinculación plan estratégico"],
        "F1": ["Registro proyecto sistema", "Tipología asignada"],
        "F2": ["SOW con entregables listados", "Cronograma de hitos", "Dictamen A1 Estrategia"],  # CANDADO
        "F3": ["Due diligence proveedor", "Consulta 69-B", "Opinión 32-D", "Score proveedor A6"],
        "F4": ["Contrato firmado", "Presupuesto confirmado", "Dictamen A4 Legal"],
        "F5": ["VBC Fiscal preliminar", "Análisis deducibilidad"],
        "F6": ["Minuta kick-off", "Entregable V1", "Versiones iterativas", "Minutas de revisión"],  # CANDADO
        "F7": ["Entregable final", "Acta de aceptación técnica", "Evidencia de uso"],
        "F8": ["CFDI específico", "Comprobante pago", "3-way match"],  # CANDADO
        "F9": ["Matriz completa", "VBC Fiscal", "VBC Legal", "Defense File integrado", "Índice defendibilidad"]
    },

    # Candados de control - fases que requieren aprobación antes de continuar
    "candados_control": {
        "F2": {
            "descripcion": "Evaluación Estratégica completada",
            "condiciones": ["Dictamen A1 APROBAR o APROBAR_CONDICIONES", "BEE documentado > beneficio fiscal"],
            "agente_responsable": "A1_SPONSOR"
        },
        "F6": {
            "descripcion": "Ejecución verificada",
            "condiciones": ["Evidencia de ejecución suficiente", "Minutas de trabajo"],
            "agente_responsable": "A2_PMO"
        },
        "F8": {
            "descripcion": "Three-Way Match validado",
            "condiciones": ["Contrato = CFDI = Pago", "Sin discrepancias"],
            "agente_responsable": "A5_FINANZAS"
        }
    },

    # Criterios de los 4 pilares fiscales
    "pilares_fiscales": {
        "razon_negocios": {
            "articulo": "Art. 5-A CFF",
            "documentos_requeridos": ["SIB", "Vinculación plan estratégico", "Dictamen A1"],
            "criterio_aprobacion": "BEE > Beneficio fiscal",
            "peso": 25
        },
        "beneficio_economico": {
            "articulo": "Art. 5-A CFF",
            "documentos_requeridos": ["Matriz BEE", "KPIs definidos", "ROI documentado"],
            "criterio_aprobacion": "BEE cuantificable y razonable",
            "peso": 25
        },
        "materialidad": {
            "articulo": "Art. 69-B CFF",
            "documentos_requeridos": ["Evidencia ejecución", "Entregables", "Acta aceptación"],
            "criterio_aprobacion": "Servicio efectivamente prestado con evidencia",
            "peso": 25
        },
        "trazabilidad": {
            "articulo": "NOM-151",
            "documentos_requeridos": ["Documentos con fecha cierta", "Cadena custodia", "Hash integridad"],
            "criterio_aprobacion": "Documentación conservada según norma",
            "peso": 25
        }
    }
}

EVIDENCIA_ESPERADA = {
    # F0 - Identificación de necesidad
    "SIB con BEE documentado": "Service Initiation Brief con BEE cuantificado (mayor a beneficio fiscal)",
    "Evaluación inicial de riesgo": "Evaluación de A3-Fiscal con risk_score inicial",
    "Vinculación plan estratégico": "Referencia a OKR o iniciativa del plan estratégico vigente",

    # F1 - Registro inicial
    "Registro proyecto sistema": "Proyecto registrado en Revisar-IA con datos básicos",
    "Tipología asignada": "Tipología de servicio clasificada correctamente",

    # F2 - Evaluación estratégica (CANDADO)
    "SOW con entregables listados": "Statement of Work con entregables específicos y medibles",
    "Cronograma de hitos": "Cronograma con fechas, hitos y responsables definidos",
    "Dictamen A1 Estrategia": "Dictamen del agente A1 con análisis de razón de negocios",

    # F3 - Due diligence proveedor
    "Due diligence proveedor": "Verificación completa del proveedor",
    "Consulta 69-B": "Captura de consulta al listado de EFOS del SAT",
    "Opinión 32-D": "Opinión de cumplimiento de obligaciones fiscales",
    "Score proveedor A6": "Evaluación de riesgo del proveedor por agente A6",

    # F4 - Contrato
    "Contrato firmado": "Contrato firmado por ambas partes con cláusulas de materialidad",
    "Presupuesto confirmado": "Confirmación de presupuesto por A5-Finanzas",
    "Dictamen A4 Legal": "Dictamen del agente A4 con validación legal del contrato",

    # F5 - Validación fiscal
    "VBC Fiscal preliminar": "Visto Bueno de Cumplimiento Fiscal preliminar",
    "Análisis deducibilidad": "Análisis de cumplimiento de requisitos de deducibilidad",

    # F6 - Ejecución (CANDADO)
    "Minuta kick-off": "Minuta de reunión de inicio con asistentes identificados",
    "Entregable V1": "Primera versión del entregable con control de cambios",
    "Versiones iterativas": "Versiones de trabajo que demuestran proceso real",
    "Minutas de revisión": "Minutas de sesiones de revisión con observaciones",

    # F7 - Recepción
    "Entregable final": "Versión final del entregable que cumple criterios de aceptación",
    "Acta de aceptación técnica": "Acta firmada de aceptación con validador identificado",
    "Evidencia de uso": "Evidencia de que el entregable fue implementado/usado",

    # F8 - Three-Way Match (CANDADO)
    "CFDI específico": "CFDI con descripción específica que coincide con SOW (no genérica)",
    "Comprobante pago": "Comprobante de pago bancario trazable",
    "3-way match": "Validación de coincidencia Contrato=CFDI=Pago sin discrepancias",

    # F9 - Cierre y Defense File
    "Matriz completa": "Matriz de materialidad >= 80% de completitud",
    "VBC Fiscal": "Visto Bueno de Cumplimiento Fiscal definitivo",
    "VBC Legal": "Visto Bueno de Cumplimiento Legal definitivo",
    "Defense File integrado": "Expediente de defensa con 5 secciones completas",
    "Índice defendibilidad": "Índice de defendibilidad calculado (0-100)"
}

UMBRAL_VBC = 80


def evaluar_materialidad(
    proyecto: Dict[str, Any],
    documentos_cargados: List[Dict[str, Any]],
    fase_actual: str
) -> Dict[str, Any]:
    """
    Evalúa la matriz de materialidad del proyecto.
    
    Args:
        proyecto: Datos del proyecto
        documentos_cargados: Lista de documentos cargados
        fase_actual: Fase actual del proyecto (F0-F9)
    
    Returns:
        Output estructurado con evaluación de materialidad
    """
    hechos_por_fase = SUB_MATERIALIDAD_CONFIG["hechos_relevantes_por_fase"]
    
    fases_orden = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
    fase_idx = fases_orden.index(fase_actual) if fase_actual in fases_orden else 0
    
    fases_evaluar = fases_orden[:fase_idx + 1]
    
    matriz = []
    items_ok = 0
    items_total = 0
    brechas_criticas = []
    
    nombres_docs = [d.get("nombre", "").lower() for d in documentos_cargados]
    tipos_docs = [d.get("tipo", "").lower() for d in documentos_cargados]
    
    for fase in fases_evaluar:
        hechos = hechos_por_fase.get(fase, [])
        for hecho in hechos:
            items_total += 1
            evidencia_esperada = EVIDENCIA_ESPERADA.get(hecho, hecho)
            
            estado, doc_encontrado, doc_id = buscar_evidencia(
                hecho, documentos_cargados, nombres_docs, tipos_docs
            )
            
            if estado == "OK":
                items_ok += 1
            elif estado == "FALTA" and fase in ["F0", "F1", "F2", "F5", "F6"]:
                brechas_criticas.append({
                    "hecho": hecho,
                    "fase": fase,
                    "impacto": calcular_impacto(hecho, fase),
                    "accion_requerida": f"Cargar documento: {evidencia_esperada}"
                })
            
            matriz.append({
                "hecho_relevante": hecho,
                "fase": fase,
                "evidencia_esperada": evidencia_esperada,
                "evidencia_encontrada": doc_encontrado,
                "documento_id": doc_id,
                "estado": estado
            })
    
    completitud = round((items_ok / items_total * 100), 1) if items_total > 0 else 0
    
    puede_emitir_vbc = completitud >= UMBRAL_VBC and len(brechas_criticas) == 0
    
    razon_bloqueo = None
    if not puede_emitir_vbc:
        razones = []
        if completitud < UMBRAL_VBC:
            razones.append(f"Completitud {completitud}% < {UMBRAL_VBC}% requerido")
        if brechas_criticas:
            razones.append(f"{len(brechas_criticas)} brechas críticas pendientes")
        razon_bloqueo = ". ".join(razones)
    
    return {
        "matriz_materialidad": matriz,
        "completitud_porcentaje": completitud,
        "items_ok": items_ok,
        "items_total": items_total,
        "brechas_criticas": brechas_criticas,
        "puede_emitir_vbc": puede_emitir_vbc,
        "razon_bloqueo_vbc": razon_bloqueo
    }


def buscar_evidencia(
    hecho: str,
    documentos: List[Dict[str, Any]],
    nombres: List[str],
    tipos: List[str]
) -> tuple:
    """
    Busca evidencia documental para un hecho relevante.
    
    Returns:
        Tupla (estado, documento_encontrado, documento_id)
    """
    keywords_por_hecho = {
        "SIB con BEE documentado": ["sib", "bee", "solicitud", "beneficio"],
        "Evaluación inicial de riesgo": ["evaluacion", "riesgo", "risk", "fiscal"],
        "SOW con entregables listados": ["sow", "statement", "entregables", "alcance"],
        "Cronograma de hitos": ["cronograma", "hitos", "timeline", "calendario"],
        "Contrato firmado": ["contrato", "contract", "firmado"],
        "Presupuesto confirmado": ["presupuesto", "budget", "finanzas"],
        "Minuta kick-off": ["minuta", "kickoff", "kick-off", "inicio"],
        "Entregable V1": ["v1", "version 1", "entregable", "draft"],
        "Versiones iterativas": ["v2", "v3", "version", "iteracion"],
        "Minutas de revisión": ["minuta", "revision", "sesion"],
        "Entregable final": ["final", "entregable", "definitivo"],
        "Acta de aceptación técnica": ["acta", "aceptacion", "tecnica"],
        "Matriz completa": ["matriz", "materialidad", "completa"],
        "VBC Fiscal": ["vbc", "fiscal", "cumplimiento"],
        "VBC Legal": ["vbc", "legal", "cumplimiento"],
        "CFDI específico": ["cfdi", "factura", "xml"],
        "Comprobante pago": ["pago", "comprobante", "transferencia"],
        "3-way match": ["match", "validacion", "conciliacion"]
    }
    
    keywords = keywords_por_hecho.get(hecho, [hecho.lower().split()[0]])
    
    for i, doc in enumerate(documentos):
        nombre = nombres[i]
        tipo = tipos[i]
        
        matches = sum(1 for kw in keywords if kw in nombre or kw in tipo)
        if matches >= 1:
            return ("OK", doc.get("nombre"), doc.get("id"))
    
    return ("FALTA", None, None)


def calcular_impacto(hecho: str, fase: str) -> str:
    """Calcula el impacto de una brecha según el hecho y la fase"""
    impactos = {
        "SIB con BEE documentado": "Sin BEE no se puede demostrar razón de negocios",
        "Contrato firmado": "Sin contrato no hay trazabilidad legal",
        "Entregable final": "Sin entregable no hay materialidad demostrable",
        "VBC Fiscal": "Sin VBC Fiscal no se puede facturar",
        "VBC Legal": "Sin VBC Legal el expediente queda incompleto",
        "CFDI específico": "CFDI genérico es señal de operación simulada",
        "3-way match": "Sin 3-way match hay riesgo de fraude"
    }
    return impactos.get(hecho, f"Documento faltante afecta completitud de fase {fase}")


def verificar_umbral_vbc(completitud: float) -> Dict[str, Any]:
    """Verifica si se alcanza el umbral para VBC"""
    return {
        "umbral_requerido": UMBRAL_VBC,
        "completitud_actual": completitud,
        "cumple_umbral": completitud >= UMBRAL_VBC,
        "faltante": max(0, UMBRAL_VBC - completitud)
    }
