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
        "F0": ["SIB con BEE documentado", "Evaluación inicial de riesgo"],
        "F1": ["SOW con entregables listados", "Cronograma de hitos"],
        "F2": ["Contrato firmado", "Presupuesto confirmado"],
        "F3": ["Minuta kick-off", "Entregable V1"],
        "F4": ["Versiones iterativas", "Minutas de revisión"],
        "F5": ["Entregable final", "Acta de aceptación técnica"],
        "F6": ["Matriz completa", "VBC Fiscal", "VBC Legal"],
        "F8": ["CFDI específico", "Comprobante pago", "3-way match"]
    }
}

EVIDENCIA_ESPERADA = {
    "SIB con BEE documentado": "Solicitud de Inicio de Beneficio con objetivo económico documentado",
    "Evaluación inicial de riesgo": "Evaluación de A3-Fiscal con risk_score",
    "SOW con entregables listados": "Statement of Work con entregables específicos",
    "Cronograma de hitos": "Cronograma con fechas y hitos definidos",
    "Contrato firmado": "Contrato firmado por ambas partes",
    "Presupuesto confirmado": "Confirmación de presupuesto por A5-Finanzas",
    "Minuta kick-off": "Minuta de reunión de inicio",
    "Entregable V1": "Primera versión del entregable",
    "Versiones iterativas": "Versiones de trabajo con control de cambios",
    "Minutas de revisión": "Minutas de sesiones de revisión",
    "Entregable final": "Versión final del entregable",
    "Acta de aceptación técnica": "Acta firmada de aceptación",
    "Matriz completa": "Matriz de materialidad >= 80%",
    "VBC Fiscal": "Visto Bueno de Cumplimiento Fiscal",
    "VBC Legal": "Visto Bueno de Cumplimiento Legal",
    "CFDI específico": "CFDI con descripción específica (no genérica)",
    "Comprobante pago": "Comprobante de pago bancario",
    "3-way match": "Validación de coincidencia Contrato=CFDI=Pago"
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
