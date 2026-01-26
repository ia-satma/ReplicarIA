"""
Scoring Module para Revisar.IA
Exporta ejemplos few-shot y matriz de scoring
"""

from .few_shot_examples import (
    FEW_SHOT_EXAMPLES,
    get_ejemplo,
    get_todos_ejemplos
)

from .risk_scoring import (
    RISK_SCORING_MATRIX,
    calcular_risk_score,
    get_descripcion_criterio,
    get_matriz_completa,
    explicar_diferencia_scores
)


def build_few_shot_section(incluir_todos: bool = True) -> str:
    """
    Construye la sección de few-shot examples para incluir en prompts de agentes.
    
    Args:
        incluir_todos: Si True, incluye los 3 casos. Si False, solo headers.
        
    Returns:
        String con la sección formateada
    """
    import json
    
    section = """
## CASOS DE REFERENCIA (FEW-SHOT EXAMPLES)

Usa estos casos como referencia para calibrar tus decisiones:

"""
    
    if incluir_todos:
        section += f"""
### CASO MODELO: APROBAR
{json.dumps(FEW_SHOT_EXAMPLES["APROBAR"], indent=2, ensure_ascii=False)}

---

### CASO MODELO: SOLICITAR_AJUSTES
{json.dumps(FEW_SHOT_EXAMPLES["SOLICITAR_AJUSTES"], indent=2, ensure_ascii=False)}

---

### CASO MODELO: RECHAZAR
{json.dumps(FEW_SHOT_EXAMPLES["RECHAZAR"], indent=2, ensure_ascii=False)}
"""
    
    return section


def build_risk_scoring_instructions() -> str:
    """
    Construye las instrucciones de scoring para incluir en prompts de agentes.
    
    Returns:
        String con las instrucciones formateadas
    """
    return """
## INSTRUCCIONES PARA CALCULAR RISK SCORE

El risk_score debe calcularse de forma OBJETIVA usando estos criterios:

### PILAR 1: RAZÓN DE NEGOCIOS (0-25 puntos)
- Vinculación con giro: 0 (plena), 3 (genérica), 5 (débil)
- Objetivo económico: 0 (cuantificable), 5 (sin métricas), 10 (vago)
- Coherencia monto: 0 (razonable), 5 (alto defendible), 10 (desproporcionado)

### PILAR 2: BENEFICIO ECONÓMICO (0-25 puntos)
- Identificación beneficios: 0 (concretos), 5 (genéricos), 10 (inexistentes)
- Modelo ROI: 0 (documentado), 5 (narrativa), 10 (ninguno)
- Horizonte temporal: 0 (congruente), 3 (optimista), 5 (irreal)

### PILAR 3: MATERIALIDAD (0-25 puntos)
- Formalización: 0 (contrato completo), 3 (orden/correos), 5 (nada)
- Evidencias ejecución: 0 (claras), 5 (parciales), 10 (ninguna)
- Coherencia documentos: 0 (coinciden), 5 (inconsistencias menores), 10 (discrepancias graves)

### PILAR 4: TRAZABILIDAD (0-25 puntos)
- Conservación: 0 (expediente estructurado), 5 (disperso), 10 (correos sueltos)
- Integridad: 0 (mecanismos robustos), 5 (parcial), 10 (ninguno)
- Timeline: 0 (reconstruible), 3 (con huecos), 5 (confuso)

TOTAL: 0-100. Menor es mejor.
- 0-39: BAJO riesgo
- 40-59: MEDIO riesgo
- 60-79: ALTO riesgo (requiere revisión humana)
- 80-100: CRÍTICO (considerar rechazo)
"""


__all__ = [
    "FEW_SHOT_EXAMPLES",
    "RISK_SCORING_MATRIX",
    "get_ejemplo",
    "get_todos_ejemplos",
    "calcular_risk_score",
    "get_descripcion_criterio",
    "get_matriz_completa",
    "explicar_diferencia_scores",
    "build_few_shot_section",
    "build_risk_scoring_instructions"
]
