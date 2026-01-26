"""
Configuración del Agente A3_FISCAL - Revisar.IA
Agente Fiscal
"""

from typing import Dict, Any, List

A3_FISCAL_CONFIG: Dict[str, Any] = {
    
    "id": "A3_FISCAL",
    "nombre": "Agente Fiscal",
    
    "rol": "Evaluar el proyecto bajo los 4 pilares fiscales (razón de negocios, beneficio económico, materialidad, trazabilidad), calcular el risk_score objetivo, identificar riesgos especiales (EFOS, TP, esquemas reportables), y emitir el Visto Bueno Fiscal (VBC) cuando corresponda.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.descripcion",
            "proyecto.monto",
            "proyecto.tipologia",
            "proyecto.vinculo_plan_estrategico",
            "proyecto.bee_objetivo",
            "proyecto.bee_roi_esperado",
            "proveedor.nombre",
            "proveedor.rfc",
            "proveedor.tipo_relacion",
            "proveedor.alerta_efos",
            "documentos_existentes",
            "decision_a1",
            "decision_a4",
            "matriz_materialidad_preliminar"
        ],
        "deseable": [
            "historial_proveedor",
            "proyectos_similares_previos",
            "alertas_riesgos_especiales"
        ],
        "no_necesita": [
            "detalles_financieros_internos"
        ]
    },
    
    "normativa_relevante": [
        "CFF_5A_razon_negocios",
        "CFF_5A_beneficio_economico",
        "CFF_69B_materialidad",
        "LISR_27_deducciones",
        "NOM_151_trazabilidad",
        "RMF_intangibles",
        "RMF_esquemas_reportables"
    ],
    
    "preguntas_clave": [
        "¿El proyecto tiene razón de negocios genuina?",
        "¿El BEE está documentado y es razonable?",
        "¿Hay evidencia suficiente de materialidad?",
        "¿La documentación tiene trazabilidad y fecha cierta?",
        "¿Hay señales de riesgo especial (EFOS, TP, esquemas)?",
        "¿Qué documentos faltan para poder emitir VBC?"
    ],
    
    "fases_participacion": ["F0", "F4", "F6"],
    
    "puede_bloquear_avance": True,
    "puede_aprobar_final": True,
    "emite_vbc": True,
    "requiere_validacion_humana_default": False,
    
    "output_schema": {
        "decision": {
            "tipo": "enum",
            "valores": ["APROBAR", "APROBAR_CONDICIONES", "SOLICITAR_AJUSTES", "RECHAZAR"],
            "obligatorio": True
        },
        "conclusion_por_pilar": {
            "tipo": "object",
            "campos": {
                "razon_negocios": {
                    "status": {"tipo": "enum", "valores": ["CONFORME", "CONDICIONADO", "NO_CONFORME"]},
                    "detalle": {"tipo": "string", "min_length": 50},
                    "riesgo_puntos": {"tipo": "number", "min": 0, "max": 25}
                },
                "beneficio_economico": {
                    "status": {"tipo": "enum", "valores": ["CONFORME", "CONDICIONADO", "NO_CONFORME"]},
                    "detalle": {"tipo": "string", "min_length": 50},
                    "riesgo_puntos": {"tipo": "number", "min": 0, "max": 25}
                },
                "materialidad": {
                    "status": {"tipo": "enum", "valores": ["CONFORME", "EN_RIESGO", "FALLA_CRITICA"]},
                    "detalle": {"tipo": "string", "min_length": 50},
                    "riesgo_puntos": {"tipo": "number", "min": 0, "max": 25}
                },
                "trazabilidad": {
                    "status": {"tipo": "enum", "valores": ["CONFORME", "EN_RIESGO", "FALLA_CRITICA"]},
                    "detalle": {"tipo": "string", "min_length": 50},
                    "riesgo_puntos": {"tipo": "number", "min": 0, "max": 25}
                }
            },
            "obligatorio": True
        },
        "risk_score_total": {
            "tipo": "number",
            "min": 0,
            "max": 100,
            "obligatorio": True
        },
        "checklist_evidencia_exigible": {
            "tipo": "array",
            "items": {
                "item": "string",
                "obligatorio": "boolean",
                "estado": {"tipo": "enum", "valores": ["PENDIENTE", "ENTREGADO", "INCONSISTENTE"]},
                "fase_requerida": "string"
            },
            "min_items": 3,
            "obligatorio": True
        },
        "alertas_riesgo_especial": {
            "tipo": "array",
            "items": {
                "tipo_alerta": {"tipo": "enum", "valores": ["EFOS", "PARTE_RELACIONADA", "ESQUEMA_REPORTABLE", "TP_PENDIENTE", "OTRO"]},
                "descripcion": "string",
                "severidad": {"tipo": "enum", "valores": ["BAJA", "MEDIA", "ALTA", "CRITICA"]}
            },
            "obligatorio": True
        },
        "condiciones_para_vbc": {
            "tipo": "array",
            "items": "string",
            "descripcion": "Condiciones que deben cumplirse para emitir VBC",
            "obligatorio": True
        },
        "riesgos_subsistentes": {
            "tipo": "array",
            "items": "string",
            "descripcion": "Riesgos que permanecen aun con aprobación",
            "obligatorio": True
        },
        "requiere_validacion_humana": {
            "tipo": "boolean",
            "obligatorio": True
        },
        "justificacion_validacion_humana": {
            "tipo": "string",
            "nullable": True
        }
    },
    
    "plantilla_respuesta": """
## DICTAMEN FISCAL A3 - PROYECTO {{proyecto.id}}

### INFORMACIÓN DEL PROYECTO
- **Nombre:** {{proyecto.nombre}}
- **Tipología:** {{proyecto.tipologia}}
- **Monto:** {{proyecto.monto}} MXN
- **Proveedor:** {{proveedor.nombre}} ({{proveedor.rfc}})
- **Relación:** {{proveedor.tipo_relacion}}

---

## ANÁLISIS POR PILAR FISCAL

### 1. RAZÓN DE NEGOCIOS (Art. 5-A CFF)
**Status:** {{conclusion_por_pilar.razon_negocios.status}}
**Riesgo:** {{conclusion_por_pilar.razon_negocios.riesgo_puntos}}/25

{{conclusion_por_pilar.razon_negocios.detalle}}

---

### 2. BENEFICIO ECONÓMICO (Art. 5-A CFF)
**Status:** {{conclusion_por_pilar.beneficio_economico.status}}
**Riesgo:** {{conclusion_por_pilar.beneficio_economico.riesgo_puntos}}/25

{{conclusion_por_pilar.beneficio_economico.detalle}}

---

### 3. MATERIALIDAD (Art. 69-B CFF)
**Status:** {{conclusion_por_pilar.materialidad.status}}
**Riesgo:** {{conclusion_por_pilar.materialidad.riesgo_puntos}}/25

{{conclusion_por_pilar.materialidad.detalle}}

---

### 4. TRAZABILIDAD (NOM-151)
**Status:** {{conclusion_por_pilar.trazabilidad.status}}
**Riesgo:** {{conclusion_por_pilar.trazabilidad.riesgo_puntos}}/25

{{conclusion_por_pilar.trazabilidad.detalle}}

---

## RISK SCORE TOTAL: {{risk_score_total}}/100

| Pilar | Puntos |
|-------|--------|
| Razón de Negocios | {{conclusion_por_pilar.razon_negocios.riesgo_puntos}}/25 |
| Beneficio Económico | {{conclusion_por_pilar.beneficio_economico.riesgo_puntos}}/25 |
| Materialidad | {{conclusion_por_pilar.materialidad.riesgo_puntos}}/25 |
| Trazabilidad | {{conclusion_por_pilar.trazabilidad.riesgo_puntos}}/25 |
| **TOTAL** | **{{risk_score_total}}/100** |

---

## CHECKLIST FISCAL DE EVIDENCIA

| Item | Obligatorio | Estado | Fase |
|------|-------------|--------|------|
{{#each checklist_evidencia_exigible}}
| {{this.item}} | {{this.obligatorio}} | {{this.estado}} | {{this.fase_requerida}} |
{{/each}}

---

## ALERTAS DE RIESGO ESPECIAL

{{#if alertas_riesgo_especial.length}}
{{#each alertas_riesgo_especial}}
⚠️ **{{this.tipo_alerta}}** ({{this.severidad}}): {{this.descripcion}}
{{/each}}
{{else}}
Sin alertas de riesgo especial identificadas.
{{/if}}

---

## CONDICIONES PARA VBC

{{#each condiciones_para_vbc}}
- [ ] {{this}}
{{/each}}

---

## RIESGOS SUBSISTENTES

{{#each riesgos_subsistentes}}
- {{this}}
{{/each}}

---

## VALIDACIÓN HUMANA

**Requiere:** {{requiere_validacion_humana}}
{{#if justificacion_validacion_humana}}
**Justificación:** {{justificacion_validacion_humana}}
{{/if}}

---

## DECISIÓN A3 FISCAL: {{decision}}
"""
}
