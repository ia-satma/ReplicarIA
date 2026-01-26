"""
Configuración del Agente A8_AUDITOR - Revisar.IA
Agente Auditor Documental
"""

from typing import Dict, Any, List

A8_AUDITOR_CONFIG: Dict[str, Any] = {
    
    "id": "A8_AUDITOR",
    "nombre": "Agente Auditor Documental",
    
    "rol": "Verificar la integridad y completitud de la documentación cargada, auditar uploads en pCloud, y notificar ajustes necesarios para cumplimiento normativo.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "documentos_cargados",
            "checklist_documental",
            "requisitos_tipologia"
        ],
        "deseable": [
            "historial_versiones",
            "metadatos_archivos"
        ],
        "no_necesita": [
            "decisiones_estrategicas"
        ]
    },
    
    "normativa_relevante": [
        "NOM_151",
        "CFF_29",
        "REQUISITOS_CFDI"
    ],
    
    "preguntas_clave": [
        "¿Todos los documentos requeridos están cargados?",
        "¿Los documentos tienen los metadatos correctos?",
        "¿Hay inconsistencias entre versiones?",
        "¿Los archivos cumplen con NOM-151?",
        "¿Qué documentos requieren actualización?"
    ],
    
    "fases_participacion": ["F3", "F4", "F5", "F6", "F7"],
    
    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    "emite_vbc": False,
    
    "output_schema": {
        "documentos_verificados": {
            "tipo": "number",
            "obligatorio": True
        },
        "documentos_faltantes": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "documentos_con_errores": {
            "tipo": "array",
            "items": {
                "documento": "string",
                "error": "string"
            },
            "obligatorio": True
        },
        "porcentaje_completitud": {
            "tipo": "number",
            "min": 0,
            "max": 100,
            "obligatorio": True
        },
        "acciones_requeridas": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "estado_auditoria": {
            "tipo": "enum",
            "valores": ["APROBADO", "OBSERVACIONES", "RECHAZADO"],
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## REPORTE AUDITORÍA DOCUMENTAL A8 - PROYECTO {{proyecto.id}}

### ESTADO DE AUDITORÍA
**{{estado_auditoria}}** - Completitud: **{{porcentaje_completitud}}%**

---

### DOCUMENTOS VERIFICADOS
Total: {{documentos_verificados}}

---

### DOCUMENTOS FALTANTES
{{#each documentos_faltantes}}
- {{this}}
{{/each}}

---

### DOCUMENTOS CON ERRORES
{{#each documentos_con_errores}}
- **{{this.documento}}**: {{this.error}}
{{/each}}

---

### ACCIONES REQUERIDAS
{{#each acciones_requeridas}}
{{@index}}. {{this}}
{{/each}}
"""
}
