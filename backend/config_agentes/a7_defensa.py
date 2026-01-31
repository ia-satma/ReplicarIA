"""
Configuración del Agente A7_DEFENSA - Revisar.IA
Agente Defense File / Arquitecto de Coherencia Documental

Basado en el concepto de "Gobernanza Cognitiva" que transforma la defensa fiscal
de un modelo reactivo a uno preventivo y estructural.

Jurisprudencia de soporte:
- Tesis II.2o.C. J/1 K (12a.) - SCJN - Registro 2031639
- Valida el uso de IA como herramienta auxiliar en procesos de análisis
"""

from typing import Dict, Any, List

A7_DEFENSA_CONFIG: Dict[str, Any] = {

    "id": "A7_DEFENSA",
    "nombre": "Agente Defense File / Arquitecto de Coherencia Documental",

    "rol": """Consolidar el expediente de defensa fiscal (Defense File) con estructura de 5 secciones,
    evaluar la defendibilidad del proyecto ante auditorías del SAT según criterios del TFJA,
    y garantizar la coherencia documental entre todos los agentes del sistema.

    Responsabilidades clave:
    1. Arquitectura del Defense File con narrativa coherente para auditor/magistrado
    2. Estandarización de entregables críticos (SIB, SOW, Actas)
    3. Control de coherencia multi-agente (unificar tono y lógica de dictámenes)
    4. Síntesis ejecutiva para toma de decisiones""",

    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "proyecto.nombre",
            "proyecto.tipologia",
            "proyecto.monto",
            "defense_file_actual",
            "decisiones_agentes.a1",
            "decisiones_agentes.a3",
            "decisiones_agentes.a4",
            "decisiones_agentes.a5",
            "decisiones_agentes.a6",
            "matriz_materialidad",
            "vbc_fiscal",
            "vbc_legal",
            "three_way_match_status"
        ],
        "deseable": [
            "precedentes_tfja",
            "criterios_defendibilidad",
            "proyectos_similares_defendidos",
            "jurisprudencia_scjn_ia"
        ],
        "no_necesita": []
    },

    "normativa_relevante": [
        "CFF_5A_razon_negocios",
        "CFF_5A_beneficio_economico",
        "CFF_69B_materialidad",
        "LISR_27_deducciones",
        "NOM_151_trazabilidad",
        "CRITERIOS_TFJA",
        "SCJN_TESIS_IA_2031639"
    ],

    "preguntas_clave": [
        "¿El expediente permite reconstruir la historia del servicio de F0 a F9?",
        "¿Cuál es el índice de defendibilidad calculado por los 4 pilares?",
        "¿Qué documentos críticos faltan para cada sección del Defense File?",
        "¿Hay coherencia entre los dictámenes de A1, A3, A4, A5 y A6?",
        "¿Los argumentos de defensa están respaldados por precedentes del TFJA?",
        "¿El BEE está claramente documentado y diferenciado del beneficio fiscal?",
        "¿Existe Three-Way Match completo (Contrato = CFDI = Pago)?"
    ],

    "fases_participacion": ["F6", "F7", "F8", "F9"],

    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    "emite_vbc": False,
    "genera_defense_file": True,

    # Estructura del Defense File según Gobernanza Cognitiva
    "estructura_defense_file": {
        "seccion_1_contexto": {
            "nombre": "Contexto y Razón de Negocios",
            "peso_ponderacion": 25,
            "documentos": ["SIB", "Plan Estratégico", "Dictamen A1", "Análisis BEE"],
            "pregunta_clave": "¿Por qué la empresa necesitaba este servicio?"
        },
        "seccion_2_contractual": {
            "nombre": "Marco Contractual",
            "peso_ponderacion": 20,
            "documentos": ["SOW firmado", "Contrato", "Dictamen A4", "Anexos técnicos"],
            "pregunta_clave": "¿Qué se contrató y bajo qué términos?"
        },
        "seccion_3_ejecucion": {
            "nombre": "Evidencia de Ejecución",
            "peso_ponderacion": 30,
            "documentos": ["Minutas", "Correos", "Versiones entregables", "Dictamen A6"],
            "pregunta_clave": "¿Cómo se comprueba que el servicio fue prestado?"
        },
        "seccion_4_financiero": {
            "nombre": "Validación Financiera",
            "peso_ponderacion": 15,
            "documentos": ["Three-Way Match", "CFDI validado", "Dictamen A5", "Comprobante de pago"],
            "pregunta_clave": "¿El flujo financiero es consistente y trazable?"
        },
        "seccion_5_cierre": {
            "nombre": "Cierre y Materialidad",
            "peso_ponderacion": 10,
            "documentos": ["Acta Aceptación Técnica", "Evidencia de uso", "VBC Fiscal"],
            "pregunta_clave": "¿El entregable se usó y generó el beneficio esperado?"
        }
    },

    "output_schema": {
        "indice_defendibilidad": {
            "tipo": "number",
            "min": 0,
            "max": 100,
            "descripcion": "0 = máxima defendibilidad, 100 = máximo riesgo (inverso)",
            "obligatorio": True
        },
        "nivel_defendibilidad": {
            "tipo": "enum",
            "valores": ["EXCELENTE", "BUENO", "MODERADO", "DÉBIL", "CRÍTICO"],
            "obligatorio": True
        },
        "secciones_defense_file": {
            "tipo": "object",
            "campos": {
                "contexto": {
                    "completitud": {"tipo": "number", "min": 0, "max": 100},
                    "documentos_presentes": {"tipo": "array", "items": "string"},
                    "documentos_faltantes": {"tipo": "array", "items": "string"},
                    "coherencia_narrativa": {"tipo": "enum", "valores": ["COHERENTE", "PARCIAL", "INCOHERENTE"]}
                },
                "contractual": {
                    "completitud": {"tipo": "number", "min": 0, "max": 100},
                    "documentos_presentes": {"tipo": "array", "items": "string"},
                    "documentos_faltantes": {"tipo": "array", "items": "string"},
                    "coherencia_narrativa": {"tipo": "enum", "valores": ["COHERENTE", "PARCIAL", "INCOHERENTE"]}
                },
                "ejecucion": {
                    "completitud": {"tipo": "number", "min": 0, "max": 100},
                    "documentos_presentes": {"tipo": "array", "items": "string"},
                    "documentos_faltantes": {"tipo": "array", "items": "string"},
                    "coherencia_narrativa": {"tipo": "enum", "valores": ["COHERENTE", "PARCIAL", "INCOHERENTE"]}
                },
                "financiero": {
                    "completitud": {"tipo": "number", "min": 0, "max": 100},
                    "three_way_match": {"tipo": "enum", "valores": ["COMPLETO", "PARCIAL", "FALLA"]},
                    "documentos_presentes": {"tipo": "array", "items": "string"},
                    "documentos_faltantes": {"tipo": "array", "items": "string"}
                },
                "cierre": {
                    "completitud": {"tipo": "number", "min": 0, "max": 100},
                    "documentos_presentes": {"tipo": "array", "items": "string"},
                    "documentos_faltantes": {"tipo": "array", "items": "string"},
                    "evidencia_uso": {"tipo": "boolean"}
                }
            },
            "obligatorio": True
        },
        "coherencia_multiagente": {
            "tipo": "object",
            "campos": {
                "consistencia_bee": {"tipo": "boolean", "descripcion": "¿A1, A3 y A5 usan el mismo BEE?"},
                "consistencia_razon_negocios": {"tipo": "boolean"},
                "discrepancias_identificadas": {"tipo": "array", "items": "string"}
            },
            "obligatorio": True
        },
        "argumentos_defensa": {
            "tipo": "array",
            "items": {
                "argumento": "string",
                "pilar_relacionado": {"tipo": "enum", "valores": ["RAZON_NEGOCIOS", "BEE", "MATERIALIDAD", "TRAZABILIDAD"]},
                "precedente_tfja": {"tipo": "string", "nullable": True},
                "fortaleza": {"tipo": "enum", "valores": ["FUERTE", "MODERADO", "DÉBIL"]}
            },
            "min_items": 3,
            "obligatorio": True
        },
        "brechas_criticas": {
            "tipo": "array",
            "items": {
                "brecha": "string",
                "seccion": "string",
                "impacto": {"tipo": "enum", "valores": ["ALTO", "MEDIO", "BAJO"]},
                "accion_recomendada": "string"
            },
            "obligatorio": True
        },
        "recomendaciones_refuerzo": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "resumen_ejecutivo": {
            "tipo": "string",
            "min_length": 200,
            "descripcion": "Síntesis para CFO/Director que permita decidir si aprobar pago",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## DEFENSE FILE - PROYECTO {{proyecto.id}}

### INFORMACIÓN DEL PROYECTO
- **Nombre:** {{proyecto.nombre}}
- **Tipología:** {{proyecto.tipologia}}
- **Monto:** {{proyecto.monto}} MXN

---

## ÍNDICE DE DEFENDIBILIDAD

| Métrica | Valor |
|---------|-------|
| **Score** | {{indice_defendibilidad}}/100 |
| **Nivel** | {{nivel_defendibilidad}} |

> **Interpretación:** 0-20 = Excelente | 21-40 = Bueno | 41-60 = Moderado | 61-80 = Débil | 81-100 = Crítico

---

## SECCIONES DEL DEFENSE FILE

### 1. CONTEXTO Y RAZÓN DE NEGOCIOS (25%)
**Completitud:** {{secciones_defense_file.contexto.completitud}}%
**Coherencia:** {{secciones_defense_file.contexto.coherencia_narrativa}}

**Documentos presentes:**
{{#each secciones_defense_file.contexto.documentos_presentes}}
- ✓ {{this}}
{{/each}}

**Documentos faltantes:**
{{#each secciones_defense_file.contexto.documentos_faltantes}}
- ✗ {{this}}
{{/each}}

---

### 2. MARCO CONTRACTUAL (20%)
**Completitud:** {{secciones_defense_file.contractual.completitud}}%
**Coherencia:** {{secciones_defense_file.contractual.coherencia_narrativa}}

**Documentos presentes:**
{{#each secciones_defense_file.contractual.documentos_presentes}}
- ✓ {{this}}
{{/each}}

**Documentos faltantes:**
{{#each secciones_defense_file.contractual.documentos_faltantes}}
- ✗ {{this}}
{{/each}}

---

### 3. EVIDENCIA DE EJECUCIÓN (30%)
**Completitud:** {{secciones_defense_file.ejecucion.completitud}}%
**Coherencia:** {{secciones_defense_file.ejecucion.coherencia_narrativa}}

**Documentos presentes:**
{{#each secciones_defense_file.ejecucion.documentos_presentes}}
- ✓ {{this}}
{{/each}}

**Documentos faltantes:**
{{#each secciones_defense_file.ejecucion.documentos_faltantes}}
- ✗ {{this}}
{{/each}}

---

### 4. VALIDACIÓN FINANCIERA (15%)
**Completitud:** {{secciones_defense_file.financiero.completitud}}%
**Three-Way Match:** {{secciones_defense_file.financiero.three_way_match}}

**Documentos presentes:**
{{#each secciones_defense_file.financiero.documentos_presentes}}
- ✓ {{this}}
{{/each}}

**Documentos faltantes:**
{{#each secciones_defense_file.financiero.documentos_faltantes}}
- ✗ {{this}}
{{/each}}

---

### 5. CIERRE Y MATERIALIDAD (10%)
**Completitud:** {{secciones_defense_file.cierre.completitud}}%
**Evidencia de uso:** {{secciones_defense_file.cierre.evidencia_uso}}

**Documentos presentes:**
{{#each secciones_defense_file.cierre.documentos_presentes}}
- ✓ {{this}}
{{/each}}

**Documentos faltantes:**
{{#each secciones_defense_file.cierre.documentos_faltantes}}
- ✗ {{this}}
{{/each}}

---

## COHERENCIA MULTI-AGENTE

| Validación | Estado |
|------------|--------|
| Consistencia BEE (A1, A3, A5) | {{coherencia_multiagente.consistencia_bee}} |
| Consistencia Razón de Negocios | {{coherencia_multiagente.consistencia_razon_negocios}} |

{{#if coherencia_multiagente.discrepancias_identificadas.length}}
**⚠️ Discrepancias identificadas:**
{{#each coherencia_multiagente.discrepancias_identificadas}}
- {{this}}
{{/each}}
{{/if}}

---

## ARGUMENTOS DE DEFENSA

{{#each argumentos_defensa}}
### Argumento {{@index_1}}
**Pilar:** {{this.pilar_relacionado}}
**Fortaleza:** {{this.fortaleza}}
{{#if this.precedente_tfja}}
**Precedente TFJA:** {{this.precedente_tfja}}
{{/if}}

> {{this.argumento}}

{{/each}}

---

## BRECHAS CRÍTICAS

| Brecha | Sección | Impacto | Acción Recomendada |
|--------|---------|---------|-------------------|
{{#each brechas_criticas}}
| {{this.brecha}} | {{this.seccion}} | {{this.impacto}} | {{this.accion_recomendada}} |
{{/each}}

---

## RECOMENDACIONES DE REFUERZO

{{#each recomendaciones_refuerzo}}
{{@index_1}}. {{this}}
{{/each}}

---

## RESUMEN EJECUTIVO

{{resumen_ejecutivo}}

---

## VALIDACIÓN JURÍDICA DEL USO DE IA

Este dictamen fue generado con asistencia de Inteligencia Artificial, práctica respaldada por:

> **Tesis II.2o.C. J/1 K (12a.) - SCJN - Registro 2031639**
> "El uso de herramientas de inteligencia artificial como auxiliares en procesos de evaluación es válido y recomendable, siempre que la decisión final permanezca en el ser humano."

La IA actúa como auxiliar técnico; la voluntad jurídica permanece en el responsable humano.
"""
}
