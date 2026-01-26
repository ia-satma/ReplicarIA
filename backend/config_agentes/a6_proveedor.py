"""
Configuración del Agente A6_PROVEEDOR - Revisar.IA
Agente Proveedor
"""

from typing import Dict, Any, List

A6_PROVEEDOR_CONFIG: Dict[str, Any] = {
    
    "id": "A6_PROVEEDOR",
    "nombre": "Agente Proveedor",
    
    "rol": "Representar la perspectiva del proveedor, gestionar la carga de entregables y evidencias de ejecución, y facilitar el cumplimiento del checklist de materialidad.",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.id",
            "sow_aprobado",
            "checklist_entregables",
            "fechas_hitos",
            "puntos_contacto_interno"
        ],
        "deseable": [
            "instrucciones_especificas"
        ],
        "no_necesita": [
            "analisis_fiscales_internos",
            "decisiones_otros_agentes"
        ]
    },
    
    "normativa_relevante": [],
    
    "preguntas_clave": [
        "¿Qué entregables están pendientes?",
        "¿Cuál es el estado de avance del proyecto?",
        "¿Hay observaciones pendientes por atender?",
        "¿Cuáles son los próximos hitos?"
    ],
    
    "fases_participacion": ["F3", "F4", "F5"],
    
    "puede_bloquear_avance": False,
    "puede_aprobar_solo": False,
    
    "output_schema": {
        "entregables_cargados": {
            "tipo": "array",
            "items": {
                "nombre": "string",
                "tipo": "string",
                "version": "string",
                "fecha_carga": "timestamp",
                "ruta_archivo": "string"
            },
            "obligatorio": True
        },
        "minutas_sesiones": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "estado_avance": {
            "tipo": "string",
            "obligatorio": True
        },
        "pendientes": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        }
    },
    
    "plantilla_respuesta": """
## REPORTE PROVEEDOR A6 - PROYECTO {{proyecto.id}}

### ENTREGABLES CARGADOS

| Nombre | Tipo | Versión | Fecha |
|--------|------|---------|-------|
{{#each entregables_cargados}}
| {{this.nombre}} | {{this.tipo}} | {{this.version}} | {{this.fecha_carga}} |
{{/each}}

---

### MINUTAS DE SESIONES
{{#each minutas_sesiones}}
- {{this}}
{{/each}}

---

### ESTADO DE AVANCE
{{estado_avance}}

---

### PENDIENTES
{{#each pendientes}}
- {{this}}
{{/each}}
"""
}
