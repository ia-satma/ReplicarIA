"""
Tipologías de Servicio - Revisar.IA
Sistema de Auditoría de Intangibles

Este módulo contiene las tipologías de servicios/intangibles con sus
características de riesgo fiscal inherente, foco de revisión y documentación típica.
"""

from typing import Dict, List, Any, Optional

TIPOLOGIAS_SERVICIO: Dict[str, Dict[str, Any]] = {
    
    "CONSULTORIA_ESTRATEGICA": {
        "nombre": "Consultoría estratégica / de negocio",
        "descripcion": "Servicios de asesoría en estrategia, gestión, transformación organizacional, planeación de negocios.",
        "ejemplos": [
            "Planeación estratégica",
            "Diagnóstico organizacional",
            "Diseño de modelo de negocio",
            "Consultoría de gestión del cambio",
            "Asesoría en gobierno corporativo"
        ],
        "riesgo_fiscal_inherente": "MEDIO-ALTO",
        "razon": "Los entregables suelen ser intangibles (presentaciones, recomendaciones) y es difícil demostrar materialidad sin buena documentación.",
        "foco_de_revision": [
            "Vinculación clara con problema/oportunidad del negocio",
            "Entregables tangibles y específicos",
            "KPIs de éxito medibles",
            "Evidencia de implementación de recomendaciones"
        ],
        "documentos_tipicos": [
            "Propuesta/SOW con alcance detallado",
            "Metodología documentada",
            "Diagnóstico o análisis inicial",
            "Presentaciones de avance",
            "Informe final con recomendaciones",
            "Plan de acción derivado",
            "Minutas de sesiones de trabajo"
        ],
        "alertas_especiales": [
            "Descripciones vagas como 'asesoría general'",
            "Montos desproporcionados vs alcance",
            "Ausencia de entregables tangibles"
        ],
        "revision_humana_obligatoria": False
    },
    
    "CONSULTORIA_MACRO_MERCADO": {
        "nombre": "Estudios macroeconómicos, de mercado, regulatorios",
        "descripcion": "Estudios especializados que analizan entorno macro, mercado, regulación, tendencias, para informar decisiones de negocio.",
        "ejemplos": [
            "Estudio de mercado",
            "Análisis macroeconómico sectorial",
            "Estudios regulatorios y de impacto normativo",
            "Estudios de factibilidad",
            "Análisis de competencia"
        ],
        "riesgo_fiscal_inherente": "MEDIO",
        "razon": "Generalmente producen entregables documentales claros, pero el vínculo con beneficio económico puede ser indirecto.",
        "foco_de_revision": [
            "Uso real del estudio en decisiones de negocio",
            "Conexión con Plan Estratégico",
            "Metodología y fuentes verificables",
            "ROI aunque sea indirecto"
        ],
        "documentos_tipicos": [
            "Contrato/SOW con entregables listados",
            "Informe final con metodología y fuentes",
            "Modelo cuantitativo/paramétrico",
            "Dashboard o herramientas de visualización",
            "Manual metodológico para replicar",
            "Minutas de sesiones de trabajo",
            "Presentaciones ejecutivas"
        ],
        "alertas_especiales": [
            "Estudios genéricos sin foco en el negocio específico",
            "Ausencia de conexión con decisiones concretas",
            "Falta de uso posterior del estudio"
        ],
        "revision_humana_obligatoria": False
    },
    
    "SOFTWARE_SAAS_DESARROLLO": {
        "nombre": "Desarrollo de software, licencias, SaaS",
        "descripcion": "Servicios de desarrollo de software a la medida, licenciamiento, suscripciones SaaS, implementación de sistemas.",
        "ejemplos": [
            "Desarrollo de aplicaciones a la medida",
            "Implementación de ERP/CRM",
            "Licencias de software",
            "Suscripciones SaaS",
            "Mantenimiento y soporte de sistemas"
        ],
        "riesgo_fiscal_inherente": "MEDIO",
        "razon": "Generalmente hay evidencia tangible (código, sistemas funcionando), pero la valuación puede ser compleja si se capitaliza.",
        "foco_de_revision": [
            "Evidencia de desarrollo real (commits, tickets, sprints)",
            "Pruebas de uso efectivo del sistema",
            "Valuación correcta si se capitaliza como activo",
            "Coherencia entre desarrollo y precio pagado"
        ],
        "documentos_tipicos": [
            "Contrato de desarrollo o licencia",
            "Especificaciones funcionales/técnicas",
            "Bitácora de desarrollo (tickets, commits)",
            "Evidencia de pruebas/QA",
            "Manual de usuario y técnico",
            "Logs de uso del sistema",
            "Acta de aceptación"
        ],
        "alertas_especiales": [
            "Sistemas que nunca se usan",
            "Desarrollo sin especificaciones previas",
            "Precios muy altos sin justificación técnica",
            "Capitalización incorrecta vs gasto"
        ],
        "revision_humana_obligatoria": False
    },
    
    "MARKETING_BRANDING": {
        "nombre": "Marketing digital, branding, campañas publicitarias",
        "descripcion": "Servicios de mercadotecnia, publicidad, construcción de marca, campañas digitales, relaciones públicas.",
        "ejemplos": [
            "Campañas de publicidad digital",
            "Branding y diseño de identidad",
            "Social media marketing",
            "SEO/SEM",
            "Producción de contenidos",
            "Relaciones públicas"
        ],
        "riesgo_fiscal_inherente": "ALTO",
        "razon": "Es una de las categorías más cuestionadas por SAT. Dificultad para demostrar que las campañas realmente se ejecutaron y generaron valor.",
        "foco_de_revision": [
            "Evidencia de ejecución real de campañas",
            "Reportes de plataformas (Meta, Google, etc.)",
            "KPIs y resultados medibles",
            "Relación con ingresos o estrategia comercial"
        ],
        "documentos_tipicos": [
            "Contrato con tipo de campaña, medios, KPIs",
            "Brief creativo aprobado",
            "Capturas de anuncios publicados",
            "Reportes de plataformas publicitarias",
            "Métricas de resultados (impresiones, clics, conversiones)",
            "Análisis de ROI de campaña",
            "Facturas de medios/terceros"
        ],
        "alertas_especiales": [
            "Campañas sin evidencia de publicación",
            "Ausencia de reportes de plataformas",
            "KPIs no verificables",
            "Montos altos sin correlación con alcance",
            "Servicios 'de posicionamiento' vagos"
        ],
        "revision_humana_obligatoria": False
    },
    
    "INTRAGRUPO_MANAGEMENT_FEE": {
        "nombre": "Servicios intra-grupo, management fees, soporte corporativo",
        "descripcion": "Servicios prestados entre empresas del mismo grupo: administración centralizada, soporte corporativo, regalías, fees de gestión.",
        "ejemplos": [
            "Management fees",
            "Servicios administrativos compartidos",
            "Soporte de TI centralizado",
            "Regalías por uso de marca",
            "Servicios de tesorería centralizada",
            "Servicios de recursos humanos compartidos"
        ],
        "riesgo_fiscal_inherente": "MUY ALTO",
        "razon": "Altamente escrutados por SAT. Riesgo de precios de transferencia, duplicidad de funciones, erosión de base gravable.",
        "foco_de_revision": [
            "Documentación completa de precios de transferencia",
            "Demostración de que los servicios se prestan realmente",
            "Inexistencia de duplicidad de funciones",
            "Beneficio real para la receptora del servicio",
            "Método de TP y comparables"
        ],
        "documentos_tipicos": [
            "Contrato de servicios intra-grupo",
            "Estudio de precios de transferencia",
            "Desglose de servicios y base de asignación",
            "Reportes periódicos de servicios prestados",
            "Registro de horas por servicio",
            "Minutas de comités de gestión",
            "Evidencia de capacidad del prestador"
        ],
        "alertas_especiales": [
            "Servicios genéricos 'de gestión' sin desglose",
            "Ausencia de estudio de TP",
            "Duplicidad con funciones internas",
            "Prestador sin capacidad real (EFOS potencial)",
            "Bases de asignación arbitrarias"
        ],
        "revision_humana_obligatoria": True
    },
    
    "SERVICIOS_ESG_CUMPLIMIENTO": {
        "nombre": "Servicios de ESG, cumplimiento, sostenibilidad",
        "descripcion": "Consultoría en temas ambientales, sociales, de gobierno corporativo, compliance, certificaciones.",
        "ejemplos": [
            "Diagnóstico ESG",
            "Implementación de sistemas de compliance",
            "Certificaciones ambientales",
            "Reportes de sostenibilidad",
            "Due diligence de cumplimiento"
        ],
        "riesgo_fiscal_inherente": "MEDIO",
        "razon": "Área relativamente nueva, pero generalmente produce entregables tangibles. El reto es demostrar necesidad/indispensabilidad.",
        "foco_de_revision": [
            "Vinculación con requisitos regulatorios o de mercado",
            "Entregables concretos (reportes, certificaciones)",
            "Uso real de los resultados"
        ],
        "documentos_tipicos": [
            "Contrato con alcance específico",
            "Diagnóstico o gap analysis",
            "Plan de acción",
            "Reportes de implementación",
            "Certificaciones obtenidas",
            "Evidencia de auditorías"
        ],
        "alertas_especiales": [],
        "revision_humana_obligatoria": False
    },
    
    "REESTRUCTURAS": {
        "nombre": "Servicios relacionados con reestructuras corporativas",
        "descripcion": "Asesoría en fusiones, escisiones, adquisiciones, reestructuras societarias, valuaciones.",
        "ejemplos": [
            "Due diligence financiero/legal/fiscal",
            "Valuación de empresas",
            "Asesoría en M&A",
            "Diseño de estructuras corporativas",
            "Integración post-fusión"
        ],
        "riesgo_fiscal_inherente": "MUY ALTO",
        "razon": "Operaciones de alto monto y complejidad, frecuentemente involucran partes relacionadas y pueden tener implicaciones fiscales significativas.",
        "foco_de_revision": [
            "Valuaciones con metodología sólida",
            "Independencia de los asesores",
            "Razón de negocios de la reestructura",
            "Implicaciones fiscales documentadas"
        ],
        "documentos_tipicos": [
            "Contrato de asesoría",
            "Informe de due diligence",
            "Valuación independiente",
            "Memorando de transacción",
            "Opiniones legales/fiscales",
            "Documentos societarios"
        ],
        "alertas_especiales": [
            "Valuaciones sin metodología clara",
            "Asesores relacionados con las partes",
            "Estructuras artificiales",
            "Beneficios fiscales sin sustancia económica"
        ],
        "revision_humana_obligatoria": True
    },
    
    "OTROS": {
        "nombre": "Otros servicios no clasificados",
        "descripcion": "Servicios que no encajan en las categorías anteriores.",
        "ejemplos": [],
        "riesgo_fiscal_inherente": "VARIABLE",
        "razon": "Requiere análisis caso por caso.",
        "foco_de_revision": [
            "Aplicar criterios generales de los 4 pilares",
            "Evaluar caso por caso"
        ],
        "documentos_tipicos": [],
        "alertas_especiales": [],
        "requiere_tipificacion_manual": True,
        "revision_humana_obligatoria": False
    }
}


