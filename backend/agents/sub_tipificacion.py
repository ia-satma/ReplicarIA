"""
SUB_TIPIFICACION - Subagente de Tipificación de Proyectos

Clasifica cada proyecto nuevo en la tipología correcta basándose en la 
descripción, objetivo y características del servicio. Esta clasificación 
determina qué checklists aplican y qué nivel de rigor se requiere.
"""

SUB_TIPIFICACION_CONFIG = {
    "id": "SUB_TIPIFICACION",
    "nombre": "Subagente de Tipificación de Proyectos",
    
    "rol": """Clasificar cada proyecto nuevo en la tipología correcta 
    (CONSULTORIA_MACRO_MERCADO, SOFTWARE_SAAS_DESARROLLO, INTRAGRUPO_MANAGEMENT_FEE, etc.) 
    basándose en la descripción, objetivo y características del servicio. 
    Esta clasificación determina qué checklists aplican y qué nivel de rigor se requiere.""",
    
    "contexto_requerido": {
        "obligatorio": [
            "proyecto.nombre",
            "proyecto.descripcion",
            "proyecto.objetivo_declarado",
            "proveedor.tipo_relacion",
            "monto"
        ],
        "deseable": [
            "sow_preliminar",
            "entregables_esperados"
        ]
    },
    
    "fases_participacion": ["F0"],
    "puede_bloquear_avance": False,
    
    "logica_clasificacion": """
REGLAS DE CLASIFICACIÓN:

1. INTRAGRUPO_MANAGEMENT_FEE:
   - SI proveedor.tipo_relacion != 'TERCERO_INDEPENDIENTE'
   - Y descripción incluye: management fee, servicios corporativos, soporte centralizado, regalías
   → Clasificar como INTRAGRUPO_MANAGEMENT_FEE
   → ALERTA: Requiere revisión humana obligatoria

2. SOFTWARE_SAAS_DESARROLLO:
   - SI descripción incluye: desarrollo, sistema, aplicación, software, SaaS, implementación, ERP, CRM
   - Y entregables esperados incluyen: código, sistema, licencia, plataforma
   → Clasificar como SOFTWARE_SAAS_DESARROLLO

3. CONSULTORIA_MACRO_MERCADO:
   - SI descripción incluye: estudio de mercado, análisis macroeconómico, investigación, factibilidad, regulatorio
   - Y entregables incluyen: informe, análisis, modelo, proyecciones
   → Clasificar como CONSULTORIA_MACRO_MERCADO

4. MARKETING_BRANDING:
   - SI descripción incluye: marketing, publicidad, campaña, branding, SEO, redes sociales, contenido
   → Clasificar como MARKETING_BRANDING
   → ALERTA: Tipología de alto escrutinio SAT

5. CONSULTORIA_ESTRATEGICA:
   - SI descripción incluye: estrategia, transformación, consultoría de gestión, diagnóstico organizacional
   - Y NO clasifica en las anteriores
   → Clasificar como CONSULTORIA_ESTRATEGICA

6. REESTRUCTURAS:
   - SI descripción incluye: fusión, escisión, adquisición, M&A, due diligence, valuación de empresa
   → Clasificar como REESTRUCTURAS
   → ALERTA: Requiere revisión humana obligatoria

7. SERVICIOS_ESG_CUMPLIMIENTO:
   - SI descripción incluye: ESG, sostenibilidad, compliance, cumplimiento, certificación ambiental
   → Clasificar como SERVICIOS_ESG_CUMPLIMIENTO

8. OTROS:
   - SI no encaja en ninguna de las anteriores
   → Clasificar como OTROS
   → ALERTA: Requiere tipificación manual por humano
    """,
    
    "output_schema": {
        "tipologia_asignada": {
            "tipo": "enum",
            "valores": [
                "CONSULTORIA_ESTRATEGICA",
                "CONSULTORIA_MACRO_MERCADO",
                "SOFTWARE_SAAS_DESARROLLO",
                "MARKETING_BRANDING",
                "INTRAGRUPO_MANAGEMENT_FEE",
                "SERVICIOS_ESG_CUMPLIMIENTO",
                "REESTRUCTURAS",
                "OTROS"
            ],
            "obligatorio": True
        },
        "confianza_clasificacion": {
            "tipo": "enum",
            "valores": ["ALTA", "MEDIA", "BAJA"],
            "obligatorio": True
        },
        "justificacion": {
            "tipo": "string",
            "min_length": 50,
            "obligatorio": True
        },
        "palabras_clave_detectadas": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "alertas_tipologia": {
            "tipo": "array",
            "items": "string",
            "obligatorio": True
        },
        "requiere_validacion_humana": {
            "tipo": "boolean",
            "obligatorio": True
        },
        "checklist_aplicable": {
            "tipo": "string",
            "descripcion": "Nombre del checklist que aplica según la tipología",
            "obligatorio": True
        }
    }
}

TIPOLOGIA_KEYWORDS = {
    "INTRAGRUPO_MANAGEMENT_FEE": [
        "management fee", "servicios corporativos", "soporte centralizado", 
        "regalías", "intercompany", "intragrupo", "fee corporativo"
    ],
    "SOFTWARE_SAAS_DESARROLLO": [
        "desarrollo", "sistema", "aplicación", "software", "saas", 
        "implementación", "erp", "crm", "código", "plataforma", "app"
    ],
    "CONSULTORIA_MACRO_MERCADO": [
        "estudio de mercado", "análisis macroeconómico", "investigación",
        "factibilidad", "regulatorio", "informe", "proyecciones", "modelo"
    ],
    "MARKETING_BRANDING": [
        "marketing", "publicidad", "campaña", "branding", "seo",
        "redes sociales", "contenido", "digital", "creatividad"
    ],
    "CONSULTORIA_ESTRATEGICA": [
        "estrategia", "transformación", "consultoría de gestión",
        "diagnóstico organizacional", "plan estratégico", "roadmap"
    ],
    "REESTRUCTURAS": [
        "fusión", "escisión", "adquisición", "m&a", "due diligence",
        "valuación de empresa", "restructuración", "merger"
    ],
    "SERVICIOS_ESG_CUMPLIMIENTO": [
        "esg", "sostenibilidad", "compliance", "cumplimiento",
        "certificación ambiental", "normas ambientales", "auditoría ambiental"
    ]
}

