"""
Configuración del Agente A5_FINANZAS - Revisar.IA
Agente Finanzas
"""

from typing import Dict, Any, List

A5_FINANZAS_CONFIG: Dict[str, Any] = {
    
    "id": "A5_FINANZAS",
    "nombre": "Agente Finanzas",
    
    "rol": "Validar la proporción económica del gasto, confirmar disponibilidad de presupuesto, evaluar el impacto financiero, y ejecutar el 3-way match al momento del pago.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.monto",
            "proyecto.tipologia",
            "proyecto.bee_roi_esperado",
            "proyecto.bee_horizonte_meses",
            "ingresos_anuales_empresa",
            "presupuesto_disponible",
            "decision_a1",
            "risk_score_a3"
        ],
        "deseable": [
            "historial_gastos_similares",
            "benchmark_interno"
        ],
        "no_necesita": [
            "detalles_normativos_fiscales",
            "clausulas_contractuales"
        ]
    },
    
    "normativa_relevante": [
        "POLITICA_INTERNA_PRESUPUESTOS",
        "LISR_27_DEDUCCIONES"
    ],
    
    "preguntas_clave": [
        "¿El monto es proporcional a los ingresos de la empresa?",
        "¿Hay presupuesto disponible?",
        "¿El ROI esperado es razonable?",
        "¿Cuál sería el impacto si el gasto no fuera deducible?",
        "¿Se requiere evaluación post-implementación?"
    ],
    
    "fases_participacion": ["F2", "F4", "F8"],
    
    "puede_bloquear_avance": True,
    "puede_aprobar_solo": False,
    "ejecuta_3way_match": True,
    
    "output_schema": {
        "decision": {
            "tipo": "enum",
            "valores": ["APROBAR", "SOLICITAR_AJUSTES", "RECHAZAR"],
            "obligatorio": True
        },
        "analisis_proporcion": {
            "tipo": "object",
            "campos": {
                "costo_vs_ventas_porcentaje": "number",
                "evaluacion_proporcion": {"tipo": "enum", "valores": ["RAZONABLE", "ALTO_PERO_JUSTIFICABLE", "DESPROPORCIONADO"]},
                "presupuesto_disponible": "boolean",
                "centro_costo": "string"
            },
            "obligatorio": True
        },
        "evaluacion_bee": {
            "tipo": "object",
            "campos": {
                "roi_evaluacion": "string",
                "horizonte_evaluacion": "string",
                "conclusion": {"tipo": "enum", "valores": ["CONFORME", "CONDICIONADO", "NO_CONFORME"]}
            },
            "obligatorio": True
        },
        "condiciones_financieras": {
            "tipo": "array",
            "items": {
                "condicion": "string",
                "cumplido": "boolean"
            },
            "obligatorio": True
        },
        "impacto_no_deducibilidad": {
            "tipo": "string",
            "descripcion": "Qué pasaría si SAT rechaza la deducción",
            "obligatorio": True
        },
        "requiere_evaluacion_f9": {
            "tipo": "boolean",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## DICTAMEN FINANZAS A5 - PROYECTO {{proyecto.id}}

### INFORMACIÓN DEL PROYECTO
- **Nombre:** {{proyecto.nombre}}
- **Monto:** {{proyecto.monto}} MXN
- **Tipología:** {{proyecto.tipologia}}

---

## ANÁLISIS DE PROPORCIÓN ECONÓMICA

**Costo vs Ventas:** {{analisis_proporcion.costo_vs_ventas_porcentaje}}%
**Evaluación:** {{analisis_proporcion.evaluacion_proporcion}}
**Presupuesto disponible:** {{analisis_proporcion.presupuesto_disponible}}
**Centro de costo:** {{analisis_proporcion.centro_costo}}

---

## EVALUACIÓN DEL BEE

**ROI:** {{evaluacion_bee.roi_evaluacion}}
**Horizonte:** {{evaluacion_bee.horizonte_evaluacion}}
**Conclusión:** {{evaluacion_bee.conclusion}}

---

## CONDICIONES FINANCIERAS

| Condición | Cumplido |
|-----------|----------|
{{#each condiciones_financieras}}
| {{this.condicion}} | {{this.cumplido}} |
{{/each}}

---

## IMPACTO SI NO ES DEDUCIBLE

{{impacto_no_deducibilidad}}

---

## REQUIERE EVALUACIÓN F9: {{requiere_evaluacion_f9}}

---

## DECISIÓN A5 FINANZAS: {{decision}}
"""
}