def obtener_tipologia(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de una tipología específica.
    """
    return TIPOLOGIAS_SERVICIO.get(codigo)


def obtener_riesgo_inherente(codigo: str) -> Optional[str]:
    """
    Obtiene el nivel de riesgo fiscal inherente de una tipología.
    """
    tipologia = obtener_tipologia(codigo)
    if tipologia:
        return tipologia.get("riesgo_fiscal_inherente")
    return None


def requiere_revision_humana_por_tipologia(codigo: str) -> bool:
    """
    Determina si una tipología requiere revisión humana obligatoria.
    """
    tipologia = obtener_tipologia(codigo)
    if tipologia:
        return tipologia.get("revision_humana_obligatoria", False)
    return False


def obtener_documentos_tipicos(codigo: str) -> List[str]:
    """
    Obtiene la lista de documentos típicos para una tipología.
    """
    tipologia = obtener_tipologia(codigo)
    if tipologia:
        return tipologia.get("documentos_tipicos", [])
    return []


def obtener_alertas_especiales(codigo: str) -> List[str]:
    """
    Obtiene las alertas especiales para una tipología.
    """
    tipologia = obtener_tipologia(codigo)
    if tipologia:
        return tipologia.get("alertas_especiales", [])
    return []


def listar_tipologias() -> List[str]:
    """
    Lista todas las tipologías disponibles.
    """
    return list(TIPOLOGIAS_SERVICIO.keys())


def obtener_tipologias_alto_riesgo() -> List[str]:
    """
    Obtiene las tipologías con riesgo fiscal inherente ALTO o MUY ALTO.
    """
    alto_riesgo = []
    for codigo, tipologia in TIPOLOGIAS_SERVICIO.items():
        riesgo = tipologia.get("riesgo_fiscal_inherente", "")
        if "ALTO" in riesgo:
            alto_riesgo.append(codigo)
    return alto_riesgo
