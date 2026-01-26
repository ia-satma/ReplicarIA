"""
Configuración del Agente KNOWLEDGE_BASE - Revisar.IA
Agente Gestor de Base de Conocimiento
"""

from typing import Dict, Any, List

KNOWLEDGE_BASE_CONFIG: Dict[str, Any] = {
    
    "id": "KNOWLEDGE_BASE",
    "nombre": "Agente Knowledge Base",
    
    "rol": "Gestionar el acervo de conocimiento normativo, fiscal y legal. Proporcionar contexto relevante a otros agentes mediante RAG y mantener actualizada la base de conocimiento.",
    
    "contexto_requerido": {
        "obligatorio": [
            "query_contexto",
            "agente_solicitante"
        ],
        "deseable": [
            "tipologia_proyecto",
            "fase_actual"
        ],
        "no_necesita": []
    },
    
    "normativa_relevante": [
        "CFF_COMPLETO",
        "LISR_COMPLETO",
        "LIVA_COMPLETO",
        "RMF_2024",
        "RMF_2025",
        "NOM_151",
        "JURISPRUDENCIAS_SCJN",
        "CRITERIOS_TFJA",
        "CRITERIOS_PRODECON"
    ],
    
    "preguntas_clave": [
        "¿Qué normativa aplica a este caso?",
        "¿Existen precedentes similares?",
        "¿Cuál es la interpretación vigente?",
        "¿Hay jurisprudencias relevantes?",
        "¿Qué documentos de KB son relevantes?"
    ],
    
    "fases_participacion": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    
    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    "emite_vbc": False,
    
    "output_schema": {
        "documentos_relevantes": {
            "tipo": "array",
            "items": {
                "titulo": "string",
                "relevancia": "number",
                "extracto": "string",
                "fuente": "string"
            },
            "obligatorio": True
        },
        "normativa_aplicable": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "jurisprudencias": {
            "tipo": "array",
            "items": {
                "tesis": "string",
                "criterio": "string",
                "aplicabilidad": "string"
            },
            "obligatorio": False
        },
        "resumen_contexto": {
            "tipo": "string",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## CONTEXTO KNOWLEDGE BASE

### RESUMEN
{{resumen_contexto}}

---

### NORMATIVA APLICABLE
{{#each normativa_aplicable}}
- {{this}}
{{/each}}

---

### DOCUMENTOS RELEVANTES
{{#each documentos_relevantes}}
#### {{this.titulo}}
- **Relevancia**: {{this.relevancia}}%
- **Fuente**: {{this.fuente}}
- **Extracto**: {{this.extracto}}
{{/each}}

---

### JURISPRUDENCIAS RELEVANTES
{{#each jurisprudencias}}
- **{{this.tesis}}**: {{this.criterio}} ({{this.aplicabilidad}})
{{/each}}
"""
}
