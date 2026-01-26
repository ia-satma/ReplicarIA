"""
A7_DEFENSA - Agente de Defense File y Defendibilidad

Consolida toda la documentación del proyecto en un Defense File estructurado,
evalúa su defendibilidad ante una auditoría SAT o juicio TFJA, identifica
fortalezas y debilidades probatorias, y genera recomendaciones de refuerzo.
"""

from typing import Dict, Any, List, Optional

A7_DEFENSA_CONFIG = {
    "id": "A7_DEFENSA",
    "nombre": "Agente de Defense File y Defendibilidad",
    
    "rol": """Consolidar toda la documentación del proyecto en un Defense File 
    estructurado, evaluar su defendibilidad ante una auditoría SAT o juicio TFJA, 
    identificar fortalezas y debilidades probatorias, y generar recomendaciones 
    de refuerzo.""",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.tipologia",
            "proyecto.monto",
            "proyecto.risk_score_total",
            "matriz_materialidad",
            "deliberaciones_todos_agentes",
            "documentos_todos",
            "vbc_fiscal",
            "vbc_legal"
        ],
        "deseable": [
            "historial_fases",
            "minutas_sesiones",
            "correspondencia_relevante"
        ]
    },
    
    "fases_participacion": ["F6", "F9"],
    "puede_bloquear_avance": False,
    "emite_defense_file": True,
    
    "criterios_defendibilidad": """
CRITERIOS PARA EVALUAR DEFENDIBILIDAD:

1. RAZÓN DE NEGOCIOS (Art. 5-A CFF)
   - ¿Existe SIB con objetivo económico específico?
   - ¿Hay vinculación documentada con plan estratégico?
   - ¿Se puede explicar por qué se necesitó este servicio?

2. BENEFICIO ECONÓMICO (Art. 5-A CFF)
   - ¿Hay BEE con ROI documentado?
   - ¿Se pueden mostrar los usos concretos del servicio?
   - ¿Existe evidencia de seguimiento post-implementación?

3. MATERIALIDAD (Art. 69-B CFF)
   - ¿Existe contrato con entregables específicos?
   - ¿Hay entregables tangibles verificables?
   - ¿Se pueden reconstruir las sesiones de trabajo?
   - ¿El CFDI es específico y coincide con el contrato?

4. TRAZABILIDAD (NOM-151)
   - ¿Todos los documentos tienen fecha cierta?
   - ¿Se puede reconstruir el timeline completo?
   - ¿Los documentos tienen integridad verificable?

5. COHERENCIA GLOBAL
   - ¿Todo el expediente cuenta una historia consistente?
   - ¿Hay contradicciones entre documentos?
   - ¿El expediente resistiría un cuestionamiento adverso?
    """
}

DOCUMENTOS_CLAVE = [
    {"tipo": "SIB", "importancia": "CRITICO", "descripcion": "Solicitud de Inicio con BEE"},
    {"tipo": "CONTRATO", "importancia": "CRITICO", "descripcion": "Contrato firmado"},
    {"tipo": "SOW", "importancia": "CRITICO", "descripcion": "Statement of Work"},
    {"tipo": "ENTREGABLE_FINAL", "importancia": "CRITICO", "descripcion": "Entregable final"},
    {"tipo": "ACTA_ACEPTACION", "importancia": "CRITICO", "descripcion": "Acta de aceptación técnica"},
    {"tipo": "VBC_FISCAL", "importancia": "CRITICO", "descripcion": "VBC Fiscal emitido"},
    {"tipo": "VBC_LEGAL", "importancia": "CRITICO", "descripcion": "VBC Legal emitido"},
    {"tipo": "CFDI", "importancia": "CRITICO", "descripcion": "CFDI con descripción específica"},
    {"tipo": "CRONOGRAMA", "importancia": "IMPORTANTE", "descripcion": "Cronograma de hitos"},
    {"tipo": "MINUTAS", "importancia": "IMPORTANTE", "descripcion": "Minutas de sesiones"},
    {"tipo": "VERSIONES", "importancia": "COMPLEMENTARIO", "descripcion": "Versiones iterativas"},
    {"tipo": "CORRESPONDENCIA", "importancia": "COMPLEMENTARIO", "descripcion": "Correos relevantes"}
]


