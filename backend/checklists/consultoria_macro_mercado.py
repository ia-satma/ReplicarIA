"""
Checklist para Consultoría Macro/Mercado - Revisar.IA
Estudios macroeconómicos, de mercado, regulatorios
"""

from typing import Dict, Any, List

CHECKLIST_CONSULTORIA_MACRO_MERCADO: Dict[str, Any] = {
    
    "tipologia": "CONSULTORIA_MACRO_MERCADO",
    "nombre": "Estudios macroeconómicos, de mercado, regulatorios",
    "riesgo_inherente": "BAJO",
    "revision_humana_obligatoria": False,
    
    "F0": {
        "nombre": "Aprobación - Definir BEE",
        "items": [
            {
                "id": "CMM_F0_01",
                "descripcion": "SIB (Service Initiation Brief) con objetivo del estudio claramente definido",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento que especifique: qué se quiere conocer, por qué se necesita, cómo se usará",
                "ejemplo_bueno": "SIB que dice: 'Estudio para dimensionar demanda residencial premium NL 2026-2028, para informar decisiones de inversión en nuevos desarrollos'",
                "ejemplo_malo": "SIB que dice: 'Estudio de mercado general'"
            },
            {
                "id": "CMM_F0_02",
                "descripcion": "BEE (Beneficio Económico Esperado) con ROI estimado",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento o sección del SIB que cuantifique: beneficio esperado, ROI estimado, horizonte temporal",
                "ejemplo_bueno": "ROI 2.5x: mejor asignación de CAPEX estimada en $15M sobre horizonte de 24 meses",
                "ejemplo_malo": "'El estudio nos ayudará a tomar mejores decisiones'"
            },
            {
                "id": "CMM_F0_03",
                "descripcion": "Vinculación documentada con Plan Estratégico",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Referencia específica a qué iniciativa/objetivo del plan estratégico soporta este estudio",
                "ejemplo_bueno": "Soporta Iniciativa 3.2 del PE 2025-2028: 'Expansión a nuevos mercados geográficos'",
                "ejemplo_malo": "'Está alineado con nuestra estrategia'"
            },
            {
                "id": "CMM_F0_04",
                "descripcion": "Evaluación inicial de riesgo fiscal por A3",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Dictamen preliminar de A3 con risk_score inicial y observaciones",
                "ejemplo_bueno": "Risk score inicial: 22/100 - Bajo riesgo. Observación: asegurar entregables tangibles",
                "ejemplo_malo": "Sin evaluación fiscal previa"
            }
        ]
    },
    
    "F1": {
        "nombre": "Pre-contratación / SOW",
        "items": [
            {
                "id": "CMM_F1_01",
                "descripcion": "SOW o propuesta con alcance del estudio definido",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Documento con: objetivo, alcance geográfico/temporal, metodología general, fuentes a consultar",
                "ejemplo_bueno": "SOW con: 'Análisis de mercado residencial premium en ZMM, horizonte 2026-2028, metodología PESTEL + análisis cuantitativo de demanda'",
                "ejemplo_malo": "'Estudio de mercado completo'"
            },
            {
                "id": "CMM_F1_02",
                "descripcion": "Lista de entregables específicos",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Enumeración clara de qué documentos/archivos se recibirán",
                "ejemplo_bueno": "1) Informe ejecutivo (30-50 pp), 2) Informe técnico completo (150-200 pp), 3) Modelo paramétrico Excel, 4) Dashboard interactivo, 5) Manual metodológico",
                "ejemplo_malo": "'Entregables según lo acordado'"
            },
            {
                "id": "CMM_F1_03",
                "descripcion": "Cronograma de hitos con fechas estimadas",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Timeline con al menos: kick-off, entrega V1, revisión, entrega final",
                "ejemplo_bueno": "Kick-off: Sem 1 | V1 borrador: Sem 4 | Revisión: Sem 5-6 | Entrega final: Sem 8",
                "ejemplo_malo": "'Duración estimada: 2 meses'"
            },
            {
                "id": "CMM_F1_04",
                "descripcion": "Esquema de honorarios/precio",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Monto total y forma de pago (único, por hitos, etc.)",
                "ejemplo_bueno": "$1,250,000 MXN: 30% anticipo, 40% entrega V1, 30% entrega final",
                "ejemplo_malo": "'Precio a convenir'"
            },
            {
                "id": "CMM_F1_05",
                "descripcion": "Criterios de aceptación del estudio",
                "obligatorio": False,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Qué condiciones debe cumplir el entregable para considerarse aceptado",
                "ejemplo_bueno": "Aceptación si: 1) Cubre las 5 zonas geográficas acordadas, 2) Incluye proyecciones a 3 años, 3) Modelo paramétrico funcional con al menos 10 variables",
                "ejemplo_malo": "'A satisfacción del cliente'"
            }
        ]
    },
    
    "F2": {
        "nombre": "Validación previa al inicio",
        "items": [
            {
                "id": "CMM_F2_01",
                "descripcion": "Confirmación de presupuesto disponible",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Documento o registro de A5 confirmando partida presupuestal",
                "ejemplo_bueno": "Confirmación A5: Presupuesto disponible en partida 'Estudios y Consultoría 2026' - $1.5M asignados",
                "ejemplo_malo": "Sin confirmación de presupuesto"
            },
            {
                "id": "CMM_F2_02",
                "descripcion": "Contrato o SOW firmado",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Documento con firmas de ambas partes y fecha",
                "ejemplo_bueno": "Contrato firmado el 15/mar/2026 por representantes autorizados",
                "ejemplo_malo": "Solo propuesta enviada por correo sin aceptación formal"
            },
            {
                "id": "CMM_F2_03",
                "descripcion": "Revisión humana obtenida (si aplica por umbral)",
                "obligatorio": False,
                "responsable": "PMO",
                "criterio_aceptacion": "Si monto >= $5M o risk_score >= 60, documentar aprobación humana",
                "ejemplo_bueno": "Proyecto de $1.25M con risk_score 22: No requiere revisión humana adicional",
                "ejemplo_malo": "Proyecto de $8M sin ninguna revisión humana documentada"
            }
        ]
    },
    
    "F3": {
        "nombre": "Ejecución inicial",
        "items": [
            {
                "id": "CMM_F3_01",
                "descripcion": "Minuta de kick-off con asistentes y acuerdos",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Documento con: fecha, asistentes, temas tratados, acuerdos, próximos pasos",
                "ejemplo_bueno": "Minuta kick-off 5/abr: Asistentes (lista), Acuerdos: fuentes a consultar, zonas prioritarias, formato de entregas",
                "ejemplo_malo": "Sin registro de reunión inicial"
            },
            {
                "id": "CMM_F3_02",
                "descripcion": "Entregable V1 / borrador inicial",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Primera versión identificable del estudio, aunque sea preliminar",
                "ejemplo_bueno": "Informe V1.0 - Borrador 15/may - 80 páginas con análisis preliminar",
                "ejemplo_malo": "Solo presentación de 10 slides genéricas"
            },
            {
                "id": "CMM_F3_03",
                "descripcion": "Registro de fuentes consultadas",
                "obligatorio": False,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Lista de fuentes de información utilizadas",
                "ejemplo_bueno": "Fuentes: INEGI, Banxico, AMPI, entrevistas a 15 desarrolladores locales",
                "ejemplo_malo": "Sin mención de fuentes"
            }
        ]
    },
    
    "F4": {
        "nombre": "Revisión iterativa",
        "items": [
            {
                "id": "CMM_F4_01",
                "descripcion": "Versiones sucesivas del entregable (V1.1, V1.2, V2, etc.)",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Al menos una versión revisada después de retroalimentación",
                "ejemplo_bueno": "V1.0 (15/may) → V1.2 (25/may) con ajustes en proyecciones → V2.0 (10/jun) versión final",
                "ejemplo_malo": "Solo una versión sin iteración"
            },
            {
                "id": "CMM_F4_02",
                "descripcion": "Registro de observaciones y cómo se atendieron",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento o correos que muestren qué se pidió ajustar y qué se hizo",
                "ejemplo_bueno": "Correo 20/may: 'Favor incluir análisis de zona Valle Poniente'. Respuesta 25/may: 'Incluido en V1.2 sección 4.3'",
                "ejemplo_malo": "Sin registro de retroalimentación"
            },
            {
                "id": "CMM_F4_03",
                "descripcion": "Minuta(s) de sesiones de revisión",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Al menos 1-2 minutas de sesiones de trabajo/revisión",
                "ejemplo_bueno": "Minuta sesión revisión 22/may: Asistentes, observaciones al V1, acuerdos para V2",
                "ejemplo_malo": "Sin minutas de reuniones"
            }
        ]
    },
    
    "F5": {
        "nombre": "Entrega final / Aceptación técnica",
        "items": [
            {
                "id": "CMM_F5_01",
                "descripcion": "Informe final completo y versionado",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Documento final con número de versión, fecha, índice, metodología, hallazgos, conclusiones",
                "ejemplo_bueno": "Informe Final V2.0 - 'Estudio de Mercado Residencial Premium NL 2026-2028' - 180 páginas - 30/jun/2026",
                "ejemplo_malo": "Documento sin versión ni fecha, incompleto"
            },
            {
                "id": "CMM_F5_02",
                "descripcion": "Modelo paramétrico / cuantitativo funcional",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Archivo Excel/herramienta con modelo de proyecciones que funcione y sea modificable",
                "ejemplo_bueno": "Modelo Excel con 12 variables ajustables, proyecciones a 3 años, escenarios base/optimista/pesimista",
                "ejemplo_malo": "Excel con datos estáticos sin fórmulas"
            },
            {
                "id": "CMM_F5_03",
                "descripcion": "Dashboard interactivo (si aplica)",
                "obligatorio": False,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Herramienta de visualización funcional (Power BI, Tableau, web)",
                "ejemplo_bueno": "Dashboard Power BI con 8 indicadores clave, filtros por zona y segmento, actualizable",
                "ejemplo_malo": "Capturas de pantalla estáticas"
            },
            {
                "id": "CMM_F5_04",
                "descripcion": "Manual metodológico",
                "obligatorio": True,
                "responsable": "PROVEEDOR",
                "criterio_aceptacion": "Documento que explique metodología utilizada para replicabilidad",
                "ejemplo_bueno": "Manual de 25 páginas explicando: fuentes, métodos de análisis, supuestos, limitaciones",
                "ejemplo_malo": "Sin documentación de metodología"
            },
            {
                "id": "CMM_F5_05",
                "descripcion": "Acta de aceptación técnica firmada",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Documento donde el área usuaria acepta formalmente el entregable",
                "ejemplo_bueno": "Acta firmada por Director de Planeación: 'Se acepta el estudio cumpliendo los criterios acordados'",
                "ejemplo_malo": "Solo correo informal diciendo 'ok, recibido'"
            }
        ]
    },
    
    "F6": {
        "nombre": "Visto Bueno Fiscal/Legal",
        "items": [
            {
                "id": "CMM_F6_01",
                "descripcion": "Matriz de materialidad completa (>80%)",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Tabla que vincule cada hecho relevante con su evidencia documental",
                "ejemplo_bueno": "Matriz con 15 hechos, 14 con evidencia OK (93% completitud)",
                "ejemplo_malo": "Sin matriz o con menos de 80% de evidencias"
            },
            {
                "id": "CMM_F6_02",
                "descripcion": "Contrato/anexo final que refleje realidad del servicio",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Versión final del contrato congruente con lo entregado",
                "ejemplo_bueno": "Contrato con anexo técnico que lista los mismos entregables que se recibieron",
                "ejemplo_malo": "Contrato genérico que no menciona los entregables específicos"
            },
            {
                "id": "CMM_F6_03",
                "descripcion": "VBC Fiscal emitido por A3",
                "obligatorio": True,
                "responsable": "FISCAL",
                "criterio_aceptacion": "Documento de A3 aprobando el proyecto desde perspectiva tributaria",
                "ejemplo_bueno": "VBC Fiscal firmado: 'Se aprueba la deducibilidad del gasto. Risk score final: 16/100'",
                "ejemplo_malo": "Sin VBC o con VBC condicionado sin resolver condiciones"
            },
            {
                "id": "CMM_F6_04",
                "descripcion": "VBC Legal emitido por A4",
                "obligatorio": True,
                "responsable": "LEGAL",
                "criterio_aceptacion": "Documento de A4 aprobando el proyecto desde perspectiva jurídica",
                "ejemplo_bueno": "VBC Legal firmado: 'Documentación contractual completa y coherente'",
                "ejemplo_malo": "Sin VBC Legal"
            }
        ]
    },
    
    "F7": {
        "nombre": "Auditoría interna",
        "items": [
            {
                "id": "CMM_F7_01",
                "descripcion": "Informe de auditoría interna / control",
                "obligatorio": True,
                "responsable": "PMO",
                "criterio_aceptacion": "Revisión de que se siguió el POE y Defense File está completo",
                "ejemplo_bueno": "Informe AI: 'Se verificó cumplimiento de F0-F6, Defense File completo con 22 documentos'",
                "ejemplo_malo": "Sin revisión de auditoría interna"
            }
        ]
    },
    
    "F8": {
        "nombre": "CFDI y pago",
        "items": [
            {
                "id": "CMM_F8_01",
                "descripcion": "CFDI con descripción específica del servicio",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Factura cuyo concepto coincida con el objeto del contrato",
                "ejemplo_bueno": "CFDI: 'Estudio de mercado residencial premium Nuevo León 2026-2028 según contrato XXX'",
                "ejemplo_malo": "CFDI: 'Servicios profesionales varios'"
            },
            {
                "id": "CMM_F8_02",
                "descripcion": "Comprobante de pago por medios trazables",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Transferencia bancaria con referencia identificable",
                "ejemplo_bueno": "Transferencia SPEI del 15/jul al RFC XXX por $1,250,000 ref: Estudio Mercado NL",
                "ejemplo_malo": "Pago en efectivo sin comprobante"
            },
            {
                "id": "CMM_F8_03",
                "descripcion": "Conciliación contable / registro en póliza",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Asiento contable que registre el gasto en cuenta apropiada",
                "ejemplo_bueno": "Póliza 2026-0458: Cargo a 'Gastos - Estudios y Consultoría' $1,250,000",
                "ejemplo_malo": "Sin registro contable"
            },
            {
                "id": "CMM_F8_04",
                "descripcion": "3-way match validado",
                "obligatorio": True,
                "responsable": "FINANZAS",
                "criterio_aceptacion": "Verificación de que CFDI, contrato y pago coinciden en monto y concepto",
                "ejemplo_bueno": "3-way match OK: Contrato $1.25M = CFDI $1.25M = Pago $1.25M",
                "ejemplo_malo": "Montos diferentes entre documentos"
            }
        ]
    },
    
    "F9": {
        "nombre": "Post-implementación",
        "items": [
            {
                "id": "CMM_F9_01",
                "descripcion": "Informe de seguimiento del BEE (a 6, 12 o 24 meses)",
                "obligatorio": True,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Evaluación de si los beneficios esperados se están cumpliendo",
                "ejemplo_bueno": "Seguimiento 12 meses: 'El estudio informó 3 decisiones de inversión por $45M. ROI parcial: 1.8x vs 2.5x esperado'",
                "ejemplo_malo": "Sin seguimiento post-implementación"
            },
            {
                "id": "CMM_F9_02",
                "descripcion": "Documentación de usos concretos del estudio",
                "obligatorio": False,
                "responsable": "SPONSOR",
                "criterio_aceptacion": "Registro de cómo se utilizó el estudio en decisiones reales",
                "ejemplo_bueno": "El estudio se usó para: 1) Definir ubicación de Proyecto Cumbres, 2) Ajustar pricing de Torre Valle, 3) Descartar proyecto en zona saturada",
                "ejemplo_malo": "Sin evidencia de uso del estudio"
            }
        ]
    }
}
