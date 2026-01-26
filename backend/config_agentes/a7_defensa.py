"""
Configuración del Agente A7_DEFENSA - Revisar.IA
Agente Defense File
"""

from typing import Dict, Any, List

A7_DEFENSA_CONFIG: Dict[str, Any] = {
    
    "id": "A7_DEFENSA",
    "nombre": "Agente Defense File",
    
    "rol": "Consolidar el expediente de defensa fiscal, evaluar la defendibilidad del proyecto ante auditorías del SAT, y preparar la documentación probatoria para controversias fiscales.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "defense_file_actual",
            "decisiones_agentes",
            "matriz_materialidad",
            "vbc_fiscal",
            "vbc_legal"
        ],
        "deseable": [
            "precedentes_tfja",
            "criterios_defendibilidad"
        ],
        "no_necesita": []
    },
    
    "normativa_relevante": [
        "CFF_69B",
        "CFF_5A",
        "LISR_27",
        "CRITERIOS_TFJA"
    ],
    
    "preguntas_clave": [
        "¿El expediente está completo para defensa?",
        "¿Cuál es el índice de defendibilidad?",
        "¿Qué documentos críticos faltan?",
        "¿Cuáles son los argumentos de defensa principales?",
        "¿Existen precedentes favorables?"
    ],
    
    "fases_participacion": ["F6", "F7", "F9"],
    
    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    "emite_vbc": False,
    
    "output_schema": {
        "indice_defendibilidad": {
            "tipo": "number",
            "min": 0,
            "max": 100,
            "obligatorio": True
        },
        "nivel_defendibilidad": {
            "tipo": "enum",
            "valores": ["DÉBIL", "MODERADO", "BUENO", "EXCELENTE"],
            "obligatorio": True
        },
        "documentos_criticos_status": {
            "tipo": "object",
            "obligatorio": True
        },
        "brechas_identificadas": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "recomendaciones_refuerzo": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "argumentos_defensa": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## REPORTE DEFENSE FILE A7 - PROYECTO {{proyecto.id}}

### ÍNDICE DE DEFENDIBILIDAD
**Score: {{indice_defendibilidad}}%** - Nivel: **{{nivel_defendibilidad}}**

---

### DOCUMENTOS CRÍTICOS
{{#each documentos_criticos_status}}
- {{@key}}: {{this}}
{{/each}}

---

### BRECHAS IDENTIFICADAS
{{#each brechas_identificadas}}
- {{this}}
{{/each}}

---

### ARGUMENTOS DE DEFENSA
{{#each argumentos_defensa}}
{{@index}}. {{this}}
{{/each}}

---

### RECOMENDACIONES DE REFUERZO
{{#each recomendaciones_refuerzo}}
- {{this}}
{{/each}}
"""
}
