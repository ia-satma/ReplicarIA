"""
Checklist para Intragrupo/Management Fee - Revisar.IA
Servicios intra-grupo, management fees, soporte corporativo (ALTO RIESGO)
"""

from typing import Dict, Any, List

CHECKLIST_INTRAGRUPO_MANAGEMENT_FEE: Dict[str, Any] = {
    
    "tipologia": "INTRAGRUPO_MANAGEMENT_FEE",
    "nombre": "Servicios intra-grupo, management fees, soporte corporativo",
    "riesgo_inherente": "MUY_ALTO",
    "revision_humana_obligatoria": True,
    
    "alertas_especiales": [
        "Esta tipología SIEMPRE requiere revisión humana de Fiscal y Legal",
        "Se requiere estudio de precios de transferencia ANTES de F2",
        "Verificar que no haya duplicidad de funciones con personal interno",
        "Documentar capacidad operativa del prestador (empleados, infraestructura)"
    ],
    
    "F0": {
        "nombre": "Aprobación - Definir BEE",
        "items": [
            {
                "id": "IMF_F0_01",
                "descripcion": "SIB con justificación de necesidad del servicio intra-grupo",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Por qué se necesita este servicio de una empresa relacionada y no se hace internamente",
                "ejemplo_bueno": "SIB: 'Servicios de TI centralizados porque holding tiene equipo especializado de 50 personas que da soporte a 8 subsidiarias, evitando duplicar infraestructura en cada una'",
                "ejemplo_malo": "'Management fee por servicios corporativos'"
            },
            {
                "id": "IMF_F0_02",
                "descripcion": "BEE con análisis de ahorro vs hacer internamente",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Comparativo de costo centralizado vs costo de hacerlo en cada subsidiaria",
                "ejemplo_bueno": "Costo centralizado: $2M/año. Costo de equipo propio equivalente: $3.5M/año. Ahorro: $1.5M",
                "ejemplo_malo": "'Es más eficiente centralizar' sin números"
            },
            {
                "id": "IMF_F0_03",
                "descripcion": "Análisis de no duplicidad de funciones",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Verificación de que no se paga por servicios que ya hace el personal interno",
                "ejemplo_bueno": "Análisis: La subsidiaria no tiene departamento de TI propio. El fee cubre: soporte, infraestructura, licencias, seguridad",
                "ejemplo_malo": "Sin análisis de duplicidad"
            },
            {
                "id": "IMF_F0_04",
                "descripcion": "Estudio de precios de transferencia vigente",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Estudio de TP que cubra estos servicios con método y comparables",
                "ejemplo_bueno": "Estudio TP 2025 por Deloitte: Servicios de TI intra-grupo, método TNMM, margen operativo 8% dentro de rango de mercado",
                "ejemplo_malo": "Sin estudio de TP o estudio de hace 5 años"
            },
            {
                "id": "IMF_F0_05",
                "descripcion": "Documentación de capacidad operativa del prestador",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Evidencia de que el prestador tiene personal e infraestructura para dar el servicio",
                "ejemplo_bueno": "Organigrama del prestador con 50 empleados de TI, lista de activos tecnológicos, instalaciones",
                "ejemplo_malo": "Empresa prestadora sin empleados visibles ni infraestructura"
            }
        ]
    },
    
    "F1": {
        "nombre": "Pre-contratación / SOW",
        "items": [
            {
                "id": "IMF_F1_01",
                "descripcion": "Contrato de servicios intra-grupo detallado",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Contrato que especifique: servicios concretos, niveles de servicio, base de cobro",
                "ejemplo_bueno": "Contrato con anexo: 'Servicios de TI: soporte N1/N2/N3 (SLA 4h/8h/24h), gestión de infraestructura, licenciamiento, seguridad. Base: usuarios activos + consumo'",
                "ejemplo_malo": "'Contrato de management fee por servicios corporativos'"
            },
            {
                "id": "IMF_F1_02",
                "descripcion": "Desglose de servicios incluidos en el fee",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Lista detallada de qué servicios específicos cubre el fee",
                "ejemplo_bueno": "Desglose: 1) Soporte técnico (40%), 2) Infraestructura cloud (25%), 3) Licencias (20%), 4) Seguridad (15%)",
                "ejemplo_malo": "'Servicios de gestión y asesoría corporativa general'"
            },
            {
                "id": "IMF_F1_03",
                "descripcion": "Metodología de asignación de costos",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Cómo se calcula el monto a cobrar a cada subsidiaria",
                "ejemplo_bueno": "Base de asignación: 60% usuarios activos + 40% ingresos. Subsidiaria X tiene 15% de usuarios y 20% de ingresos = 17% del costo total",
                "ejemplo_malo": "Sin metodología de asignación"
            },
            {
                "id": "IMF_F1_04",
                "descripcion": "Referencia a estudio de TP en contrato",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "El contrato debe mencionar que los precios están soportados por estudio de TP",
                "ejemplo_bueno": "Cláusula: 'Los precios de este contrato se determinan conforme al estudio de TP elaborado por [firma] vigente para el ejercicio'",
                "ejemplo_malo": "Contrato sin mención de TP"
            }
        ]
    },
    
    "F2": {
        "nombre": "Validación previa al inicio",
        "items": [
            {
                "id": "IMF_F2_01",
                "descripcion": "Revisión humana obligatoria de Fiscal",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Revisión y aprobación por persona de Fiscal (no solo agente)",
                "ejemplo_bueno": "Revisión 15/mar por Director Fiscal: 'Aprobado con observación de actualizar estudio TP para 2026'",
                "ejemplo_malo": "Solo aprobación del agente A3 sin revisión humana"
            },
            {
                "id": "IMF_F2_02",
                "descripcion": "Revisión humana obligatoria de Legal",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Revisión y aprobación por persona de Legal (no solo agente)",
                "ejemplo_bueno": "Revisión 16/mar por Gerente Legal: 'Contrato aprobado, incluir cláusula de auditoría'",
                "ejemplo_malo": "Solo aprobación del agente A4 sin revisión humana"
            },
            {
                "id": "IMF_F2_03",
                "descripcion": "Confirmación de presupuesto",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Partida presupuestal identificada para el fee",
                "ejemplo_bueno": "Presupuesto 2026: Partida 'Servicios intra-grupo TI' - $2.4M aprobados",
                "ejemplo_malo": "Sin presupuesto asignado"
            }
        ]
    },
    
    "F3": {
        "nombre": "Ejecución inicial",
        "items": [
            {
                "id": "IMF_F3_01",
                "descripcion": "Reportes periódicos de servicios prestados",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Reportes mensuales/trimestrales de qué servicios se dieron",
                "ejemplo_bueno": "Reporte mensual Ene-2026: 145 tickets atendidos, 99.2% SLA cumplido, consumo cloud $X",
                "ejemplo_malo": "Sin reportes de servicio"
            },
            {
                "id": "IMF_F3_02",
                "descripcion": "Registro de horas/recursos dedicados",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Log de tiempo dedicado por el equipo del prestador",
                "ejemplo_bueno": "Timesheet Ene-2026: 320 horas de soporte N1, 80 horas N2, 20 horas N3",
                "ejemplo_malo": "Sin registro de horas"
            }
        ]
    },
    
    "F4": {
        "nombre": "Revisión iterativa",
        "items": [
            {
                "id": "IMF_F4_01",
                "descripcion": "Revisiones trimestrales de niveles de servicio",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Minutas de reuniones de revisión de SLAs",
                "ejemplo_bueno": "Minuta Q1-2026: SLA cumplido al 98.5%, 2 incidentes mayores, plan de mejora acordado",
                "ejemplo_malo": "Sin revisiones periódicas"
            }
        ]
    },
    
    "F5": {
        "nombre": "Entrega final / Cierre de periodo",
        "items": [
            {
                "id": "IMF_F5_01",
                "descripcion": "Reporte anual consolidado de servicios",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Resumen anual de todos los servicios prestados",
                "ejemplo_bueno": "Reporte 2026: 1,680 tickets, SLA promedio 98.7%, proyectos completados: migración cloud, actualización ERP",
                "ejemplo_malo": "Sin reporte consolidado"
            },
            {
                "id": "IMF_F5_02",
                "descripcion": "Acta de conformidad del receptor",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento donde la subsidiaria confirma haber recibido los servicios",
                "ejemplo_bueno": "Acta firmada: 'La subsidiaria X confirma haber recibido los servicios de TI conforme al contrato durante 2026'",
                "ejemplo_malo": "Sin acta de conformidad"
            }
        ]
    },
    
    "F6": {
        "nombre": "VBC Fiscal/Legal",
        "items": [
            {
                "id": "IMF_F6_01",
                "descripcion": "Verificación de estudio TP vigente",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Confirmar que el estudio de TP sigue vigente y cubre la operación",
                "ejemplo_bueno": "Estudio TP 2026 vigente, operación dentro del rango de precios de mercado",
                "ejemplo_malo": "Estudio TP vencido o que no cubre estos servicios"
            },
            {
                "id": "IMF_F6_02",
                "descripcion": "Matriz de materialidad con énfasis en sustancia",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Demostrar que los servicios realmente se prestaron (no simulación)",
                "ejemplo_bueno": "Matriz con: reportes mensuales, timesheets, tickets resueltos, minutas, evidencia de trabajo real",
                "ejemplo_malo": "Solo contrato y facturas sin evidencia de ejecución"
            },
            {
                "id": "IMF_F6_03",
                "descripcion": "VBC Fiscal con análisis especial de TP",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "VBC que confirme cumplimiento de requisitos de precios de transferencia",
                "ejemplo_bueno": "VBC Fiscal: 'Operación conforme a estudio TP, evidencia de sustancia económica suficiente'",
                "ejemplo_malo": "VBC sin análisis de TP"
            },
            {
                "id": "IMF_F6_04",
                "descripcion": "VBC Legal",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "VBC Legal confirmando adecuada documentación",
                "ejemplo_bueno": "VBC Legal: 'Contrato adecuado, desglose de servicios completo'",
                "ejemplo_malo": "Sin VBC Legal"
            }
        ]
    },
    
    "F8": {
        "nombre": "CFDI y pago",
        "items": [
            {
                "id": "IMF_F8_01",
                "descripcion": "CFDI con desglose de servicios",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Factura que detalle los servicios cobrados",
                "ejemplo_bueno": "CFDI: 'Servicios de TI Ene-Dic 2026: Soporte técnico $960K, Infraestructura $600K, Licencias $480K'",
                "ejemplo_malo": "CFDI: 'Management fee 2026'"
            },
            {
                "id": "IMF_F8_02",
                "descripcion": "Pago conforme a metodología de asignación",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "El monto pagado corresponde a la base de asignación documentada",
                "ejemplo_bueno": "Pago $2.04M = 17% del costo total de $12M según metodología de asignación",
                "ejemplo_malo": "Monto arbitrario sin base de cálculo"
            }
        ]
    }
}
