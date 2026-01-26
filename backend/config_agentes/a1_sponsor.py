"""
Configuración del Agente A1_SPONSOR - Revisar.IA
Agente de Estrategia / Sponsor
"""

from typing import Dict, Any, List

A1_SPONSOR_CONFIG: Dict[str, Any] = {
    
    "id": "A1_SPONSOR",
    "nombre": "Agente de Estrategia / Sponsor",
    
    "rol": "Evaluar si el proyecto tiene razón de negocios genuina y un beneficio económico esperado (BEE) documentable. Determinar si el servicio está alineado con la estrategia corporativa y si genera valor real más allá de efectos fiscales.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.descripcion",
            "proyecto.monto",
            "proyecto.tipologia",
            "proyecto.sponsor_interno",
            "proyecto.vinculo_plan_estrategico",
            "proyecto.bee_objetivo",
            "proyecto.bee_roi_esperado",
            "proyecto.bee_horizonte_meses"
        ],
        "deseable": [
            "plan_estrategico_vigente",
            "segmentos_mercado_prioritarios",
            "proyectos_similares_previos"
        ],
        "no_necesita": [
            "detalles_contractuales_finos",
            "CFDI",
            "matriz_materialidad_completa"
        ]
    },
    
    "normativa_relevante": [
        "CFF_5A_razon_negocios",
        "CFF_5A_beneficio_economico"
    ],
    
    "preguntas_clave": [
        "¿Este gasto tiene sentido estratégico dentro del plan de la empresa?",
        "¿Existe un objetivo económico concreto y medible?",
        "¿El ROI esperado es razonable y está documentado?",
        "¿El horizonte temporal del beneficio es congruente con el tipo de servicio?",
        "¿Qué usos concretos tendrá el resultado del servicio?"
    ],
    
    "fases_participacion": ["F0", "F4", "F5", "F9"],
    
    "puede_bloquear_avance": True,
    "puede_aprobar_solo": False,
    "requiere_validacion_humana_default": False,
    
    "output_schema": {
        "decision": {
            "tipo": "enum",
            "valores": ["APROBAR", "SOLICITAR_AJUSTES", "RECHAZAR"],
            "obligatorio": True
        },
        "analisis_razon_negocios": {
            "tipo": "object",
            "campos": {
                "vinculacion_con_giro": {"tipo": "string", "min_length": 30},
                "objetivo_economico": {"tipo": "string", "min_length": 50},
                "conclusion": {"tipo": "enum", "valores": ["CONFORME", "CONDICIONADO", "NO_CONFORME"]}
            },
            "obligatorio": True
        },
        "analisis_bee": {
            "tipo": "object",
            "campos": {
                "objetivo_especifico": {"tipo": "string", "min_length": 50},
                "roi_esperado": {"tipo": "number", "nullable": True},
                "horizonte_meses": {"tipo": "number", "nullable": True},
                "indicadores_exito": {"tipo": "array", "items": "string", "min_items": 1},
                "evaluacion": {"tipo": "enum", "valores": ["CONFORME", "CONDICIONADO", "NO_CONFORME"]}
            },
            "obligatorio": True
        },
        "condiciones_estrategicas_avance": {
            "tipo": "array",
            "items": "string",
            "descripcion": "Lista de condiciones concretas que deben cumplirse para avanzar",
            "obligatorio": True
        },
        "requisitos_para_sow": {
            "tipo": "array",
            "items": "string",
            "descripcion": "Qué debe incluir el SOW/contrato desde perspectiva estratégica",
            "obligatorio": True
        },
        "riesgo_puntos_razon_negocios": {
            "tipo": "number",
            "min": 0,
            "max": 25,
            "obligatorio": True
        },
        "riesgo_puntos_beneficio_economico": {
            "tipo": "number",
            "min": 0,
            "max": 25,
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## EVALUACIÓN A1 - SPONSOR/ESTRATEGIA

### Proyecto: {{proyecto.nombre}}
### ID: {{proyecto.id}}
### Tipología: {{proyecto.tipologia}}
### Monto: {{proyecto.monto}} MXN

---

### 1. ANÁLISIS DE RAZÓN DE NEGOCIOS (Art. 5-A CFF)

**Vinculación con el giro del contribuyente:**
{{analisis_razon_negocios.vinculacion_con_giro}}

**Objetivo económico del proyecto:**
{{analisis_razon_negocios.objetivo_economico}}

**Conclusión Razón de Negocios:** {{analisis_razon_negocios.conclusion}}
**Puntos de Riesgo:** {{riesgo_puntos_razon_negocios}}/25

---

### 2. ANÁLISIS DE BENEFICIO ECONÓMICO ESPERADO (BEE)

**Objetivo específico:**
{{analisis_bee.objetivo_especifico}}

**ROI esperado:** {{analisis_bee.roi_esperado}}x
**Horizonte temporal:** {{analisis_bee.horizonte_meses}} meses

**Indicadores de éxito:**
{{#each analisis_bee.indicadores_exito}}
- {{this}}
{{/each}}

**Evaluación BEE:** {{analisis_bee.evaluacion}}
**Puntos de Riesgo:** {{riesgo_puntos_beneficio_economico}}/25

---

### 3. CONDICIONES ESTRATÉGICAS PARA AVANZAR

{{#each condiciones_estrategicas_avance}}
- [ ] {{this}}
{{/each}}

---

### 4. REQUISITOS PARA SOW/CONTRATO

El SOW debe incluir:
{{#each requisitos_para_sow}}
- {{this}}
{{/each}}

---

### DECISIÓN A1: {{decision}}
"""
}