TIPOLOGIAS_REVISION_HUMANA = [
    "INTRAGRUPO_MANAGEMENT_FEE",
    "REESTRUCTURAS",
    "OTROS"
]

TIPOLOGIAS_ALTO_ESCRUTINIO = [
    "MARKETING_BRANDING",
    "INTRAGRUPO_MANAGEMENT_FEE"
]

CHECKLIST_POR_TIPOLOGIA = {
    "CONSULTORIA_ESTRATEGICA": "checklist_consultoria_estrategica",
    "CONSULTORIA_MACRO_MERCADO": "checklist_consultoria_macro_mercado",
    "SOFTWARE_SAAS_DESARROLLO": "checklist_software_saas_desarrollo",
    "MARKETING_BRANDING": "checklist_marketing_branding",
    "INTRAGRUPO_MANAGEMENT_FEE": "checklist_intragrupo_management_fee",
    "SERVICIOS_ESG_CUMPLIMIENTO": "checklist_esg_cumplimiento",
    "REESTRUCTURAS": "checklist_reestructuras",
    "OTROS": "checklist_generico"
}


def clasificar_proyecto(proyecto: dict, proveedor: dict) -> dict:
    """
    Clasifica un proyecto en la tipología correcta.
    
    Args:
        proyecto: Datos del proyecto (nombre, descripcion, objetivo_declarado, monto)
        proveedor: Datos del proveedor (tipo_relacion)
    
    Returns:
        Output estructurado con clasificación
    """
    descripcion = proyecto.get("descripcion", "").lower()
    objetivo = proyecto.get("objetivo_declarado", "").lower()
    entregables = proyecto.get("entregables_esperados", [])
    tipo_relacion = proveedor.get("tipo_relacion", "TERCERO_INDEPENDIENTE")
    monto = proyecto.get("monto", 0)
    
    texto_analizar = f"{descripcion} {objetivo} {' '.join(entregables).lower()}"
    
    tipologia_scores = {}
    palabras_detectadas = {}
    
    for tipologia, keywords in TIPOLOGIA_KEYWORDS.items():
        score = 0
        palabras = []
        for keyword in keywords:
            if keyword in texto_analizar:
                score += 1
                palabras.append(keyword)
        tipologia_scores[tipologia] = score
        palabras_detectadas[tipologia] = palabras
    
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        tipologia_scores["INTRAGRUPO_MANAGEMENT_FEE"] += 5
    
    tipologia_asignada = max(tipologia_scores, key=tipologia_scores.get)
    max_score = tipologia_scores[tipologia_asignada]
    
    if max_score == 0:
        tipologia_asignada = "OTROS"
    
    if max_score >= 3:
        confianza = "ALTA"
    elif max_score >= 2:
        confianza = "MEDIA"
    else:
        confianza = "BAJA"
    
    alertas = []
    requiere_validacion = False
    
    if tipologia_asignada in TIPOLOGIAS_REVISION_HUMANA:
        requiere_validacion = True
        alertas.append(f"Tipología {tipologia_asignada} requiere revisión humana obligatoria")
    
    if tipologia_asignada in TIPOLOGIAS_ALTO_ESCRUTINIO:
        alertas.append(f"ALERTA: Tipología de alto escrutinio SAT")
    
    if confianza == "BAJA":
        requiere_validacion = True
        alertas.append("Confianza de clasificación BAJA - requiere validación manual")
    
    if monto >= 5000000:
        alertas.append(f"Monto alto (${monto:,}) - mayor rigor requerido")
    
    palabras_clave = palabras_detectadas.get(tipologia_asignada, [])
    
    justificacion = generar_justificacion(
        tipologia_asignada, 
        palabras_clave, 
        tipo_relacion, 
        confianza,
        monto
    )
    
    return {
        "tipologia_asignada": tipologia_asignada,
        "confianza_clasificacion": confianza,
        "justificacion": justificacion,
        "palabras_clave_detectadas": palabras_clave,
        "alertas_tipologia": alertas,
        "requiere_validacion_humana": requiere_validacion,
        "checklist_aplicable": CHECKLIST_POR_TIPOLOGIA.get(tipologia_asignada, "checklist_generico")
    }


def generar_justificacion(tipologia: str, palabras: list, tipo_relacion: str, confianza: str, monto: float) -> str:
    """Genera justificación de la clasificación"""
    base = f"Proyecto clasificado como {tipologia} con confianza {confianza}. "
    
    if palabras:
        base += f"Se detectaron las siguientes palabras clave: {', '.join(palabras)}. "
    
    if tipo_relacion != "TERCERO_INDEPENDIENTE":
        base += f"El proveedor es {tipo_relacion}, lo cual influye en la clasificación. "
    
    if monto >= 5000000:
        base += f"Monto del proyecto: ${monto:,.0f} requiere mayor rigor documental. "
    
    base += f"Se aplicará el checklist correspondiente a esta tipología."
    
    return base
