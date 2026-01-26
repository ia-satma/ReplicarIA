"""
Configuración de documentos requeridos por cada agente (A1-A7)
para el módulo Estado del Acervo de Bibliotecar.IA
"""
from typing import List, Dict, Any

ACERVO_REQUERIDO: Dict[str, Dict[str, Any]] = {
    "A1": {
        "id": "A1",
        "nombre": "Razón de Negocios",
        "icono": "⚖️",
        "descripcion": "Agente especializado en validar la razón de negocios y sustancia económica",
        "documentos": [
            {
                "id": "a1_cff_5a",
                "nombre": "CFF Art. 5-A - Razón de Negocios",
                "descripcion": "Código Fiscal de la Federación, artículo 5-A sobre razón de negocios",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["CFF", "CFF_5A", "cff", "codigo_fiscal"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
                "instrucciones": "Descargar versión vigente del CFF completo desde el sitio de la Cámara de Diputados"
            },
            {
                "id": "a1_jurisprudencias_razon",
                "nombre": "Jurisprudencias Razón de Negocios",
                "descripcion": "Tesis y jurisprudencias de SCJN sobre razón de negocios",
                "categoria": "jurisprudencias",
                "criticidad": "critico",
                "codigos_aceptados": ["JURIS_RAZON", "razon_negocios", "scjn_razon", "tesis_razon"],
                "instrucciones": "Compilar jurisprudencias relevantes de la SCJN sobre razón de negocios y sustancia económica"
            },
            {
                "id": "a1_criterios_simulacion",
                "nombre": "Criterios SAT sobre simulación",
                "descripcion": "Criterios del SAT respecto a actos simulados y operaciones inexistentes",
                "categoria": "criterios_sat",
                "criticidad": "importante",
                "codigos_aceptados": ["CRIT_SIM", "criterios_simulacion", "sat_simulacion"],
                "url_descarga": "http://omawww.sat.gob.mx/fichas_tematicas/reforma_fiscal/Paginas/criterios_normativos.aspx"
            },
            {
                "id": "a1_tesis_materialidad",
                "nombre": "Tesis SCJN - Materialidad",
                "descripcion": "Tesis de la Suprema Corte sobre materialidad de operaciones",
                "categoria": "jurisprudencias",
                "criticidad": "importante",
                "codigos_aceptados": ["TESIS_MAT", "scjn_materialidad", "materialidad_scjn"],
                "instrucciones": "Incluir tesis relevantes sobre la carga de prueba de materialidad"
            },
            {
                "id": "a1_guia_sustancia",
                "nombre": "Guía de Sustancia Económica",
                "descripcion": "Guía práctica para demostrar sustancia económica en operaciones",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["GUIA_SUST", "sustancia_economica", "guia_bee"],
                "instrucciones": "Documento interno con mejores prácticas para documentar sustancia económica"
            }
        ]
    },
    "A2": {
        "id": "A2",
        "nombre": "Materialidad y Sustancia",
        "icono": "📋",
        "descripcion": "Agente de comprobantes fiscales y evidencia documental",
        "documentos": [
            {
                "id": "a2_cff_comprobantes",
                "nombre": "CFF - Comprobantes Fiscales",
                "descripcion": "Artículos del CFF relacionados con comprobantes fiscales digitales",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["CFF_CFDI", "cff_comprobantes", "CFF"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf"
            },
            {
                "id": "a2_rmf_cfdi",
                "nombre": "RMF - Reglas CFDI",
                "descripcion": "Reglas de la Miscelánea Fiscal relacionadas con CFDI",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["RMF", "rmf_cfdi", "RMF_2025", "RMF_2024", "miscelanea"],
                "url_descarga": "https://www.sat.gob.mx/normatividad/23481/resolucion-miscelanea-fiscal"
            },
            {
                "id": "a2_guia_llenado",
                "nombre": "Guía de Llenado CFDI 4.0",
                "descripcion": "Guía oficial del SAT para llenado de CFDI versión 4.0",
                "categoria": "guias",
                "criticidad": "importante",
                "codigos_aceptados": ["GUIA_CFDI", "guia_llenado", "cfdi_4", "cfdi40"],
                "url_descarga": "https://www.sat.gob.mx/consultas/35025/anexo-20-guia-de-llenado-de-los-comprobantes-fiscales-digitales-por-internet"
            },
            {
                "id": "a2_catalogo_claveprodserv",
                "nombre": "Catálogo c_ClaveProdServ",
                "descripcion": "Catálogo de claves de productos y servicios del SAT",
                "categoria": "catalogos",
                "criticidad": "importante",
                "codigos_aceptados": ["c_ClaveProdServ", "catalogo_clave", "clave_sat"],
                "url_descarga": "http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20_version3-3.htm"
            },
            {
                "id": "a2_nom151",
                "nombre": "NOM-151 - Conservación de documentos",
                "descripcion": "Norma oficial para conservación de mensajes de datos y documentos electrónicos",
                "categoria": "marco_legal",
                "criticidad": "recomendado",
                "codigos_aceptados": ["NOM151", "nom_151", "conservacion_docs"],
                "instrucciones": "NOM para asegurar integridad y trazabilidad de documentos digitales"
            }
        ]
    },
    "A3": {
        "id": "A3",
        "nombre": "Deducciones Autorizadas",
        "icono": "📊",
        "descripcion": "Agente fiscal especializado en deducciones y cumplimiento tributario",
        "documentos": [
            {
                "id": "a3_lisr",
                "nombre": "LISR - Ley del ISR",
                "descripcion": "Ley del Impuesto sobre la Renta completa",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["LISR", "lisr", "ley_isr", "isr"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf"
            },
            {
                "id": "a3_rlisr",
                "nombre": "Reglamento LISR",
                "descripcion": "Reglamento de la Ley del Impuesto sobre la Renta",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["RLISR", "rlisr", "reglamento_isr", "reg_lisr"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LISR.pdf"
            },
            {
                "id": "a3_rmf_deducciones",
                "nombre": "RMF - Reglas de Deducciones",
                "descripcion": "Sección de la RMF sobre deducciones autorizadas",
                "categoria": "marco_legal",
                "criticidad": "importante",
                "codigos_aceptados": ["RMF_DED", "rmf_deducciones", "miscelanea_ded"],
                "url_descarga": "https://www.sat.gob.mx/normatividad/23481/resolucion-miscelanea-fiscal"
            },
            {
                "id": "a3_jurisprudencias_ded",
                "nombre": "Jurisprudencias Deducciones",
                "descripcion": "Compilación de jurisprudencias sobre deducciones fiscales",
                "categoria": "jurisprudencias",
                "criticidad": "importante",
                "codigos_aceptados": ["JURIS_DED", "jurisprudencias_deducciones", "tesis_ded"],
                "instrucciones": "Incluir tesis relevantes sobre estricta indispensabilidad y requisitos de deducciones"
            },
            {
                "id": "a3_criterios_no_vinculativos",
                "nombre": "Criterios No Vinculativos",
                "descripcion": "Criterios no vinculativos del SAT sobre prácticas indebidas",
                "categoria": "criterios_sat",
                "criticidad": "importante",
                "codigos_aceptados": ["CNV", "no_vinculativos", "criterios_nv"],
                "url_descarga": "http://omawww.sat.gob.mx/fichas_tematicas/reforma_fiscal/Paginas/criterios_no_vinculativos.aspx"
            },
            {
                "id": "a3_lisr_27",
                "nombre": "LISR Art. 27 - Requisitos Deducciones",
                "descripcion": "Artículo 27 de la LISR sobre requisitos de deducciones",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["LISR_27", "art27", "requisitos_ded"],
                "instrucciones": "Extracto específico del artículo 27 con análisis detallado"
            }
        ]
    },
    "A4": {
        "id": "A4",
        "nombre": "Obligaciones Formales",
        "icono": "📝",
        "descripcion": "Agente legal para contratos y obligaciones formales",
        "documentos": [
            {
                "id": "a4_cff_obligaciones",
                "nombre": "CFF - Obligaciones Fiscales",
                "descripcion": "Código Fiscal de la Federación - Título sobre obligaciones",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["CFF_OBL", "cff_obligaciones", "CFF"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf"
            },
            {
                "id": "a4_rcff",
                "nombre": "Reglamento CFF",
                "descripcion": "Reglamento del Código Fiscal de la Federación",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["RCFF", "rcff", "reglamento_cff"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_CFF.pdf"
            },
            {
                "id": "a4_calendario_fiscal",
                "nombre": "Calendario Fiscal 2025",
                "descripcion": "Calendario de obligaciones fiscales del ejercicio",
                "categoria": "guias",
                "criticidad": "importante",
                "codigos_aceptados": ["CAL_2025", "calendario_fiscal", "fechas_sat"],
                "url_descarga": "https://www.sat.gob.mx/home"
            },
            {
                "id": "a4_plantillas_contratos",
                "nombre": "Plantillas de Contratos",
                "descripcion": "Modelos de contratos con cláusulas fiscales requeridas",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["CONTRATOS", "plantillas_contrato", "modelos_legales"],
                "instrucciones": "Plantillas internas con cláusulas de materialidad y trazabilidad"
            },
            {
                "id": "a4_guia_nom151",
                "nombre": "Guía NOM-151 Digitalización",
                "descripcion": "Guía práctica para digitalización conforme a NOM-151",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["GUIA_NOM151", "digitalizacion", "archivo_digital"],
                "instrucciones": "Procedimientos para archivo y conservación digital de documentos"
            }
        ]
    },
    "A5": {
        "id": "A5",
        "nombre": "Intangibles y Regalías",
        "icono": "💰",
        "descripcion": "Agente financiero para inversiones, intangibles y precios de transferencia",
        "documentos": [
            {
                "id": "a5_lisr_inversiones",
                "nombre": "LISR - Inversiones e Intangibles",
                "descripcion": "Artículos de la LISR sobre deducciones de inversiones",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["LISR_INV", "lisr_inversiones", "inversiones_isr"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf"
            },
            {
                "id": "a5_precios_transferencia",
                "nombre": "Precios de Transferencia",
                "descripcion": "Marco normativo de precios de transferencia en México",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["PT", "precios_transferencia", "transfer_pricing"],
                "instrucciones": "Incluir artículos de LISR y lineamientos aplicables"
            },
            {
                "id": "a5_guias_ocde",
                "nombre": "Guías OCDE Precios Transferencia",
                "descripcion": "Directrices de la OCDE sobre precios de transferencia",
                "categoria": "guias",
                "criticidad": "importante",
                "codigos_aceptados": ["OCDE_PT", "guias_ocde", "oecd_tp"],
                "url_descarga": "https://www.oecd.org/tax/transfer-pricing/"
            },
            {
                "id": "a5_regalias",
                "nombre": "Tratamiento Fiscal Regalías",
                "descripcion": "Marco fiscal para regalías y asistencia técnica",
                "categoria": "marco_legal",
                "criticidad": "importante",
                "codigos_aceptados": ["REGALIAS", "royalties", "asistencia_tecnica"],
                "instrucciones": "Compilar artículos de LISR y tratados sobre regalías"
            },
            {
                "id": "a5_benchmarks",
                "nombre": "Benchmarks Financieros",
                "descripcion": "Referencias de mercado para análisis financiero",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["BENCH", "benchmarks", "referencias_mercado"],
                "instrucciones": "Bases de datos y fuentes para comparables de mercado"
            }
        ]
    },
    "A6": {
        "id": "A6",
        "nombre": "Verificación EFOS",
        "icono": "🔍",
        "descripcion": "Agente de verificación de proveedores y lista 69-B",
        "documentos": [
            {
                "id": "a6_lista_69b",
                "nombre": "Lista 69-B Actualizada",
                "descripcion": "Lista de contribuyentes con operaciones inexistentes (EFOS)",
                "categoria": "catalogos",
                "criticidad": "critico",
                "codigos_aceptados": ["LISTA_69B", "69b", "efos", "lista_negra"],
                "url_descarga": "http://omawww.sat.gob.mx/cifras_sat/Paginas/datos/vinculo.html?page=ListCompl662702.html"
            },
            {
                "id": "a6_art_69b",
                "nombre": "CFF Art. 69-B",
                "descripcion": "Artículo 69-B del CFF sobre operaciones simuladas",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["CFF_69B", "art_69b", "69-B"],
                "url_descarga": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf"
            },
            {
                "id": "a6_procedimiento_69b",
                "nombre": "Procedimiento Art. 69-B",
                "descripcion": "Guía del procedimiento de defensa ante 69-B",
                "categoria": "guias",
                "criticidad": "importante",
                "codigos_aceptados": ["PROC_69B", "procedimiento_efos", "defensa_69b"],
                "instrucciones": "Protocolo interno para responder ante notificaciones 69-B"
            },
            {
                "id": "a6_criterios_efos",
                "nombre": "Criterios Identificación EFOS",
                "descripcion": "Criterios para identificar posibles EFOS",
                "categoria": "criterios_sat",
                "criticidad": "importante",
                "codigos_aceptados": ["CRIT_EFOS", "criterios_efos", "red_flags"],
                "instrucciones": "Indicadores de riesgo y señales de alerta para proveedores"
            },
            {
                "id": "a6_due_diligence",
                "nombre": "Checklist Due Diligence",
                "descripcion": "Lista de verificación para evaluación de proveedores",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["DD_CHECK", "due_diligence", "verificacion_proveedor"],
                "instrucciones": "Checklist interno para onboarding de proveedores"
            }
        ]
    },
    "A7": {
        "id": "A7",
        "nombre": "Defensa Fiscal",
        "icono": "🛡️",
        "descripcion": "Agente integrador para expediente de defensa fiscal",
        "documentos": [
            {
                "id": "a7_todos_anteriores",
                "nombre": "Acervo Completo A1-A6",
                "descripcion": "Requiere todos los documentos de agentes A1 a A6",
                "categoria": "marco_legal",
                "criticidad": "critico",
                "codigos_aceptados": ["COMPLETO", "full_kb", "acervo_total"],
                "instrucciones": "A7 requiere que A1-A6 tengan sus documentos críticos cargados"
            },
            {
                "id": "a7_precedentes_tfja",
                "nombre": "Precedentes TFJA",
                "descripcion": "Jurisprudencias del Tribunal Federal de Justicia Administrativa",
                "categoria": "jurisprudencias",
                "criticidad": "critico",
                "codigos_aceptados": ["TFJA", "precedentes_tfja", "tribunal_fiscal"],
                "instrucciones": "Compilar precedentes relevantes para defensa fiscal"
            },
            {
                "id": "a7_prodecon",
                "nombre": "Criterios PRODECON",
                "descripcion": "Criterios y recomendaciones de la PRODECON",
                "categoria": "criterios_sat",
                "criticidad": "importante",
                "codigos_aceptados": ["PRODECON", "prodecon", "ombudsman_fiscal"],
                "url_descarga": "https://www.prodecon.gob.mx/"
            },
            {
                "id": "a7_guia_defense_file",
                "nombre": "Guía Expediente de Defensa",
                "descripcion": "Manual para construcción del expediente de defensa",
                "categoria": "guias",
                "criticidad": "critico",
                "codigos_aceptados": ["GUIA_DEF", "defense_file", "expediente_defensa"],
                "instrucciones": "Protocolo interno para estructurar expediente probatorio"
            },
            {
                "id": "a7_casos_exitosos",
                "nombre": "Casos Exitosos de Referencia",
                "descripcion": "Casos de defensa fiscal ganados como referencia",
                "categoria": "guias",
                "criticidad": "recomendado",
                "codigos_aceptados": ["CASOS_REF", "casos_exitosos", "precedentes_internos"],
                "instrucciones": "Documentar casos previos exitosos para uso como referencia"
            }
        ]
    }
}


def get_acervo_requerido() -> Dict[str, Dict[str, Any]]:
    """Retorna la configuración completa del acervo requerido."""
    return ACERVO_REQUERIDO


def get_documentos_por_agente(agente_id: str) -> List[Dict[str, Any]]:
    """Retorna la lista de documentos requeridos para un agente específico."""
    agente = ACERVO_REQUERIDO.get(agente_id)
    if agente:
        return agente.get("documentos", [])
    return []


def get_todos_los_documentos() -> List[Dict[str, Any]]:
    """Retorna todos los documentos requeridos de todos los agentes."""
    todos = []
    for agente_id, agente in ACERVO_REQUERIDO.items():
        for doc in agente.get("documentos", []):
            doc_copy = doc.copy()
            doc_copy["agente_id"] = agente_id
            doc_copy["agente_nombre"] = agente.get("nombre", agente_id)
            todos.append(doc_copy)
    return todos


def get_codigos_aceptados_map() -> Dict[str, Dict[str, Any]]:
    """
    Retorna un diccionario que mapea códigos aceptados a su documento y agente.
    Útil para verificar si un documento cargado satisface algún requerimiento.
    """
    mapa = {}
    for agente_id, agente in ACERVO_REQUERIDO.items():
        for doc in agente.get("documentos", []):
            for codigo in doc.get("codigos_aceptados", []):
                codigo_lower = codigo.lower()
                mapa[codigo_lower] = {
                    "documento_id": doc["id"],
                    "documento_nombre": doc["nombre"],
                    "agente_id": agente_id,
                    "agente_nombre": agente.get("nombre"),
                    "criticidad": doc.get("criticidad", "recomendado")
                }
    return mapa
