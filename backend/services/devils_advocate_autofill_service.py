"""
Devils Advocate Auto-Fill Service
Automatically populates the 25 Devil's Advocate questions from agent outputs
The PMO uses this to consolidate agent evaluations into a structured questionnaire.

This service integrates with the PMO Subagent Orchestrator to leverage parallel
processing capabilities for analyzing, classifying, and summarizing agent outputs.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Import PMO subagent orchestrator for enhanced processing
try:
    from services.pmo_subagent_orchestrator import get_pmo_subagent_orchestrator
    PMO_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    PMO_ORCHESTRATOR_AVAILABLE = False
    logger.warning("PMO Subagent Orchestrator not available - using basic mode")


class FuenteRespuesta(str, Enum):
    """Source of the auto-filled response"""
    A1_SPONSOR = "A1_SPONSOR"       # Strategic validation
    A3_FISCAL = "A3_FISCAL"          # Fiscal compliance
    A4_CONTABLE = "A4_CONTABLE"      # Accounting/document matching
    A5_FINANZAS = "A5_FINANZAS"      # Financial analysis
    A6_DD_PROVEEDOR = "A6_DD_PROVEEDOR"  # Provider due diligence
    A7_DEFENSA = "A7_DEFENSA"        # Legal defense
    A8_AUDITOR = "A8_AUDITOR"        # Internal audit/red team
    PMO_CONSOLIDADO = "PMO_CONSOLIDADO"  # PMO's own consolidation
    MANUAL = "MANUAL"                 # Requires manual input


@dataclass
class RespuestaAutoFill:
    """Auto-filled response from agent outputs"""
    pregunta_id: str
    respuesta: str
    confianza: float  # 0.0 - 1.0
    fuente: FuenteRespuesta
    datos_soporte: List[str] = field(default_factory=list)
    requiere_revision: bool = False
    notas: str = ""
    indice_opcion: Optional[int] = None  # For selection/scale questions


# Mapping of questions to their primary agent sources
PREGUNTA_FUENTE_MAPPING = {
    # Block 1: Hechos y Objeto del Servicio
    "P01_DESCRIPCION_SERVICIO": {
        "fuentes_primarias": [FuenteRespuesta.A1_SPONSOR],
        "campos_agente": ["analysis", "service_description"],
        "fuentes_secundarias": [FuenteRespuesta.A7_DEFENSA]
    },
    "P02_ENTREGABLE_CONCRETO": {
        "fuentes_primarias": [FuenteRespuesta.A5_FINANZAS, FuenteRespuesta.A8_AUDITOR],
        "campos_agente": ["deliverables", "findings"],
        "fuentes_secundarias": [FuenteRespuesta.A1_SPONSOR]
    },
    "P03_EVIDENCIA_EJECUCION": {
        "fuentes_primarias": [FuenteRespuesta.A6_DD_PROVEEDOR, FuenteRespuesta.A8_AUDITOR],
        "campos_agente": ["execution_evidence", "timeline_analysis"],
        "fuentes_secundarias": [FuenteRespuesta.A7_DEFENSA]
    },
    "P04_TESTIGO_INDEPENDIENTE": {
        "fuentes_primarias": [FuenteRespuesta.A7_DEFENSA],
        "campos_agente": ["third_party_evidence", "external_validation"],
        "fuentes_secundarias": [FuenteRespuesta.A8_AUDITOR]
    },

    # Block 2: Materialidad / CFF 69-B
    "P05_CAPACIDAD_PROVEEDOR": {
        "fuentes_primarias": [FuenteRespuesta.A6_DD_PROVEEDOR],
        "campos_agente": ["provider_capacity", "infrastructure_check"],
        "fuentes_secundarias": [FuenteRespuesta.A1_SPONSOR]
    },
    "P06_DOMICILIO_VERIFICABLE": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL, FuenteRespuesta.A6_DD_PROVEEDOR],
        "campos_agente": ["domicilio_fiscal", "sat_verification"],
        "fuentes_secundarias": []
    },
    "P07_RASTRO_DIGITAL": {
        "fuentes_primarias": [FuenteRespuesta.A6_DD_PROVEEDOR, FuenteRespuesta.A8_AUDITOR],
        "campos_agente": ["digital_trace", "email_evidence", "platform_logs"],
        "fuentes_secundarias": []
    },
    "P08_FABRICACION_POSTERIOR": {
        "fuentes_primarias": [FuenteRespuesta.A8_AUDITOR, FuenteRespuesta.A7_DEFENSA],
        "campos_agente": ["document_forensics", "timestamp_validation"],
        "fuentes_secundarias": []
    },

    # Block 3: Razon de Negocios / CFF 5-A
    "P09_BENEFICIO_SIN_FISCAL": {
        "fuentes_primarias": [FuenteRespuesta.A1_SPONSOR],
        "campos_agente": ["economic_benefit", "non_tax_roi", "business_value"],
        "fuentes_secundarias": [FuenteRespuesta.A5_FINANZAS]
    },
    "P10_ALTERNATIVA_INTERNA": {
        "fuentes_primarias": [FuenteRespuesta.A1_SPONSOR],
        "campos_agente": ["make_vs_buy", "internal_capacity_analysis"],
        "fuentes_secundarias": []
    },
    "P11_PRECIO_MERCADO": {
        "fuentes_primarias": [FuenteRespuesta.A5_FINANZAS],
        "campos_agente": ["price_benchmark", "market_comparison"],
        "fuentes_secundarias": [FuenteRespuesta.A1_SPONSOR]
    },
    "P12_RESULTADO_MEDIBLE": {
        "fuentes_primarias": [FuenteRespuesta.A5_FINANZAS],
        "campos_agente": ["performance_metrics", "results_tracking"],
        "fuentes_secundarias": [FuenteRespuesta.A8_AUDITOR]
    },

    # Block 4: Proveedor y EFOS
    "P13_LISTA_69B": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL],
        "campos_agente": ["lista_69b_check", "sat_blacklist_status"],
        "fuentes_secundarias": [FuenteRespuesta.A6_DD_PROVEEDOR]
    },
    "P14_OPINION_32D": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL],
        "campos_agente": ["opinion_32d", "compliance_opinion"],
        "fuentes_secundarias": []
    },
    "P15_HISTORIAL_PROVEEDOR": {
        "fuentes_primarias": [FuenteRespuesta.A6_DD_PROVEEDOR],
        "campos_agente": ["provider_history", "client_references"],
        "fuentes_secundarias": [FuenteRespuesta.A1_SPONSOR]
    },
    "P16_EMPLEADOS_IMSS": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL, FuenteRespuesta.A6_DD_PROVEEDOR],
        "campos_agente": ["imss_verification", "employee_count"],
        "fuentes_secundarias": []
    },

    # Block 5: Requisitos Fiscales Formales
    "P17_CFDI_DETALLE": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL],
        "campos_agente": ["cfdi_analysis", "invoice_description"],
        "fuentes_secundarias": []
    },
    "P18_COINCIDENCIA_CONTRATO_CFDI": {
        "fuentes_primarias": [FuenteRespuesta.A4_CONTABLE, FuenteRespuesta.A3_FISCAL],
        "campos_agente": ["contract_cfdi_match", "document_reconciliation"],
        "fuentes_secundarias": []
    },
    "P19_PAGO_BANCARIZADO": {
        "fuentes_primarias": [FuenteRespuesta.A5_FINANZAS],
        "campos_agente": ["payment_trace", "bank_transfer_verification"],
        "fuentes_secundarias": [FuenteRespuesta.A4_CONTABLE]
    },
    "P20_CONGRUENCIA_FECHAS": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL, FuenteRespuesta.A4_CONTABLE],
        "campos_agente": ["date_sequence_validation", "timeline_check"],
        "fuentes_secundarias": [FuenteRespuesta.A8_AUDITOR]
    },
    "P21_REGIMEN_CONGRUENTE": {
        "fuentes_primarias": [FuenteRespuesta.A3_FISCAL],
        "campos_agente": ["regime_validation", "tax_regime_compatibility"],
        "fuentes_secundarias": []
    },

    # Block 6: Riesgo Residual y Lecciones
    "P22_DEBILIDAD_PRINCIPAL": {
        "fuentes_primarias": [FuenteRespuesta.A8_AUDITOR],
        "campos_agente": ["vulnerabilities", "red_team_findings", "weak_points"],
        "fuentes_secundarias": [FuenteRespuesta.PMO_CONSOLIDADO]
    },
    "P23_MITIGACION_DEBILIDAD": {
        "fuentes_primarias": [FuenteRespuesta.A8_AUDITOR, FuenteRespuesta.PMO_CONSOLIDADO],
        "campos_agente": ["mitigation_strategies", "remediation_plan"],
        "fuentes_secundarias": []
    },
    "P24_LECCION_PREVENCION": {
        "fuentes_primarias": [FuenteRespuesta.PMO_CONSOLIDADO],
        "campos_agente": ["lessons_learned", "pattern_analysis"],
        "fuentes_secundarias": [FuenteRespuesta.A8_AUDITOR]
    },
    "P25_RIESGO_ACEPTADO": {
        "fuentes_primarias": [FuenteRespuesta.PMO_CONSOLIDADO],
        "campos_agente": ["risk_acceptance", "residual_risk_level"],
        "fuentes_secundarias": [FuenteRespuesta.A8_AUDITOR]
    },
}


class DevilsAdvocateAutoFillService:
    """
    Service that automatically populates Devil's Advocate questionnaire
    from agent outputs. The PMO uses this as the "oracle" to consolidate
    all agent evaluations into structured responses.

    Features:
    - Auto-extracts responses from agent outputs (A1-A8)
    - Integrates with PMO Subagent Orchestrator for parallel processing
    - Provides confidence scoring and source tracking
    - Flags low-confidence responses for manual review
    """

    def __init__(self):
        self.min_confidence_threshold = 0.6  # Below this, flag for manual review
        self.use_pmo_orchestrator = PMO_ORCHESTRATOR_AVAILABLE
        self._pmo_orchestrator = None

    def _get_pmo_orchestrator(self):
        """Get the PMO Subagent Orchestrator instance (lazy loading)."""
        if self._pmo_orchestrator is None and self.use_pmo_orchestrator:
            self._pmo_orchestrator = get_pmo_subagent_orchestrator()
        return self._pmo_orchestrator

    def auto_fill_from_agent_outputs(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
        proyecto_data: Dict[str, Any]
    ) -> Dict[str, RespuestaAutoFill]:
        """
        Auto-populate all 25 questions from consolidated agent outputs.

        Args:
            agent_outputs: Dictionary with agent responses
                {
                    "A1_SPONSOR": {"analysis": "...", "decision": "...", "findings": [...], ...},
                    "A3_FISCAL": {"analysis": "...", "sat_check": {...}, ...},
                    ...
                }
            proyecto_data: Project metadata

        Returns:
            Dictionary of auto-filled responses by question ID
        """
        respuestas = {}

        for pregunta_id, mapping in PREGUNTA_FUENTE_MAPPING.items():
            respuesta = self._extract_response_for_question(
                pregunta_id,
                mapping,
                agent_outputs,
                proyecto_data
            )
            respuestas[pregunta_id] = respuesta

        logger.info(f"Auto-filled {len(respuestas)} Devil's Advocate questions")
        return respuestas

    def _extract_response_for_question(
        self,
        pregunta_id: str,
        mapping: Dict,
        agent_outputs: Dict[str, Dict],
        proyecto_data: Dict
    ) -> RespuestaAutoFill:
        """Extract and consolidate response for a single question."""

        fuentes_primarias = mapping["fuentes_primarias"]
        campos = mapping["campos_agente"]
        fuentes_secundarias = mapping.get("fuentes_secundarias", [])

        respuesta_texto = ""
        confianza = 0.0
        fuente_usada = FuenteRespuesta.MANUAL
        datos_soporte = []
        indice_opcion = None

        # Try primary sources first
        for fuente in fuentes_primarias:
            agent_key = fuente.value
            if agent_key in agent_outputs:
                agent_data = agent_outputs[agent_key]
                extracted = self._extract_from_agent_data(
                    pregunta_id, agent_data, campos
                )
                if extracted["respuesta"]:
                    respuesta_texto = extracted["respuesta"]
                    confianza = extracted["confianza"]
                    fuente_usada = fuente
                    datos_soporte = extracted.get("soporte", [])
                    indice_opcion = extracted.get("indice_opcion")
                    break

        # If no primary source, try secondary
        if not respuesta_texto and fuentes_secundarias:
            for fuente in fuentes_secundarias:
                agent_key = fuente.value
                if agent_key in agent_outputs:
                    agent_data = agent_outputs[agent_key]
                    extracted = self._extract_from_agent_data(
                        pregunta_id, agent_data, campos
                    )
                    if extracted["respuesta"]:
                        respuesta_texto = extracted["respuesta"]
                        confianza = extracted["confianza"] * 0.8  # Lower confidence
                        fuente_usada = fuente
                        datos_soporte = extracted.get("soporte", [])
                        indice_opcion = extracted.get("indice_opcion")
                        break

        # If still no response, try to extract from general analysis
        if not respuesta_texto:
            for fuente in fuentes_primarias + fuentes_secundarias:
                agent_key = fuente.value
                if agent_key in agent_outputs:
                    agent_data = agent_outputs[agent_key]
                    if "analysis" in agent_data:
                        # Try to find relevant info in the analysis
                        extracted = self._extract_from_analysis(
                            pregunta_id, agent_data["analysis"]
                        )
                        if extracted:
                            respuesta_texto = extracted
                            confianza = 0.5  # Low confidence
                            fuente_usada = fuente
                            break

        # Create response object
        requiere_revision = confianza < self.min_confidence_threshold or not respuesta_texto

        if not respuesta_texto:
            respuesta_texto = "[REQUIERE ENTRADA MANUAL]"
            fuente_usada = FuenteRespuesta.MANUAL
            confianza = 0.0

        return RespuestaAutoFill(
            pregunta_id=pregunta_id,
            respuesta=respuesta_texto,
            confianza=confianza,
            fuente=fuente_usada,
            datos_soporte=datos_soporte,
            requiere_revision=requiere_revision,
            indice_opcion=indice_opcion
        )

    def _extract_from_agent_data(
        self,
        pregunta_id: str,
        agent_data: Dict,
        campos: List[str]
    ) -> Dict[str, Any]:
        """Extract response from specific agent data fields."""

        result = {
            "respuesta": "",
            "confianza": 0.0,
            "soporte": [],
            "indice_opcion": None
        }

        # Check specific fields first
        for campo in campos:
            if campo in agent_data and agent_data[campo]:
                value = agent_data[campo]

                # Handle different value types
                if isinstance(value, str):
                    result["respuesta"] = value
                    result["confianza"] = 0.85
                elif isinstance(value, dict):
                    result["respuesta"] = self._dict_to_response(value)
                    result["confianza"] = 0.8
                    if "indice" in value:
                        result["indice_opcion"] = value["indice"]
                elif isinstance(value, list):
                    result["respuesta"] = "\n".join([str(v) for v in value[:5]])
                    result["confianza"] = 0.75
                elif isinstance(value, bool):
                    result["respuesta"] = "Si" if value else "No"
                    result["confianza"] = 0.95
                    result["indice_opcion"] = 0 if value else 1

                if result["respuesta"]:
                    break

        # Check findings if no specific field matched
        if not result["respuesta"] and "findings" in agent_data:
            findings = agent_data["findings"]
            relevant = self._find_relevant_findings(pregunta_id, findings)
            if relevant:
                result["respuesta"] = relevant
                result["confianza"] = 0.7

        # Add supporting docs
        if "supporting_docs" in agent_data:
            result["soporte"] = agent_data["supporting_docs"][:3]

        # Add confidence from agent if available
        if "confidence_level" in agent_data and result["respuesta"]:
            agent_confidence = agent_data["confidence_level"]
            result["confianza"] = min(result["confianza"], agent_confidence)

        return result

    def _extract_from_analysis(
        self,
        pregunta_id: str,
        analysis: str
    ) -> Optional[str]:
        """Try to extract relevant info from agent's general analysis."""

        # Keywords by question for extraction
        keywords_by_question = {
            "P01_DESCRIPCION_SERVICIO": ["servicio", "descripcion", "objetivo", "alcance"],
            "P02_ENTREGABLE_CONCRETO": ["entregable", "producto", "resultado", "deliverable"],
            "P03_EVIDENCIA_EJECUCION": ["evidencia", "ejecucion", "prestacion", "realizo"],
            "P05_CAPACIDAD_PROVEEDOR": ["capacidad", "infraestructura", "personal", "recursos"],
            "P06_DOMICILIO_VERIFICABLE": ["domicilio", "direccion", "ubicacion", "localizable"],
            "P09_BENEFICIO_SIN_FISCAL": ["beneficio", "valor", "ahorro", "mejora", "ROI"],
            "P13_LISTA_69B": ["69-B", "69B", "lista negra", "EFOS", "operaciones inexistentes"],
            "P14_OPINION_32D": ["32-D", "32D", "opinion de cumplimiento", "constancia"],
            "P17_CFDI_DETALLE": ["CFDI", "factura", "descripcion", "concepto"],
            "P19_PAGO_BANCARIZADO": ["pago", "transferencia", "banco", "bancarizado"],
            "P22_DEBILIDAD_PRINCIPAL": ["debilidad", "riesgo", "vulnerabilidad", "punto debil"],
        }

        keywords = keywords_by_question.get(pregunta_id, [])
        if not keywords:
            return None

        # Find sentences containing keywords
        sentences = analysis.replace("\n", " ").split(".")
        relevant_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(kw.lower() in sentence_lower for kw in keywords):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            # Return first 2-3 relevant sentences
            return ". ".join(relevant_sentences[:3]) + "."

        return None

    def _find_relevant_findings(
        self,
        pregunta_id: str,
        findings: List
    ) -> Optional[str]:
        """Find findings relevant to the question."""

        if not findings:
            return None

        # Simple keyword matching
        keywords = {
            "P13_LISTA_69B": ["69-B", "69B", "lista", "EFOS"],
            "P14_OPINION_32D": ["32-D", "32D", "opinion", "cumplimiento"],
            "P17_CFDI_DETALLE": ["CFDI", "factura", "descripcion"],
            "P19_PAGO_BANCARIZADO": ["pago", "transferencia", "banco"],
        }

        kws = keywords.get(pregunta_id, [])
        if not kws:
            return None

        for finding in findings:
            finding_str = str(finding)
            if any(kw.lower() in finding_str.lower() for kw in kws):
                return finding_str

        return None

    def _dict_to_response(self, value: Dict) -> str:
        """Convert a dictionary value to a response string."""

        if "resultado" in value:
            return str(value["resultado"])
        if "status" in value:
            return str(value["status"])
        if "descripcion" in value:
            return str(value["descripcion"])
        if "value" in value:
            return str(value["value"])

        # Default: stringify first few key-value pairs
        parts = []
        for k, v in list(value.items())[:3]:
            parts.append(f"{k}: {v}")
        return "; ".join(parts)

    def generate_responses_dict(
        self,
        auto_filled: Dict[str, RespuestaAutoFill]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Convert auto-filled responses to the format expected by
        devils_advocate_service.generar_resumen_evaluacion()
        """
        return {
            pregunta_id: {
                "respuesta": resp.respuesta,
                "indice_opcion": resp.indice_opcion,
                "fuente": resp.fuente.value,
                "confianza": resp.confianza
            }
            for pregunta_id, resp in auto_filled.items()
        }

    def get_manual_required_questions(
        self,
        auto_filled: Dict[str, RespuestaAutoFill]
    ) -> List[str]:
        """Get list of question IDs that require manual input."""
        return [
            pregunta_id
            for pregunta_id, resp in auto_filled.items()
            if resp.requiere_revision or resp.fuente == FuenteRespuesta.MANUAL
        ]

    def generate_autofill_summary(
        self,
        auto_filled: Dict[str, RespuestaAutoFill]
    ) -> Dict[str, Any]:
        """Generate a summary of the auto-fill process."""

        total = len(auto_filled)
        auto_filled_count = sum(
            1 for r in auto_filled.values()
            if r.fuente != FuenteRespuesta.MANUAL
        )
        high_confidence = sum(
            1 for r in auto_filled.values()
            if r.confianza >= 0.7
        )
        needs_review = sum(
            1 for r in auto_filled.values()
            if r.requiere_revision
        )

        by_source = {}
        for r in auto_filled.values():
            source = r.fuente.value
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_preguntas": total,
            "auto_llenadas": auto_filled_count,
            "alta_confianza": high_confidence,
            "requieren_revision": needs_review,
            "porcentaje_auto": round(auto_filled_count / total * 100, 1) if total else 0,
            "por_fuente": by_source,
            "fecha_proceso": datetime.now().isoformat()
        }

    async def auto_fill_with_pmo_enhancement(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
        proyecto_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced auto-fill using PMO Subagent Orchestrator for parallel processing.

        This method leverages the PMO's team of specialized subagents to:
        - Analyze agent outputs in parallel
        - Classify findings by severity
        - Identify risks and red flags
        - Generate executive summaries
        - Verify completeness of information

        Args:
            agent_outputs: Dictionary with agent responses (A1-A8)
            proyecto_data: Project metadata

        Returns:
            Dictionary with auto-filled responses and PMO enhancement data
        """
        # First do basic auto-fill
        basic_autofill = self.auto_fill_from_agent_outputs(agent_outputs, proyecto_data)

        # If PMO orchestrator available, enhance with parallel processing
        pmo_enhancement = None
        if self.use_pmo_orchestrator:
            try:
                orchestrator = self._get_pmo_orchestrator()
                if orchestrator:
                    logger.info("[PMO] Running enhanced processing with subagents...")
                    pmo_enhancement = await orchestrator.procesar_para_abogado_diablo(
                        agent_outputs=agent_outputs,
                        proyecto_data=proyecto_data
                    )
                    logger.info("[PMO] Enhanced processing complete")

                    # Enrich auto-fill with PMO analysis
                    basic_autofill = self._enrich_with_pmo_data(
                        basic_autofill, pmo_enhancement
                    )
            except Exception as e:
                logger.warning(f"[PMO] Enhancement failed, using basic mode: {e}")
                pmo_enhancement = {"error": str(e), "modo": "fallback"}

        # Generate summary
        summary = self.generate_autofill_summary(basic_autofill)

        return {
            "respuestas": self.generate_responses_dict(basic_autofill),
            "auto_filled_objects": basic_autofill,
            "summary": summary,
            "pmo_enhancement": pmo_enhancement,
            "manual_required": self.get_manual_required_questions(basic_autofill),
            "procesado_por": "PMO_ENHANCED" if pmo_enhancement else "BASIC"
        }

    def _enrich_with_pmo_data(
        self,
        basic_autofill: Dict[str, RespuestaAutoFill],
        pmo_data: Dict[str, Any]
    ) -> Dict[str, RespuestaAutoFill]:
        """
        Enrich auto-fill responses with PMO subagent analysis.

        Updates confidence levels and adds supporting data from PMO processing.
        """
        if not pmo_data:
            return basic_autofill

        # Get PMO analysis results
        riesgos = pmo_data.get("riesgos_identificados", {})
        clasificacion = pmo_data.get("clasificacion", {})
        verificacion = pmo_data.get("verificacion", {})

        # Use classification to boost confidence on critical findings
        severidad_alta = clasificacion.get("severidad") in ["critico", "importante"]

        # Enrich P22 (main weakness) with PMO risk identification
        if "P22_DEBILIDAD_PRINCIPAL" in basic_autofill and (riesgos or severidad_alta):
            resp = basic_autofill["P22_DEBILIDAD_PRINCIPAL"]
            banderas = riesgos.get("banderas_rojas", [])
            if banderas:
                resp.datos_soporte.extend(banderas[:3])
                if resp.confianza < 0.8:
                    resp.confianza = min(0.85, resp.confianza + 0.15)
                resp.notas = "Enriquecido con análisis PMO"

        # Enrich P24/P25 (lessons/risk) with PMO consolidation
        resumen = pmo_data.get("resumen_ejecutivo", {})
        if resumen:
            for pregunta_id in ["P24_LECCION_PREVENCION", "P25_RIESGO_ACEPTADO"]:
                if pregunta_id in basic_autofill:
                    resp = basic_autofill[pregunta_id]
                    if resp.fuente == FuenteRespuesta.MANUAL:
                        # Try to fill from PMO summary
                        if pregunta_id == "P24_LECCION_PREVENCION":
                            leccion = resumen.get("lecciones", resumen.get("patron", ""))
                            if leccion:
                                resp.respuesta = str(leccion)
                                resp.fuente = FuenteRespuesta.PMO_CONSOLIDADO
                                resp.confianza = 0.7
                                resp.requiere_revision = True
                        elif pregunta_id == "P25_RIESGO_ACEPTADO":
                            riesgo = resumen.get("riesgo_residual", "")
                            if riesgo:
                                resp.respuesta = str(riesgo)
                                resp.fuente = FuenteRespuesta.PMO_CONSOLIDADO
                                resp.confianza = 0.65
                                resp.requiere_revision = True

        # Update completeness based on PMO verification
        completitud = verificacion.get("completitud", {})
        if completitud:
            completitud_score = completitud.get("score", 0)
            faltantes = completitud.get("faltantes", [])
            logger.info(f"[PMO] Completitud score: {completitud_score}%, faltantes: {len(faltantes)}")
            # Flag questions related to missing data
            for pregunta_id, resp in basic_autofill.items():
                for campo in faltantes:
                    if campo.lower() in pregunta_id.lower():
                        resp.requiere_revision = True
                        resp.notas = f"Campo '{campo}' marcado como faltante por verificador PMO"

        return basic_autofill


# Global instance
devils_advocate_autofill_service = DevilsAdvocateAutoFillService()


def get_devils_advocate_autofill_service() -> DevilsAdvocateAutoFillService:
    """Get the Devil's Advocate auto-fill service instance."""
    return devils_advocate_autofill_service
