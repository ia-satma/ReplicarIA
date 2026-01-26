"""
Few-Shot Examples para Revisar.IA
Casos modelo para calibrar decisiones de agentes (APROBAR, SOLICITAR_AJUSTES, RECHAZAR)
"""

from typing import Dict, Any

FEW_SHOT_EXAMPLES: Dict[str, Dict[str, Any]] = {
    
    "APROBAR": {
        "metadata": {
            "id": "EJEMPLO_APROBAR_001",
            "nombre": "Estudio de Mercado Residencial Premium NL 2026",
            "tipologia": "CONSULTORIA_MACRO_MERCADO",
            "monto": 1250000,
            "moneda": "MXN"
        },
        
        "descripcion_proyecto": """
Empresa desarrolladora inmobiliaria contrata estudio de mercado para:
- Analizar demanda residencial premium en Nuevo León horizonte 2026
- Proyectar precios y absorción por zona geográfica
- Identificar competidores y factores diferenciadores
- Generar modelo paramétrico para decisiones de inversión
- Entregar dashboard interactivo para monitoreo continuo
        """,
        
        "contexto_empresa": "Grupo inmobiliario con ingresos anuales de $500M MXN, operando en segmento residencial premium en Nuevo León y Nayarit. El estudio alimentará el Plan Estratégico 2026-2028.",
        
        "proveedor": {
            "nombre": "Consultoría Económica Especializada SA",
            "rfc": "CES890101XXX",
            "tipo_relacion": "TERCERO_INDEPENDIENTE",
            "historial": "Sin proyectos previos con el grupo, pero con track record verificable en estudios similares"
        },
        
        "analisis_por_pilar": {
            "razon_negocios": {
                "status": "CONFORME",
                "detalle": "El estudio se vincula directamente con el Pipeline de Proyectos 2026-2028. La empresa opera en el segmento residencial premium en NL, exactamente lo que analiza el estudio. Existe conexión clara entre el estudio y decisiones de inversión de alto impacto (apertura de nuevos desarrollos, timing de lanzamientos, pricing).",
                "riesgo_puntos": 3,
                "justificacion_puntos": "Vinculación fuerte con giro (0), objetivo claro con KPIs (0), monto razonable 0.25% de ventas (3)"
            },
            "beneficio_economico": {
                "status": "CONFORME",
                "detalle": "ROI estimado de 2.5x documentado y razonable: mejor asignación de CAPEX evitando proyectos subóptimos, timing optimizado de lanzamientos basado en proyecciones de demanda, pricing basado en datos de mercado. Horizonte de 24 meses congruente con ciclo de desarrollo inmobiliario.",
                "riesgo_puntos": 5,
                "justificacion_puntos": "Beneficios específicos identificados (0), ROI documentado con metodología (5 - podría tener más detalle), horizonte razonable (0)"
            },
            "materialidad": {
                "status": "CONFORME",
                "detalle": "Entregables claros y tangibles: informe final de 180 páginas con metodología PESTEL, modelo Excel paramétrico con 12 variables, dashboard Power BI operativo con 8 indicadores clave, manual metodológico de 25 páginas, 3 minutas de sesiones de trabajo con asistentes y acuerdos documentados.",
                "riesgo_puntos": 5,
                "justificacion_puntos": "Contrato con entregables específicos (0), evidencias abundantes de ejecución (0), CFDI específico 'Estudio de mercado residencial NL' (5 - verificar descripción)"
            },
            "trazabilidad": {
                "status": "CONFORME",
                "detalle": "Todos los documentos versionados (V1.0, V1.2, V2.0), fechados, con hash SHA-256 calculado, integrados en Defense File estructurado. Timeline reconstruible: propuesta (15/mar) → contrato (1/abr) → kick-off (5/abr) → V1 (15/may) → V2 (10/jun) → entrega final (30/jun) → factura (5/jul) → pago (15/jul).",
                "riesgo_puntos": 3,
                "justificacion_puntos": "Expediente estructurado (0), mecanismo de integridad (0), timeline claro con pequeños huecos no críticos (3)"
            }
        },
        
        "risk_score": {
            "total": 16,
            "desglose": {
                "razon_negocios": 3,
                "beneficio_economico": 5,
                "materialidad": 5,
                "trazabilidad": 3
            }
        },
        
        "checklist_cumplido": [
            {"item": "SIB con BEE documentado", "estado": "ENTREGADO"},
            {"item": "Contrato con entregables listados", "estado": "ENTREGADO"},
            {"item": "Informe final versionado", "estado": "ENTREGADO"},
            {"item": "Modelo paramétrico funcional", "estado": "ENTREGADO"},
            {"item": "Dashboard operativo", "estado": "ENTREGADO"},
            {"item": "Manual metodológico", "estado": "ENTREGADO"},
            {"item": "Minutas de sesiones (mín 2)", "estado": "ENTREGADO"},
            {"item": "CFDI específico", "estado": "ENTREGADO"},
            {"item": "Comprobante de pago", "estado": "ENTREGADO"}
        ],
        
        "decision": "APROBAR",
        
        "justificacion_decision": "El proyecto cumple con los 4 pilares fiscales de forma satisfactoria. La razón de negocios está claramente vinculada al giro y plan estratégico. El BEE está documentado con ROI razonable. Existe materialidad abundante con entregables tangibles. La trazabilidad es completa. Risk score de 16/100 indica bajo riesgo fiscal. No se requiere revisión humana adicional.",
        
        "notas_para_agentes": "Este caso representa el estándar de lo que debe considerarse un proyecto bien documentado y defendible ante SAT."
    },
    
    "SOLICITAR_AJUSTES": {
        "metadata": {
            "id": "EJEMPLO_AJUSTES_001",
            "nombre": "Consultoría en Transformación Digital",
            "tipologia": "CONSULTORIA_ESTRATEGICA",
            "monto": 3500000,
            "moneda": "MXN"
        },
        
        "descripcion_proyecto": """
Empresa contrata consultoría para "transformación digital" con alcance inicial:
- Diagnóstico de madurez digital
- Diseño de estrategia de transformación
- Roadmap de implementación
- Acompañamiento inicial
        """,
        
        "contexto_empresa": "Empresa manufacturera con $800M MXN de ingresos, buscando modernizar operaciones y canales de venta.",
        
        "proveedor": {
            "nombre": "Digital Consulting Partners SC",
            "rfc": "DCP150601XXX",
            "tipo_relacion": "TERCERO_INDEPENDIENTE",
            "historial": "Un proyecto previo de $500K hace 2 años, sin incidentes"
        },
        
        "analisis_por_pilar": {
            "razon_negocios": {
                "status": "CONDICIONADO",
                "detalle": "El objetivo 'transformación digital' es genérico. No se especifica qué procesos se transformarán, qué sistemas se implementarán, qué eficiencias específicas se esperan. Existe vínculo con el negocio (manufacturera que quiere modernizarse) pero falta concreción.",
                "riesgo_puntos": 13,
                "justificacion_puntos": "Vinculación genérica (3), objetivo vago sin métricas (10), monto alto pero podría justificarse (0)"
            },
            "beneficio_economico": {
                "status": "NO_CONFORME",
                "detalle": "No existe ROI cuantificado. La propuesta menciona 'mejora competitiva' y 'eficiencias operativas' pero sin números. No hay horizonte temporal definido para ver resultados. No hay KPIs de éxito medibles.",
                "riesgo_puntos": 20,
                "justificacion_puntos": "Beneficios genéricos (10), sin ROI ni proyecciones (10), sin horizonte definido (0 - no penaliza doble)"
            },
            "materialidad": {
                "status": "EN_RIESGO",
                "detalle": "El SOW actual solo menciona 'diagnóstico y estrategia' sin listar entregables específicos. No hay criterios de aceptación. No hay cronograma de hitos. El riesgo es que al final solo haya un PowerPoint genérico.",
                "riesgo_puntos": 15,
                "justificacion_puntos": "SOW sin entregables específicos (3), sin evidencias de ejecución aún - normal en F0 (7), coherencia por verificar (5)"
            },
            "trazabilidad": {
                "status": "EN_RIESGO",
                "detalle": "Solo existe una propuesta en PDF sin fecha cierta. No hay contrato formalizado aún. No hay mecanismo de integridad documental establecido.",
                "riesgo_puntos": 10,
                "justificacion_puntos": "Archivos dispersos (5), sin mecanismo de integridad (5), timeline incompleto pero es inicio (0)"
            }
        },
        
        "risk_score": {
            "total": 58,
            "desglose": {
                "razon_negocios": 13,
                "beneficio_economico": 20,
                "materialidad": 15,
                "trazabilidad": 10
            }
        },
        
        "brechas_identificadas": [
            {
                "pilar": "Razón de negocios",
                "brecha": "Objetivo demasiado genérico",
                "accion_correctiva": "Especificar en SOW: qué procesos concretos se analizarán/transformarán (ej: cadena de suministro, CRM, ERP)",
                "responsable": "A1_SPONSOR con A4_LEGAL"
            },
            {
                "pilar": "Beneficio económico",
                "brecha": "Sin ROI cuantificado",
                "accion_correctiva": "Agregar en SIB: ROI mínimo esperado, horizonte temporal, al menos 3 KPIs medibles",
                "responsable": "A1_SPONSOR con A5_FINANZAS"
            },
            {
                "pilar": "Materialidad",
                "brecha": "Entregables no especificados",
                "accion_correctiva": "Modificar SOW para incluir: lista de entregables con formato y extensión esperada, cronograma de hitos, criterios de aceptación",
                "responsable": "A4_LEGAL"
            },
            {
                "pilar": "Trazabilidad",
                "brecha": "Sin contrato formalizado",
                "accion_correctiva": "Formalizar contrato antes de F2 con mecanismo de fecha cierta",
                "responsable": "A4_LEGAL"
            }
        ],
        
        "checklist_pendiente": [
            {"item": "SIB con BEE cuantificado", "estado": "PENDIENTE"},
            {"item": "SOW con entregables específicos", "estado": "PENDIENTE"},
            {"item": "Cronograma de hitos", "estado": "PENDIENTE"},
            {"item": "Criterios de aceptación", "estado": "PENDIENTE"},
            {"item": "KPIs medibles definidos", "estado": "PENDIENTE"},
            {"item": "Contrato formalizado", "estado": "PENDIENTE"}
        ],
        
        "decision": "SOLICITAR_AJUSTES",
        
        "justificacion_decision": "El proyecto tiene potencial de ser legítimo - una empresa manufacturera que busca modernizarse es razonable. Sin embargo, la documentación actual es insuficiente para defender ante SAT. Con risk score de 58/100, está en zona de riesgo. Se requieren ajustes específicos antes de proceder. Si se corrigen las brechas identificadas, el proyecto podría pasar a APROBAR.",
        
        "condiciones_para_reevaluar": [
            "SOW modificado con entregables específicos y cronograma",
            "SIB actualizado con ROI estimado y KPIs",
            "Contrato formalizado con cláusulas de materialidad",
            "Compromiso del proveedor de entregar minutas de sesiones"
        ],
        
        "notas_para_agentes": "Este caso ilustra un proyecto 'salvable' pero que requiere trabajo adicional. NO es rechazo, pero tampoco se puede aprobar en su estado actual."
    },
    
    "RECHAZAR": {
        "metadata": {
            "id": "EJEMPLO_RECHAZAR_001",
            "nombre": "Servicios Profesionales de Gestión y Asesoría",
            "tipologia": "INTRAGRUPO_MANAGEMENT_FEE",
            "monto": 8000000,
            "moneda": "MXN"
        },
        
        "descripcion_proyecto": """
Pago a empresa relacionada ubicada en [jurisdicción de baja imposición] por 
"servicios profesionales varios de gestión y asesoría corporativa general".
        """,
        
        "contexto_empresa": "Grupo empresarial con operaciones en México. La empresa receptora del pago se constituyó hace 6 meses en jurisdicción favorable.",
        
        "proveedor": {
            "nombre": "Global Management Services LLC",
            "rfc": "EXTRANJERO_SIN_RFC_MEX",
            "tipo_relacion": "PARTE_RELACIONADA_EXTRANJERA",
            "historial": "Empresa recién constituida, sin historial de operaciones previas, sin empleados visibles"
        },
        
        "analisis_por_pilar": {
            "razon_negocios": {
                "status": "NO_CONFORME",
                "detalle": "No se identifica qué servicio concreto se presta. 'Gestión y asesoría corporativa general' no especifica actividades, funciones ni resultados esperados. No hay vínculo con necesidades operativas documentadas. Parece diseñado para transferir valor, no para recibir un servicio.",
                "riesgo_puntos": 25,
                "justificacion_puntos": "Débilmente vinculado al giro (5), objetivo vago sin ninguna métrica (10), monto claramente desproporcionado (10)"
            },
            "beneficio_economico": {
                "status": "NO_CONFORME",
                "detalle": "Sin ROI documentado. Sin análisis de precios de transferencia. Sin justificación de por qué el monto es de $8M. El beneficio económico aparente es únicamente fiscal (deducción en México, ingreso en jurisdicción de baja imposición).",
                "riesgo_puntos": 25,
                "justificacion_puntos": "Sin beneficios económicos identificables (10), sin ROI ni proyecciones (10), horizonte inexistente (5)"
            },
            "materialidad": {
                "status": "FALLA_CRITICA",
                "detalle": "CFDI genérico 'servicios profesionales varios'. Sin contrato con alcance definido. Sin ningún entregable identificable. Sin minutas, reportes, ni evidencia de trabajo alguno. El proveedor no tiene personal ni infraestructura visible para prestar servicios. Señales de EFOS.",
                "riesgo_puntos": 25,
                "justificacion_puntos": "Sin formalización seria (5), sin evidencia de ejecución (10), discrepancias graves CFDI genérico (10)"
            },
            "trazabilidad": {
                "status": "FALLA_CRITICA",
                "detalle": "Solo existe CFDI y transferencia bancaria. No hay secuencia de propuesta → contrato → ejecución → entregables. El único rastro es: factura → pago. Imposible reconstruir qué servicio se prestó.",
                "riesgo_puntos": 17,
                "justificacion_puntos": "Dependencia de correos sueltos (7), sin integridad documental (5), timeline confuso/inexistente (5)"
            }
        },
        
        "risk_score": {
            "total": 92,
            "desglose": {
                "razon_negocios": 25,
                "beneficio_economico": 25,
                "materialidad": 25,
                "trazabilidad": 17
            }
        },
        
        "alertas_criticas": [
            {
                "tipo": "EFOS_POTENCIAL",
                "severidad": "CRITICA",
                "descripcion": "Proveedor sin capacidad operativa visible, CFDI genérico, monto alto, parte relacionada"
            },
            {
                "tipo": "PARTE_RELACIONADA_EXTRANJERA",
                "severidad": "CRITICA",
                "descripcion": "Operación con empresa relacionada en jurisdicción de baja imposición sin estudio de TP"
            },
            {
                "tipo": "ESQUEMA_REPORTABLE_POSIBLE",
                "severidad": "ALTA",
                "descripcion": "Transferencia de valor significativa sin sustancia económica demostrable"
            },
            {
                "tipo": "TP_NO_DOCUMENTADO",
                "severidad": "CRITICA",
                "descripcion": "Sin estudio de precios de transferencia para operación intra-grupo de $8M"
            }
        ],
        
        "decision": "RECHAZAR",
        
        "justificacion_decision": "El proyecto presenta múltiples señales de simulación o planeación fiscal agresiva sin sustancia. Risk score de 92/100 indica riesgo extremo. No hay razón de negocios identificable más allá del efecto fiscal. No hay materialidad demostrable. El proveedor tiene características de EFOS. Aprobar este proyecto expondría a la empresa a: rechazo de deducción, inclusión en lista 69-B, posible delito fiscal. No es cuestión de 'ajustes' - el proyecto no debe realizarse en su forma actual.",
        
        "recomendaciones_si_es_legitimo": [
            "Si realmente existe un servicio necesario, redefinir completamente el alcance con entregables tangibles",
            "Obtener estudio de precios de transferencia antes de cualquier pago",
            "Documentar capacidad operativa del proveedor (empleados, infraestructura)",
            "Generar evidencia de ejecución real antes de pagar",
            "Considerar si el servicio puede prestarse desde una entidad mexicana"
        ],
        
        "notas_para_agentes": "Este caso representa lo que NUNCA debe aprobarse. Si un proyecto tiene características similares (monto alto + parte relacionada + descripción genérica + sin materialidad), debe rechazarse o al mínimo requerir reestructuración total."
    }
}


def get_ejemplo(decision: str) -> Dict[str, Any]:
    """Obtiene un caso modelo por tipo de decisión"""
    return FEW_SHOT_EXAMPLES.get(decision.upper(), None)


def get_todos_ejemplos() -> Dict[str, Dict[str, Any]]:
    """Obtiene todos los casos modelo"""
    return FEW_SHOT_EXAMPLES
