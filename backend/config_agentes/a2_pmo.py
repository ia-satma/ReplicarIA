"""
Configuración del Agente A2_PMO - Revisar.IA
Agente PMO / Orquestador
"""

from typing import Dict, Any, List

A2_PMO_CONFIG: Dict[str, Any] = {
    
    "id": "A2_PMO",
    "nombre": "Agente PMO / Orquestador",
    
    "rol": "Controlar el flujo de fases F0-F9, verificar que se cumplan los requisitos mínimos para avanzar entre fases, consolidar decisiones de todos los agentes, y activar alertas cuando se requiere revisión humana.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.fase_actual",
            "proyecto.tipologia",
            "proyecto.monto",
            "fases_completadas",
            "checklist_fase_actual",
            "decisiones_agentes_actuales",
            "documentos_cargados"
        ],
        "deseable": [
            "historial_fases",
            "alertas_activas"
        ],
        "no_necesita": [
            "detalles_normativos_finos",
            "analisis_fiscal_completo"
        ]
    },
    
    "normativa_relevante": [
        "POE_FASES_F0_F9"
    ],
    
    "preguntas_clave": [
        "¿En qué fase está el proyecto?",
        "¿Qué documentos faltan para completar esta fase?",
        "¿Qué agentes faltan por emitir dictamen?",
        "¿Hay bloqueos activos?",
        "¿Se requiere revisión humana?",
        "¿Cuál es la siguiente acción requerida?"
    ],
    
    "fases_participacion": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    
    "puede_bloquear_avance": True,
    "puede_aprobar_solo": False,
    "es_orquestador": True,
    
    "output_schema": {
        "estado_global_proyecto": {
            "tipo": "enum",
            "valores": ["PENDIENTE", "APROBADO_ESTRATEGICO", "APROBADO_CONDICIONAL", "APROBADO_OPERATIVO", "RECHAZADO", "BLOQUEADO"],
            "obligatorio": True
        },
        "fase_actual": {
            "tipo": "string",
            "obligatorio": True
        },
        "checklist_estado": {
            "tipo": "array",
            "items": {
                "item": "string",
                "estado": {"tipo": "enum", "valores": ["CUMPLIDO", "PENDIENTE", "NO_APLICA"]}
            },
            "obligatorio": True
        },
        "decisiones_agentes_resumen": {
            "tipo": "object",
            "campos": {
                "A1": {"tipo": "string"},
                "A3": {"tipo": "string"},
                "A4": {"tipo": "string"},
                "A5": {"tipo": "string"}
            },
            "obligatorio": True
        },
        "bloqueos_activos": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "requiere_revision_humana": {
            "tipo": "boolean",
            "obligatorio": True
        },
        "razon_revision_humana": {
            "tipo": "string",
            "nullable": True
        },
        "siguiente_accion": {
            "tipo": "string",
            "obligatorio": True
        },
        "puede_avanzar_fase": {
            "tipo": "boolean",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## ESTADO PMO - PROYECTO {{proyecto.id}}

### INFORMACIÓN GENERAL
- **Nombre:** {{proyecto.nombre}}
- **Tipología:** {{proyecto.tipologia}}
- **Monto:** {{proyecto.monto}} MXN

---

### FASE ACTUAL: {{fase_actual}}
### ESTADO GLOBAL: {{estado_global_proyecto}}

---

### CHECKLIST DE FASE {{fase_actual}}

| Item | Estado |
|------|--------|
{{#each checklist_estado}}
| {{this.item}} | {{this.estado}} |
{{/each}}

---

### DECISIONES DE AGENTES

| Agente | Decisión |
|--------|----------|
| A1 Sponsor | {{decisiones_agentes_resumen.A1}} |
| A3 Fiscal | {{decisiones_agentes_resumen.A3}} |
| A4 Legal | {{decisiones_agentes_resumen.A4}} |
| A5 Finanzas | {{decisiones_agentes_resumen.A5}} |

---

### BLOQUEOS ACTIVOS
{{#if bloqueos_activos.length}}
{{#each bloqueos_activos}}
- ⚠️ {{this}}
{{/each}}
{{else}}
Sin bloqueos activos.
{{/if}}

---

### REVISIÓN HUMANA
**Requiere:** {{requiere_revision_humana}}
{{#if razon_revision_humana}}
**Razón:** {{razon_revision_humana}}
{{/if}}

---

### ¿PUEDE AVANZAR DE FASE? {{puede_avanzar_fase}}

### SIGUIENTE ACCIÓN REQUERIDA
{{siguiente_accion}}
"""
}
