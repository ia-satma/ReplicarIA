"""
Configuración del Agente A4_LEGAL - Revisar.IA
Agente Legal
"""

from typing import Dict, Any, List

A4_LEGAL_CONFIG: Dict[str, Any] = {
    
    "id": "A4_LEGAL",
    "nombre": "Agente Legal",
    
    "rol": "Revisar y aprobar la documentación contractual (SOW, contratos, anexos), verificar que se incluyan las cláusulas necesarias para materialidad y trazabilidad, y emitir el Visto Bueno Legal cuando corresponda.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.tipologia",
            "proyecto.monto",
            "proyecto.descripcion",
            "proveedor.nombre",
            "proveedor.rfc",
            "proveedor.tipo_relacion",
            "checklist_evidencia_fiscal",
            "decision_a3"
        ],
        "deseable": [
            "plantilla_contractual_tipo",
            "sow_borrador"
        ],
        "no_necesita": [
            "analisis_financiero_detallado",
            "proyecciones_economicas"
        ]
    },
    
    "normativa_relevante": [
        "CONTRATOS_CIVILES",
        "NOM_151_trazabilidad",
        "POLITICA_INTERNA_CONTRATACION"
    ],
    
    "preguntas_clave": [
        "¿El SOW/contrato tiene objeto y alcance claros?",
        "¿Están listados los entregables específicos?",
        "¿Hay criterios de aceptación verificables?",
        "¿Existen cláusulas de confidencialidad adecuadas?",
        "¿Se obliga al proveedor a entregar evidencias de ejecución?",
        "¿Hay mecanismo de fecha cierta/trazabilidad?"
    ],
    
    "fases_participacion": ["F1", "F6"],
    
    "puede_bloquear_avance": True,
    "puede_aprobar_final": True,
    "emite_vbc": True,
    
    "output_schema": {
        "decision": {
            "tipo": "enum",
            "valores": ["APROBAR", "SOLICITAR_AJUSTES", "RECHAZAR"],
            "obligatorio": True
        },
        "checklist_contractual": {
            "tipo": "array",
            "items": {
                "item": "string",
                "status": {"tipo": "enum", "valores": ["CUMPLIDO", "PENDIENTE", "NO_APLICA"]},
                "accion_requerida": {"tipo": "string", "nullable": True}
            },
            "min_items": 5,
            "obligatorio": True
        },
        "ajustes_requeridos": {
            "tipo": "array",
            "items": {
                "descripcion": "string",
                "fase_bloquea": "string",
                "criticidad": {"tipo": "enum", "valores": ["BLOQUEANTE", "IMPORTANTE", "MENOR"]}
            },
            "obligatorio": True
        },
        "clausulas_obligatorias_faltantes": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "riesgo_puntos_trazabilidad": {
            "tipo": "number",
            "min": 0,
            "max": 25,
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## DICTAMEN LEGAL A4 - PROYECTO {{proyecto.id}}

### INFORMACIÓN DEL PROYECTO
- **Nombre:** {{proyecto.nombre}}
- **Tipología:** {{proyecto.tipologia}}
- **Proveedor:** {{proveedor.nombre}} ({{proveedor.rfc}})

---

## CHECKLIST CONTRACTUAL

| Item | Status | Acción Requerida |
|------|--------|------------------|
{{#each checklist_contractual}}
| {{this.item}} | {{this.status}} | {{this.accion_requerida}} |
{{/each}}

---

## AJUSTES REQUERIDOS

{{#if ajustes_requeridos.length}}
{{#each ajustes_requeridos}}
### Ajuste {{@index}} ({{this.criticidad}})
**Descripción:** {{this.descripcion}}
**Fase que bloquea:** {{this.fase_bloquea}}

{{/each}}
{{else}}
Sin ajustes requeridos.
{{/if}}

---

## CLÁUSULAS OBLIGATORIAS FALTANTES

{{#if clausulas_obligatorias_faltantes.length}}
{{#each clausulas_obligatorias_faltantes}}
- {{this}}
{{/each}}
{{else}}
Todas las cláusulas obligatorias están presentes.
{{/if}}

---

## RIESGO TRAZABILIDAD: {{riesgo_puntos_trazabilidad}}/25

---

## DECISIÓN A4 LEGAL: {{decision}}
"""
}
