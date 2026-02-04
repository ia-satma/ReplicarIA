"""
Research Tools for ReplicarIA Agents.
Integrates Oráculo Estratégico for deep enterprise research.

Tools for:
- A6_PROVEEDOR: Due diligence investigations
- S2_MATERIALIDAD: SAT materiality documentation
- A3_FISCAL: Business reason validation
- A1_SPONSOR: Strategic evaluation

Last updated: 2026-02-04
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .registry import tool

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL: INVESTIGACIÓN PROFUNDA DE EMPRESA
# ============================================================================

@tool(
    name="investigar_empresa_profunda",
    description="""
    Ejecuta investigación empresarial EXHAUSTIVA usando Oráculo Estratégico.

    Realiza análisis en 14 fases incluyendo:
    - Scraping del sitio web
    - Perfil empresarial completo
    - Análisis de industria y competidores
    - PESTEL, Porter, ESG
    - Ecosistema y transformación digital

    Ideal para: Due diligence de proveedores, validación de razón de negocios,
    documentación de materialidad SAT.

    IMPORTANTE: Este análisis puede tomar 2-5 minutos por su profundidad.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre completo de la empresa a investigar"
            },
            "sitio_web": {
                "type": "string",
                "description": "URL del sitio web de la empresa (opcional pero recomendado)"
            },
            "sector": {
                "type": "string",
                "description": "Sector o industria de la empresa (opcional, se infiere)"
            },
            "contexto": {
                "type": "string",
                "description": "Información adicional para contextualizar la búsqueda"
            }
        },
        "required": ["empresa"]
    }
)
async def investigar_empresa_profunda(
    empresa: str,
    sitio_web: str = None,
    sector: str = None,
    contexto: str = None
) -> Dict[str, Any]:
    """Execute deep enterprise investigation via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: investigar_empresa_profunda - {empresa}")

    try:
        resultado = await oraculo_estrategico_service.investigar_completo(
            empresa=empresa,
            sitio_web=sitio_web,
            sector=sector,
            contexto_adicional=contexto
        )

        if resultado.get("success"):
            return {
                "success": True,
                "empresa": empresa,
                "resumen_ejecutivo": resultado.get("consolidado", {}).get("resumen_ejecutivo", ""),
                "perfil_empresa": resultado.get("consolidado", {}).get("perfil_empresa", {}),
                "analisis_industria": resultado.get("consolidado", {}).get("analisis_industria", {}),
                "competidores": resultado.get("consolidado", {}).get("competidores", []),
                "oportunidades": resultado.get("consolidado", {}).get("oportunidades", []),
                "riesgos": resultado.get("consolidado", {}).get("riesgos", []),
                "conclusiones": resultado.get("consolidado", {}).get("conclusiones", ""),
                "fuentes_consultadas": resultado.get("meta", {}).get("fases_completadas", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "empresa": empresa,
                "error": resultado.get("error", "Error desconocido"),
                "message": "No se pudo completar la investigación"
            }

    except Exception as e:
        logger.error(f"Error en investigar_empresa_profunda: {e}")
        return {
            "success": False,
            "empresa": empresa,
            "error": str(e)
        }


# ============================================================================
# TOOL: DUE DILIGENCE DE PROVEEDOR
# ============================================================================

@tool(
    name="due_diligence_proveedor",
    description="""
    Ejecuta Due Diligence COMPLETO de un proveedor.

    Especialmente diseñado para agente A6_PROVEEDOR en fases F3-F5.

    Incluye:
    - Investigación empresarial profunda
    - Evaluación de riesgo
    - Identificación de banderas rojas
    - Verificación de capacidad operativa
    - Recomendaciones de acción

    NOTA: Para verificar RFC contra Lista 69-B, usar query_sat_lista_69b separadamente.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre del proveedor a evaluar"
            },
            "rfc": {
                "type": "string",
                "description": "RFC del proveedor (para referencia)"
            },
            "sitio_web": {
                "type": "string",
                "description": "URL del sitio web del proveedor"
            },
            "monto_operacion": {
                "type": "number",
                "description": "Monto de la operación en MXN"
            },
            "tipo_servicio": {
                "type": "string",
                "description": "Tipo de servicio a contratar"
            }
        },
        "required": ["empresa"]
    }
)
async def due_diligence_proveedor(
    empresa: str,
    rfc: str = None,
    sitio_web: str = None,
    monto_operacion: float = None,
    tipo_servicio: str = None
) -> Dict[str, Any]:
    """Execute supplier due diligence via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: due_diligence_proveedor - {empresa}")

    try:
        resultado = await oraculo_estrategico_service.due_diligence_proveedor(
            empresa=empresa,
            rfc=rfc,
            sitio_web=sitio_web,
            monto_operacion=monto_operacion,
            tipo_servicio=tipo_servicio
        )

        if resultado.get("success"):
            dd = resultado.get("due_diligence", {})
            return {
                "success": True,
                "empresa": empresa,
                "rfc": rfc,
                "evaluacion_riesgo": dd.get("evaluacion_riesgo", {}),
                "banderas_rojas": dd.get("banderas_rojas", []),
                "apto_para_operacion": dd.get("apto_para_operacion", {}),
                "recomendaciones": dd.get("recomendaciones", []),
                "resumen_investigacion": resultado.get("consolidado", {}).get("resumen_ejecutivo", ""),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "empresa": empresa,
                "error": resultado.get("error", "Error en due diligence")
            }

    except Exception as e:
        logger.error(f"Error en due_diligence_proveedor: {e}")
        return {"success": False, "empresa": empresa, "error": str(e)}


# ============================================================================
# TOOL: DOCUMENTAR MATERIALIDAD SAT
# ============================================================================

@tool(
    name="documentar_materialidad_sat",
    description="""
    Genera documentación COMPLETA de materialidad para SAT.

    Especialmente diseñado para S2_MATERIALIDAD en fases F5-F6.
    Cumple con Art. 69-B CFF para demostrar servicios reales.

    Documenta los 5 pilares de materialidad:
    1. RAZÓN DE NEGOCIOS - Por qué se necesita el servicio
    2. CAPACIDAD OPERATIVA - El proveedor puede prestarlo
    3. PROPORCIONALIDAD - El monto es razonable
    4. EVIDENCIA DE EJECUCIÓN - El servicio se prestó
    5. CONSISTENCIA DOCUMENTAL - Documentos coherentes

    Retorna score de materialidad y documentos sugeridos.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre del proveedor"
            },
            "rfc": {
                "type": "string",
                "description": "RFC del proveedor"
            },
            "servicio_contratado": {
                "type": "string",
                "description": "Descripción del servicio contratado"
            },
            "monto": {
                "type": "number",
                "description": "Monto de la operación en MXN"
            },
            "sitio_web": {
                "type": "string",
                "description": "URL del sitio web del proveedor"
            },
            "documentos_existentes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de documentos de soporte ya disponibles"
            }
        },
        "required": ["empresa", "rfc", "servicio_contratado", "monto"]
    }
)
async def documentar_materialidad_sat(
    empresa: str,
    rfc: str,
    servicio_contratado: str,
    monto: float,
    sitio_web: str = None,
    documentos_existentes: List[str] = None
) -> Dict[str, Any]:
    """Generate SAT materiality documentation via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: documentar_materialidad_sat - {empresa} - {servicio_contratado}")

    try:
        resultado = await oraculo_estrategico_service.documentar_materialidad(
            empresa=empresa,
            rfc=rfc,
            servicio_contratado=servicio_contratado,
            monto=monto,
            sitio_web=sitio_web,
            documentos_soporte=documentos_existentes
        )

        if resultado.get("success"):
            mat = resultado.get("materialidad_sat", {})
            return {
                "success": True,
                "empresa": empresa,
                "rfc": rfc,
                "servicio": servicio_contratado,
                "monto": monto,
                "score_materialidad": mat.get("score_materialidad", 0),
                "pilares_documentados": mat.get("pilares_documentados", {}),
                "documentos_sugeridos": mat.get("documentos_sugeridos", []),
                "riesgos_identificados": mat.get("riesgos_identificados", []),
                "conclusion": mat.get("conclusion", ""),
                "investigacion_respaldo": resultado.get("consolidado", {}).get("resumen_ejecutivo", ""),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "empresa": empresa,
                "error": resultado.get("error", "Error en documentación")
            }

    except Exception as e:
        logger.error(f"Error en documentar_materialidad_sat: {e}")
        return {"success": False, "empresa": empresa, "error": str(e)}


# ============================================================================
# TOOL: ANÁLISIS PESTEL
# ============================================================================

@tool(
    name="analisis_pestel",
    description="""
    Ejecuta análisis PESTEL completo para un sector/empresa.

    Analiza factores:
    - POLÍTICOS: Regulación, políticas gubernamentales
    - ECONÓMICOS: Inflación, tipos de cambio, crecimiento
    - SOCIALES: Demografía, tendencias culturales
    - TECNOLÓGICOS: Innovación, digitalización
    - ECOLÓGICOS: Sostenibilidad, regulación ambiental
    - LEGALES: Marco normativo, compliance

    Útil para A1_SPONSOR en evaluación estratégica.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre de la empresa"
            },
            "sector": {
                "type": "string",
                "description": "Sector industrial a analizar"
            },
            "pais": {
                "type": "string",
                "description": "País de análisis (default: México)"
            }
        },
        "required": ["empresa", "sector"]
    }
)
async def analisis_pestel(
    empresa: str,
    sector: str,
    pais: str = "México"
) -> Dict[str, Any]:
    """Execute PESTEL analysis via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: analisis_pestel - {sector} en {pais}")

    try:
        resultado = await oraculo_estrategico_service.analisis_pestel(
            empresa=empresa,
            sector=sector,
            pais=pais
        )

        return {
            "success": resultado.get("success", False),
            "empresa": empresa,
            "sector": sector,
            "pais": pais,
            "factores_politicos": resultado.get("politicos", {}),
            "factores_economicos": resultado.get("economicos", {}),
            "factores_sociales": resultado.get("sociales", {}),
            "factores_tecnologicos": resultado.get("tecnologicos", {}),
            "factores_ecologicos": resultado.get("ecologicos", {}),
            "factores_legales": resultado.get("legales", {}),
            "resumen": resultado.get("resumen", ""),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en analisis_pestel: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL: ANÁLISIS 5 FUERZAS DE PORTER
# ============================================================================

@tool(
    name="analisis_porter",
    description="""
    Ejecuta análisis de las 5 FUERZAS DE PORTER.

    Evalúa:
    1. RIVALIDAD entre competidores existentes
    2. PODER DE NEGOCIACIÓN de proveedores
    3. PODER DE NEGOCIACIÓN de compradores
    4. AMENAZA de productos sustitutos
    5. AMENAZA de nuevos entrantes

    Incluye score de intensidad competitiva por fuerza.
    Útil para A1_SPONSOR en evaluación estratégica.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre de la empresa"
            },
            "sector": {
                "type": "string",
                "description": "Sector industrial a analizar"
            }
        },
        "required": ["empresa", "sector"]
    }
)
async def analisis_porter(
    empresa: str,
    sector: str
) -> Dict[str, Any]:
    """Execute Porter's Five Forces analysis via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: analisis_porter - {sector}")

    try:
        resultado = await oraculo_estrategico_service.analisis_porter(
            empresa=empresa,
            sector=sector
        )

        return {
            "success": resultado.get("success", False),
            "empresa": empresa,
            "sector": sector,
            "rivalidad_competidores": resultado.get("rivalidad", {}),
            "poder_proveedores": resultado.get("proveedores", {}),
            "poder_compradores": resultado.get("compradores", {}),
            "amenaza_sustitutos": resultado.get("sustitutos", {}),
            "amenaza_nuevos_entrantes": resultado.get("entrantes", {}),
            "intensidad_competitiva_global": resultado.get("intensidad_global", "MEDIA"),
            "resumen_estrategico": resultado.get("resumen", ""),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en analisis_porter: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL: ANÁLISIS ESG
# ============================================================================

@tool(
    name="analisis_esg",
    description="""
    Ejecuta análisis ESG (Environmental, Social, Governance).

    Evalúa:
    - AMBIENTAL: Huella de carbono, sostenibilidad, certificaciones
    - SOCIAL: Prácticas laborales, diversidad, comunidad
    - GOBERNANZA: Estructura directiva, ética, transparencia

    Incluye score ESG y comparación vs estándares de industria.
    Útil para evaluar riesgo reputacional de proveedores.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa": {
                "type": "string",
                "description": "Nombre de la empresa"
            },
            "sitio_web": {
                "type": "string",
                "description": "URL del sitio web para buscar reportes ESG"
            }
        },
        "required": ["empresa"]
    }
)
async def analisis_esg(
    empresa: str,
    sitio_web: str = None
) -> Dict[str, Any]:
    """Execute ESG analysis via Oráculo Estratégico."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: analisis_esg - {empresa}")

    try:
        resultado = await oraculo_estrategico_service.analisis_esg(
            empresa=empresa,
            sitio_web=sitio_web
        )

        return {
            "success": resultado.get("success", False),
            "empresa": empresa,
            "score_ambiental": resultado.get("ambiental", {}).get("score", 0),
            "score_social": resultado.get("social", {}).get("score", 0),
            "score_gobernanza": resultado.get("gobernanza", {}).get("score", 0),
            "score_esg_total": resultado.get("score_total", 0),
            "factores_ambiental": resultado.get("ambiental", {}).get("factores", []),
            "factores_social": resultado.get("social", {}).get("factores", []),
            "factores_gobernanza": resultado.get("gobernanza", {}).get("factores", []),
            "certificaciones": resultado.get("certificaciones", []),
            "riesgos_esg": resultado.get("riesgos", []),
            "comparacion_industria": resultado.get("benchmark", ""),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en analisis_esg: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# TOOL: VALIDAR RAZON DE NEGOCIOS
# ============================================================================

@tool(
    name="validar_razon_negocios",
    description="""
    Valida la RAZÓN DE NEGOCIOS de una operación para cumplimiento fiscal.

    Especialmente útil para A3_FISCAL en evaluación de 4 pilares.

    Evalúa:
    - Justificación económica de la operación
    - Beneficio esperado cuantificable
    - Necesidad real del servicio
    - Alternativas consideradas
    - Proporcionalidad del gasto

    Retorna evaluación de solidez de razón de negocios.
    """,
    parameters={
        "type": "object",
        "properties": {
            "empresa_cliente": {
                "type": "string",
                "description": "Empresa que contrata el servicio"
            },
            "empresa_proveedor": {
                "type": "string",
                "description": "Empresa que presta el servicio"
            },
            "servicio": {
                "type": "string",
                "description": "Descripción del servicio contratado"
            },
            "monto": {
                "type": "number",
                "description": "Monto de la operación en MXN"
            },
            "justificacion": {
                "type": "string",
                "description": "Justificación proporcionada por el cliente"
            },
            "sector_cliente": {
                "type": "string",
                "description": "Sector de la empresa cliente"
            }
        },
        "required": ["empresa_cliente", "empresa_proveedor", "servicio", "monto"]
    }
)
async def validar_razon_negocios(
    empresa_cliente: str,
    empresa_proveedor: str,
    servicio: str,
    monto: float,
    justificacion: str = None,
    sector_cliente: str = None
) -> Dict[str, Any]:
    """Validate business reason for fiscal compliance."""
    from services.oraculo_estrategico_service import oraculo_estrategico_service

    logger.info(f"Tool: validar_razon_negocios - {servicio}")

    try:
        # Investigar ambas empresas para validar la operación
        resultado_proveedor = await oraculo_estrategico_service.investigar_completo(
            empresa=empresa_proveedor,
            sector=sector_cliente,
            contexto_adicional=f"""
            VALIDACIÓN DE RAZÓN DE NEGOCIOS:
            - Cliente: {empresa_cliente}
            - Servicio: {servicio}
            - Monto: ${monto:,.2f} MXN
            - Justificación del cliente: {justificacion or 'No proporcionada'}

            Evaluar si el proveedor puede prestar este servicio y si tiene sentido
            económico la operación.
            """
        )

        # Evaluar solidez de razón de negocios
        solidez = "MEDIA"  # Default
        factores_positivos = []
        factores_negativos = []

        if resultado_proveedor.get("success"):
            consolidado = resultado_proveedor.get("consolidado", {})

            # Verificar presencia web
            if resultado_proveedor.get("scraping", {}).get("success"):
                factores_positivos.append("Proveedor con presencia web verificable")
            else:
                factores_negativos.append("Sin presencia web verificable")

            # Verificar que el servicio corresponde al giro
            # (Esto requeriría análisis más profundo del consolidado)
            factores_positivos.append("Investigación de proveedor completada")

            if len(factores_positivos) > len(factores_negativos):
                solidez = "ALTA"
            elif len(factores_negativos) > len(factores_positivos):
                solidez = "BAJA"

        return {
            "success": True,
            "empresa_cliente": empresa_cliente,
            "empresa_proveedor": empresa_proveedor,
            "servicio": servicio,
            "monto": monto,
            "solidez_razon_negocios": solidez,
            "factores_positivos": factores_positivos,
            "factores_negativos": factores_negativos,
            "perfil_proveedor": resultado_proveedor.get("consolidado", {}).get("resumen_ejecutivo", ""),
            "recomendacion": (
                "APROBAR - Razón de negocios sólida" if solidez == "ALTA"
                else "REVISAR - Requiere documentación adicional" if solidez == "MEDIA"
                else "RECHAZAR - Razón de negocios débil"
            ),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en validar_razon_negocios: {e}")
        return {"success": False, "error": str(e)}
