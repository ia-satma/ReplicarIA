"""
Checklist para Software/SaaS/Desarrollo - Revisar.IA
Desarrollo de software, licencias, SaaS
"""

from typing import Dict, Any, List

CHECKLIST_SOFTWARE_SAAS_DESARROLLO: Dict[str, Any] = {
    
    "tipologia": "SOFTWARE_SAAS_DESARROLLO",
    "nombre": "Desarrollo de software, licencias, SaaS",
    "riesgo_inherente": "MEDIO",
    "revision_humana_obligatoria": False,
    
    "F0": {
        "nombre": "Aprobación - Definir BEE",
        "items": [
            {
                "id": "SSD_F0_01",
                "descripcion": "SIB con necesidad de negocio que resuelve el software",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Qué problema/oportunidad de negocio atiende el sistema",
                "ejemplo_bueno": "SIB: 'Sistema de gestión de inventarios para reducir faltantes de 8% a 2% y liberar capital de trabajo'",
                "ejemplo_malo": "'Desarrollo de sistema'"
            },
            {
                "id": "SSD_F0_02",
                "descripcion": "BEE con beneficios cuantificables del sistema",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Ahorros, eficiencias o ingresos esperados del sistema",
                "ejemplo_bueno": "BEE: Reducción de faltantes = $2M/año, liberación de inventario = $5M one-time. ROI: 3.5x en 18 meses",
                "ejemplo_malo": "'El sistema nos hará más eficientes'"
            },
            {
                "id": "SSD_F0_03",
                "descripcion": "Análisis de capitalización vs gasto",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Determinar si el desarrollo se capitaliza como activo intangible o se gasta",
                "ejemplo_bueno": "Análisis: Desarrollo a la medida con vida útil > 1 año → Capitalizar y amortizar en 3 años",
                "ejemplo_malo": "Sin análisis de tratamiento contable/fiscal"
            }
        ]
    },
    
    "F1": {
        "nombre": "Pre-contratación / SOW",
        "items": [
            {
                "id": "SSD_F1_01",
                "descripcion": "Especificaciones funcionales/técnicas",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento que describa qué debe hacer el sistema",
                "ejemplo_bueno": "Especificación de 40 páginas con: módulos, funcionalidades, integraciones, usuarios, permisos",
                "ejemplo_malo": "'Sistema de inventarios completo'"
            },
            {
                "id": "SSD_F1_02",
                "descripcion": "Contrato/SOW con entregables de desarrollo",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Contrato que liste módulos, fases de desarrollo, criterios de aceptación",
                "ejemplo_bueno": "SOW con: Fase 1 - Módulo inventarios (8 sem), Fase 2 - Módulo compras (6 sem), Fase 3 - Reportes (4 sem)",
                "ejemplo_malo": "'Desarrollo de sistema según requerimientos'"
            },
            {
                "id": "SSD_F1_03",
                "descripcion": "Propiedad intelectual definida en contrato",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Quién es dueño del código: cliente, proveedor, o licencia",
                "ejemplo_bueno": "Cláusula: 'El código fuente desarrollado será propiedad exclusiva del Cliente una vez pagado'",
                "ejemplo_malo": "Sin cláusula de propiedad intelectual"
            }
        ]
    },
    
    "F2": {
        "nombre": "Validación previa al inicio",
        "items": [
            {
                "id": "SSD_F2_01",
                "descripcion": "Confirmación de presupuesto",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Partida presupuestal identificada para el desarrollo",
                "ejemplo_bueno": "Presupuesto 2026: Partida 'Desarrollo de Sistemas' - $3M aprobados",
                "ejemplo_malo": "Sin presupuesto asignado"
            },
            {
                "id": "SSD_F2_02",
                "descripcion": "Contrato firmado",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Contrato con firmas de ambas partes",
                "ejemplo_bueno": "Contrato firmado el 15/mar/2026 por representantes autorizados",
                "ejemplo_malo": "Solo propuesta sin formalización"
            }
        ]
    },
    
    "F3": {
        "nombre": "Ejecución inicial",
        "items": [
            {
                "id": "SSD_F3_01",
                "descripcion": "Repositorio de código con commits",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Acceso a repo Git con historial de desarrollo",
                "ejemplo_bueno": "Repositorio GitHub con 450 commits, 12 branches, historial desde kick-off",
                "ejemplo_malo": "Solo entrega de código final sin historial"
            },
            {
                "id": "SSD_F3_02",
                "descripcion": "Tickets/issues de desarrollo",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Sistema de tracking con tareas, bugs, features",
                "ejemplo_bueno": "Jira con 180 tickets: 120 features, 45 bugs, 15 mejoras",
                "ejemplo_malo": "Sin sistema de tracking"
            },
            {
                "id": "SSD_F3_03",
                "descripcion": "Ambiente de desarrollo/staging funcional",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Sistema accesible para pruebas durante desarrollo",
                "ejemplo_bueno": "Ambiente staging en URL con credenciales de prueba",
                "ejemplo_malo": "Solo demos en computadora del proveedor"
            }
        ]
    },
    
    "F4": {
        "nombre": "Revisión iterativa",
        "items": [
            {
                "id": "SSD_F4_01",
                "descripcion": "Demos de avance por sprint/fase",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Sesiones de demo documentadas mostrando funcionalidad",
                "ejemplo_bueno": "Demo Sprint 5: Módulo de reportes, 8 participantes, feedback documentado",
                "ejemplo_malo": "Sin demos de avance"
            },
            {
                "id": "SSD_F4_02",
                "descripcion": "Minutas de sesiones de revisión",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Registro de reuniones de revisión con acuerdos",
                "ejemplo_bueno": "Minuta 20/may: Revisión módulo inventarios, 3 ajustes solicitados, próxima entrega 30/may",
                "ejemplo_malo": "Sin registro de reuniones"
            },
            {
                "id": "SSD_F4_03",
                "descripcion": "Log de cambios y versiones",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Registro de releases con changelog",
                "ejemplo_bueno": "Changelog: v0.1 (15/abr), v0.5 (1/may), v0.8 (20/may), v1.0 (10/jun)",
                "ejemplo_malo": "Sin control de versiones"
            }
        ]
    },
    
    "F5": {
        "nombre": "Entrega final / Aceptación técnica",
        "items": [
            {
                "id": "SSD_F5_01",
                "descripcion": "Sistema en producción funcionando",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Sistema desplegado y operativo en ambiente productivo",
                "ejemplo_bueno": "Sistema en producción desde 1/jul, URL productiva, 50 usuarios activos",
                "ejemplo_malo": "Sistema que nunca llegó a producción"
            },
            {
                "id": "SSD_F5_02",
                "descripcion": "Código fuente entregado (si aplica)",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Entrega del código fuente según contrato",
                "ejemplo_bueno": "Código entregado en repositorio transferido + backup en medio físico",
                "ejemplo_malo": "Sin entrega de código cuando contrato lo requería"
            },
            {
                "id": "SSD_F5_03",
                "descripcion": "Documentación técnica y de usuario",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Manuales técnico y de usuario",
                "ejemplo_bueno": "Manual técnico (arquitectura, APIs, deploy) + Manual usuario (50 pp con screenshots)",
                "ejemplo_malo": "Sin documentación"
            },
            {
                "id": "SSD_F5_04",
                "descripcion": "Pruebas de aceptación (UAT) documentadas",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Registro de pruebas realizadas y resultados",
                "ejemplo_bueno": "UAT con 45 casos de prueba, 43 pasados, 2 con workaround aceptado, firmado por usuario líder",
                "ejemplo_malo": "Sin pruebas de aceptación documentadas"
            },
            {
                "id": "SSD_F5_05",
                "descripcion": "Acta de aceptación firmada",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento formal de aceptación del sistema",
                "ejemplo_bueno": "Acta firmada por Gerente de Operaciones: 'Se acepta el sistema de inventarios cumpliendo los criterios acordados'",
                "ejemplo_malo": "Sin acta formal de aceptación"
            }
        ]
    },
    
    "F6": {
        "nombre": "VBC Fiscal/Legal",
        "items": [
            {
                "id": "SSD_F6_01",
                "descripcion": "Matriz de materialidad con evidencia de desarrollo",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Documentar que el desarrollo realmente se hizo (no compra de licencia disfrazada)",
                "ejemplo_bueno": "Matriz con: repo con historial, tickets, demos, UAT, sistema funcionando = desarrollo real",
                "ejemplo_malo": "Solo contrato y factura"
            },
            {
                "id": "SSD_F6_02",
                "descripcion": "Confirmación de tratamiento contable/fiscal",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Validar que se aplicó el tratamiento correcto (capitalización vs gasto)",
                "ejemplo_bueno": "Confirmación: Desarrollo capitalizado como activo intangible, amortización 3 años desde go-live",
                "ejemplo_malo": "Sin confirmación de tratamiento"
            },
            {
                "id": "SSD_F6_03",
                "descripcion": "VBC Fiscal",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "VBC de A3 confirmando deducibilidad/amortizabilidad",
                "ejemplo_bueno": "VBC Fiscal: 'Desarrollo de software capitalizable, amortización deducible conforme art. 32 LISR'",
                "ejemplo_malo": "Sin VBC Fiscal"
            },
            {
                "id": "SSD_F6_04",
                "descripcion": "VBC Legal",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "VBC de A4 confirmando propiedad intelectual y documentación contractual",
                "ejemplo_bueno": "VBC Legal: 'Propiedad intelectual transferida correctamente, documentación completa'",
                "ejemplo_malo": "Sin VBC Legal"
            }
        ]
    },
    
    "F8": {
        "nombre": "CFDI y pago",
        "items": [
            {
                "id": "SSD_F8_01",
                "descripcion": "CFDI con descripción del desarrollo",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Factura que describa el desarrollo realizado",
                "ejemplo_bueno": "CFDI: 'Desarrollo de Sistema de Gestión de Inventarios según contrato XXX - Fases 1-3'",
                "ejemplo_malo": "CFDI: 'Servicios de consultoría en TI'"
            },
            {
                "id": "SSD_F8_02",
                "descripcion": "Pagos por hitos conforme a contrato",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Pagos alineados a entregas según calendario contractual",
                "ejemplo_bueno": "Pago 1: $600K (kick-off), Pago 2: $900K (UAT), Pago 3: $500K (go-live) = $2M total",
                "ejemplo_malo": "Pago total anticipado sin entregas"
            },
            {
                "id": "SSD_F8_03",
                "descripcion": "3-way match validado",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Contrato, CFDI y pagos coinciden",
                "ejemplo_bueno": "3-way match OK: Contrato $2M = CFDIs $2M = Pagos $2M",
                "ejemplo_malo": "Montos inconsistentes entre documentos"
            }
        ]
    },
    
    "F9": {
        "nombre": "Post-implementación",
        "items": [
            {
                "id": "SSD_F9_01",
                "descripcion": "Informe de adopción y uso del sistema",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Métricas de uso del sistema después de go-live",
                "ejemplo_bueno": "A 6 meses: 85 usuarios activos, 12,000 transacciones/mes, faltantes reducidos de 8% a 2.5%",
                "ejemplo_malo": "Sin métricas de uso"
            },
            {
                "id": "SSD_F9_02",
                "descripcion": "Evaluación de ROI obtenido vs esperado",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Comparativo de beneficios logrados vs proyectados",
                "ejemplo_bueno": "ROI a 12 meses: 2.1x vs 3.5x esperado. Causa: implementación 3 meses retrasada",
                "ejemplo_malo": "Sin evaluación de ROI"
            }
        ]
    }
}
