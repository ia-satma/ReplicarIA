"""
Configuración del Agente ARCHIVO - Revisar.IA
Agente de Gestión de Archivos y Documentación
"""

from typing import Dict, Any, List

ARCHIVO_CONFIG: Dict[str, Any] = {
    
    "id": "ARCHIVO",
    "nombre": "Agente Archivo",
    
    "rol": "Gestionar el archivo documental del sistema, organizar expedientes, mantener la trazabilidad de versiones y asegurar la integridad del repositorio de documentos.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "estructura_carpetas",
            "documentos_activos"
        ],
        "deseable": [
            "politicas_retencion",
            "clasificacion_documentos"
        ],
        "no_necesita": [
            "analisis_fiscales",
            "decisiones_agentes"
        ]
    },
    
    "normativa_relevante": [
        "NOM_151",
        "POLITICA_RETENCION_DOCUMENTAL"
    ],
    
    "preguntas_clave": [
        "¿Dónde está archivado este documento?",
        "¿Cuál es la versión vigente?",
        "¿El expediente está completo?",
        "¿Cuándo fue la última actualización?",
        "¿Qué documentos están por vencer?"
    ],
    
    "fases_participacion": ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
    
    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    "emite_vbc": False,
    
    "output_schema": {
        "expediente_id": {
            "tipo": "string",
            "obligatorio": True
        },
        "documentos_archivados": {
            "tipo": "number",
            "obligatorio": True
        },
        "estructura_expediente": {
            "tipo": "object",
            "obligatorio": True
        },
        "versiones_activas": {
            "tipo": "array",
            "items": {
                "documento": "string",
                "version": "string",
                "fecha": "timestamp"
            },
            "obligatorio": True
        },
        "alertas_vencimiento": {
            "tipo": "array",
            "items": "string",
            "obligatorio": False
        },
        "estado_archivo": {
            "tipo": "enum",
            "valores": ["COMPLETO", "PARCIAL", "PENDIENTE"],
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## REPORTE ARCHIVO - EXPEDIENTE {{expediente_id}}

### ESTADO DEL ARCHIVO
**{{estado_archivo}}** - Total documentos: **{{documentos_archivados}}**

---

### ESTRUCTURA DEL EXPEDIENTE
{{#each estructura_expediente}}
- {{@key}}: {{this}}
{{/each}}

---

### VERSIONES ACTIVAS
{{#each versiones_activas}}
- **{{this.documento}}** v{{this.version}} ({{this.fecha}})
{{/each}}

---

### ALERTAS DE VENCIMIENTO
{{#each alertas_vencimiento}}
- ⚠️ {{this}}
{{/each}}
"""
}