def evaluar_defendibilidad(
    proyecto: Dict[str, Any],
    documentos: List[Dict[str, Any]],
    deliberaciones: Dict[str, Any],
    matriz_materialidad: Dict[str, Any],
    vbc_fiscal: Optional[Dict[str, Any]] = None,
    vbc_legal: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evalúa la defendibilidad del expediente del proyecto.
    
    Args:
        proyecto: Datos del proyecto
        documentos: Lista de documentos cargados
        deliberaciones: Deliberaciones de todos los agentes
        matriz_materialidad: Resultado de SUB_MATERIALIDAD
        vbc_fiscal: VBC Fiscal si existe
        vbc_legal: VBC Legal si existe
    
    Returns:
        Defense File estructurado con evaluación
    """
    eval_razon = evaluar_razon_negocios(proyecto, documentos, deliberaciones)
    eval_beneficio = evaluar_beneficio_economico(proyecto, documentos, deliberaciones)
    eval_materialidad = evaluar_materialidad_criterio(proyecto, documentos, matriz_materialidad)
    eval_trazabilidad = evaluar_trazabilidad(documentos, vbc_fiscal, vbc_legal)
    eval_coherencia = evaluar_coherencia_global(proyecto, documentos, deliberaciones)
    
    indice = calcular_indice_defendibilidad(
        eval_razon, eval_beneficio, eval_materialidad, 
        eval_trazabilidad, eval_coherencia
    )
    
    docs_clave = evaluar_documentos_clave(documentos)
    
    argumentos = generar_argumentos_defensa(
        proyecto, eval_razon, eval_beneficio, 
        eval_materialidad, eval_trazabilidad
    )
    
    vulnerabilidades = identificar_vulnerabilidades(
        eval_razon, eval_beneficio, eval_materialidad,
        eval_trazabilidad, eval_coherencia
    )
    
    recomendaciones = generar_recomendaciones(vulnerabilidades, indice)
    
    conclusion = generar_conclusion(indice, vulnerabilidades)
    
    return {
        "defense_file_completo": indice >= 60,
        "indice_defendibilidad": indice,
        "evaluacion_por_criterio": {
            "razon_negocios": eval_razon,
            "beneficio_economico": eval_beneficio,
            "materialidad": eval_materialidad,
            "trazabilidad": eval_trazabilidad,
            "coherencia_global": eval_coherencia
        },
        "documentos_clave": docs_clave,
        "argumentos_defensa": argumentos,
        "puntos_vulnerables": vulnerabilidades,
        "recomendaciones_refuerzo": recomendaciones,
        "conclusion": conclusion
    }


def evaluar_razon_negocios(
    proyecto: Dict[str, Any],
    documentos: List[Dict[str, Any]],
    deliberaciones: Dict[str, Any]
) -> Dict[str, Any]:
    """Evalúa el criterio de razón de negocios"""
    fortalezas = []
    debilidades = []
    score = 50
    
    tiene_sib = any(d.get("tipo", "").upper() in ["SIB", "SOLICITUD"] for d in documentos)
    if tiene_sib:
        fortalezas.append("Existe SIB documentado")
        score += 15
    else:
        debilidades.append("Falta SIB con objetivo económico")
        score -= 20
    
    a1_delib = deliberaciones.get("A1_SPONSOR", {})
    if a1_delib.get("decision") == "APROBAR":
        fortalezas.append("A1-Sponsor aprobó razón de negocios")
        score += 10
    elif a1_delib.get("decision"):
        debilidades.append(f"A1-Sponsor no aprobó: {a1_delib.get('decision')}")
        score -= 10
    
    if proyecto.get("objetivo_declarado"):
        fortalezas.append("Objetivo económico declarado")
        score += 10
    else:
        debilidades.append("Sin objetivo económico explícito")
        score -= 15
    
    return {
        "score": max(0, min(100, score)),
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }


def evaluar_beneficio_economico(
    proyecto: Dict[str, Any],
    documentos: List[Dict[str, Any]],
    deliberaciones: Dict[str, Any]
) -> Dict[str, Any]:
    """Evalúa el criterio de beneficio económico"""
    fortalezas = []
    debilidades = []
    score = 50
    
    tiene_bee = any("bee" in d.get("tipo", "").lower() or "beneficio" in d.get("nombre", "").lower() for d in documentos)
    if tiene_bee:
        fortalezas.append("BEE documentado")
        score += 15
    else:
        debilidades.append("Falta documentación de BEE")
        score -= 15
    
    roi = proyecto.get("roi_esperado")
    if roi and roi > 0:
        fortalezas.append(f"ROI documentado: {roi}x")
        score += 10
    else:
        debilidades.append("Sin ROI cuantificado")
        score -= 10
    
    tiene_seguimiento = any("seguimiento" in d.get("nombre", "").lower() for d in documentos)
    if tiene_seguimiento:
        fortalezas.append("Existe seguimiento post-implementación")
        score += 10
    
    return {
        "score": max(0, min(100, score)),
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }


def evaluar_materialidad_criterio(
    proyecto: Dict[str, Any],
    documentos: List[Dict[str, Any]],
    matriz: Dict[str, Any]
) -> Dict[str, Any]:
    """Evalúa el criterio de materialidad"""
    fortalezas = []
    debilidades = []
    score = 50
    
    tiene_contrato = any(d.get("tipo", "").upper() == "CONTRATO" for d in documentos)
    if tiene_contrato:
        fortalezas.append("Contrato firmado existente")
        score += 15
    else:
        debilidades.append("Sin contrato firmado")
        score -= 20
    
    tiene_entregable = any(d.get("tipo", "").upper() in ["ENTREGABLE", "ENTREGABLE_FINAL"] for d in documentos)
    if tiene_entregable:
        fortalezas.append("Entregables tangibles verificables")
        score += 15
    else:
        debilidades.append("Sin entregables tangibles")
        score -= 20
    
    completitud = matriz.get("completitud_porcentaje", 0)
    if completitud >= 80:
        fortalezas.append(f"Matriz de materialidad completa ({completitud}%)")
        score += 10
    elif completitud >= 60:
        debilidades.append(f"Matriz de materialidad parcial ({completitud}%)")
    else:
        debilidades.append(f"Matriz de materialidad muy incompleta ({completitud}%)")
        score -= 15
    
    return {
        "score": max(0, min(100, score)),
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }


def evaluar_trazabilidad(
    documentos: List[Dict[str, Any]],
    vbc_fiscal: Optional[Dict[str, Any]],
    vbc_legal: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Evalúa el criterio de trazabilidad"""
    fortalezas = []
    debilidades = []
    score = 50
    
    docs_con_fecha = sum(1 for d in documentos if d.get("fecha_carga"))
    if docs_con_fecha == len(documentos) and documentos:
        fortalezas.append("Todos los documentos tienen fecha cierta")
        score += 15
    elif docs_con_fecha > 0:
        debilidades.append(f"Solo {docs_con_fecha}/{len(documentos)} documentos con fecha")
    
    if vbc_fiscal and vbc_fiscal.get("emitido"):
        fortalezas.append("VBC Fiscal emitido")
        score += 10
    else:
        debilidades.append("Sin VBC Fiscal")
        score -= 10
    
    if vbc_legal and vbc_legal.get("emitido"):
        fortalezas.append("VBC Legal emitido")
        score += 10
    else:
        debilidades.append("Sin VBC Legal")
        score -= 10
    
    tiene_versiones = sum(1 for d in documentos if d.get("version") and ("v" in str(d.get("version", "")).lower()))
    if tiene_versiones >= 2:
        fortalezas.append("Control de versiones documentado")
        score += 5
    
    return {
        "score": max(0, min(100, score)),
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }


def evaluar_coherencia_global(
    proyecto: Dict[str, Any],
    documentos: List[Dict[str, Any]],
    deliberaciones: Dict[str, Any]
) -> Dict[str, Any]:
    """Evalúa la coherencia global del expediente"""
    fortalezas = []
    debilidades = []
    score = 60
    
    decisiones = [d.get("decision") for d in deliberaciones.values() if d.get("decision")]
    if all(d in ["APROBAR", "APROBAR_CONDICIONES"] for d in decisiones):
        fortalezas.append("Todas las deliberaciones son favorables")
        score += 20
    elif "RECHAZAR" in decisiones:
        debilidades.append("Hay deliberaciones con rechazo")
        score -= 20
    
    risk_score = proyecto.get("risk_score_total", 50)
    if risk_score <= 30:
        fortalezas.append(f"Risk score bajo ({risk_score})")
        score += 10
    elif risk_score >= 70:
        debilidades.append(f"Risk score alto ({risk_score})")
        score -= 15
    
    if len(documentos) >= 8:
        fortalezas.append(f"Expediente robusto ({len(documentos)} documentos)")
        score += 5
    elif len(documentos) < 4:
        debilidades.append(f"Expediente escaso ({len(documentos)} documentos)")
        score -= 10
    
    return {
        "score": max(0, min(100, score)),
        "fortalezas": fortalezas,
        "debilidades": debilidades
    }


def calcular_indice_defendibilidad(
    razon: Dict, beneficio: Dict, materialidad: Dict,
    trazabilidad: Dict, coherencia: Dict
) -> int:
    """Calcula el índice de defendibilidad ponderado"""
    pesos = {
        "razon_negocios": 0.20,
        "beneficio_economico": 0.20,
        "materialidad": 0.25,
        "trazabilidad": 0.20,
        "coherencia_global": 0.15
    }
    
    indice = (
        razon["score"] * pesos["razon_negocios"] +
        beneficio["score"] * pesos["beneficio_economico"] +
        materialidad["score"] * pesos["materialidad"] +
        trazabilidad["score"] * pesos["trazabilidad"] +
        coherencia["score"] * pesos["coherencia_global"]
    )
    
    return round(indice)


def evaluar_documentos_clave(documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evalúa la presencia de documentos clave"""
    resultado = []
    tipos_presentes = {d.get("tipo", "").upper() for d in documentos}
    
    for doc_clave in DOCUMENTOS_CLAVE:
        presente = doc_clave["tipo"] in tipos_presentes
        observacion = "Presente en expediente" if presente else "FALTANTE - Requerido"
        
        resultado.append({
            "tipo_documento": doc_clave["tipo"],
            "nombre": doc_clave["descripcion"],
            "importancia": doc_clave["importancia"],
            "presente": presente,
            "observaciones": observacion
        })
    
    return resultado


def generar_argumentos_defensa(
    proyecto: Dict[str, Any],
    razon: Dict, beneficio: Dict,
    materialidad: Dict, trazabilidad: Dict
) -> List[str]:
    """Genera argumentos que se usarían para defender ante SAT"""
    argumentos = []
    
    for f in razon.get("fortalezas", []):
        argumentos.append(f"RAZÓN DE NEGOCIOS: {f}")
    
    for f in beneficio.get("fortalezas", []):
        argumentos.append(f"BENEFICIO ECONÓMICO: {f}")
    
    for f in materialidad.get("fortalezas", []):
        argumentos.append(f"MATERIALIDAD: {f}")
    
    for f in trazabilidad.get("fortalezas", []):
        argumentos.append(f"TRAZABILIDAD: {f}")
    
    if proyecto.get("tipologia"):
        argumentos.append(f"TIPOLOGÍA: Servicio clasificado como {proyecto['tipologia']} con checklist específico")
    
    return argumentos


def identificar_vulnerabilidades(
    razon: Dict, beneficio: Dict, materialidad: Dict,
    trazabilidad: Dict, coherencia: Dict
) -> List[Dict[str, Any]]:
    """Identifica puntos vulnerables del expediente"""
    vulnerabilidades = []
    
    criterios = [
        ("Razón de Negocios", razon),
        ("Beneficio Económico", beneficio),
        ("Materialidad", materialidad),
        ("Trazabilidad", trazabilidad),
        ("Coherencia Global", coherencia)
    ]
    
    for nombre, criterio in criterios:
        for debilidad in criterio.get("debilidades", []):
            vulnerabilidades.append({
                "vulnerabilidad": f"{nombre}: {debilidad}",
                "impacto_potencial": calcular_impacto_vulnerabilidad(nombre, debilidad),
                "mitigacion_sugerida": sugerir_mitigacion(debilidad)
            })
    
    return vulnerabilidades


def calcular_impacto_vulnerabilidad(criterio: str, debilidad: str) -> str:
    """Calcula el impacto potencial de una vulnerabilidad"""
    if "falta" in debilidad.lower() or "sin" in debilidad.lower():
        return "ALTO - Documento faltante puede generar rechazo de deducción"
    elif "incompleta" in debilidad.lower() or "parcial" in debilidad.lower():
        return "MEDIO - Evidencia parcial debilita la defensa"
    else:
        return "BAJO - Observación menor que puede subsanarse"


def sugerir_mitigacion(debilidad: str) -> str:
    """Sugiere mitigación para una debilidad"""
    mitigaciones = {
        "sib": "Generar y documentar SIB con objetivo económico específico",
        "contrato": "Formalizar contrato con cláusulas de entregables específicos",
        "entregable": "Solicitar entregables tangibles y verificables al proveedor",
        "vbc": "Completar proceso de VBC con área correspondiente",
        "roi": "Documentar ROI esperado con metodología de cálculo",
        "fecha": "Asegurar timestamps y fechas ciertas en todos los documentos"
    }
    
    for keyword, mitigacion in mitigaciones.items():
        if keyword in debilidad.lower():
            return mitigacion
    
    return "Documentar y completar información faltante"


def generar_recomendaciones(vulnerabilidades: List[Dict], indice: int) -> List[str]:
    """Genera recomendaciones de refuerzo del expediente"""
    recomendaciones = []
    
    if indice < 60:
        recomendaciones.append("URGENTE: Expediente débil - reforzar documentación antes de auditoría")
    
    for vuln in vulnerabilidades:
        recomendaciones.append(vuln["mitigacion_sugerida"])
    
    recomendaciones = list(dict.fromkeys(recomendaciones))
    
    return recomendaciones[:10]


def generar_conclusion(indice: int, vulnerabilidades: List[Dict]) -> str:
    """Genera conclusión sobre la defendibilidad"""
    if indice >= 81:
        nivel = "EXCELENTE"
        mensaje = "Expediente muy sólido con alta probabilidad de defensa exitosa."
    elif indice >= 61:
        nivel = "BUENO"
        mensaje = "Expediente adecuado con algunas áreas de mejora."
    elif indice >= 41:
        nivel = "MODERADO"
        mensaje = "Expediente presenta vulnerabilidades significativas que deben atenderse."
    else:
        nivel = "DÉBIL"
        mensaje = "Expediente insuficiente - alto riesgo de rechazo en auditoría."
    
    return f"DEFENDIBILIDAD {nivel} ({indice}/100): {mensaje} Se identificaron {len(vulnerabilidades)} vulnerabilidades."
