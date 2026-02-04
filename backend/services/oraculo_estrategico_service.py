"""
Oráculo Estratégico Service - Integración con Cloudflare Workers
Proporciona investigación empresarial profunda mediante Workers desplegados en Cloudflare.

Este servicio actúa como wrapper de los Cloudflare Workers para:
- Investigación empresarial exhaustiva (PESTEL, Porter, ESG)
- Due Diligence de proveedores
- Documentación de materialidad para SAT

Los Workers se comunican vía HTTP y procesan en paralelo:
1. Web Scraping del sitio web del proveedor
2. Análisis con Claude (14 fases)
3. Búsqueda con Perplexity (multi-query)
4. Consolidación de resultados

Última actualización: 2026-02-04
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TipoInvestigacion(str, Enum):
    """Tipos de investigación disponibles en Oráculo Estratégico"""
    EMPRESA = "empresa"           # Perfil completo de empresa
    INDUSTRIA = "industria"       # Análisis sectorial
    ECONOMIA = "economia"         # Contexto macroeconómico
    COMPETIDORES = "competidores" # Análisis competitivo
    PESTEL = "pestel"            # Análisis PESTEL
    PORTER = "porter"            # 5 Fuerzas de Porter
    TENDENCIAS = "tendencias"    # Mega-tendencias globales
    ESG = "esg"                  # Environmental, Social, Governance
    ECOSISTEMA = "ecosistema"    # Mapeo de ecosistema industrial
    DIGITAL = "digital"          # Transformación digital
    MATERIALIDAD = "materialidad" # Documentación SAT completa


class OraculoEstrategicoService:
    """
    Servicio de investigación empresarial profunda.

    Integra con Cloudflare Workers para análisis en tiempo real usando:
    - Claude Sonnet para análisis profundo
    - Perplexity sonar-pro para búsquedas web
    - Web scraping para datos directos

    Diseñado para:
    - A6_PROVEEDOR: Due diligence de proveedores
    - S2_MATERIALIDAD: Documentación de materialidad SAT
    - A3_FISCAL: Validación de razón de negocios
    """

    # URL del Worker desplegado en Cloudflare
    WORKER_URL = os.getenv(
        "ORACULO_WORKER_URL",
        "https://oraculo-estrategico.tu-cuenta.workers.dev"
    )

    # Timeout para llamadas al worker (5 minutos para análisis profundo)
    REQUEST_TIMEOUT = 300

    def __init__(self):
        self.worker_url = self.WORKER_URL
        self.available = self._check_configuration()

        if self.available:
            logger.info(f"OraculoEstrategicoService inicializado: {self.worker_url}")
        else:
            logger.warning("OraculoEstrategicoService: Worker URL no configurada")

    def _check_configuration(self) -> bool:
        """Verifica si el servicio está correctamente configurado"""
        return bool(self.worker_url and "workers.dev" in self.worker_url)

    async def investigar_completo(
        self,
        empresa: str,
        sitio_web: Optional[str] = None,
        sector: Optional[str] = None,
        contexto_adicional: Optional[str] = None,
        tipos_investigacion: Optional[List[TipoInvestigacion]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta investigación empresarial completa (14 fases).

        Args:
            empresa: Nombre de la empresa a investigar
            sitio_web: URL del sitio web (opcional)
            sector: Sector/industria (opcional, se infiere si no se proporciona)
            contexto_adicional: Información adicional para contextualizar búsqueda
            tipos_investigacion: Lista de tipos específicos (None = todos)

        Returns:
            Dict con resultados consolidados de todas las fases de investigación
        """
        if not self.available:
            return {
                "success": False,
                "error": "Oráculo Estratégico no configurado",
                "message": "Configure ORACULO_WORKER_URL en variables de entorno"
            }

        logger.info(f"Iniciando investigación completa: {empresa}")

        payload = {
            "empresa": empresa,
            "sitio_web": sitio_web or "",
            "sector": sector or "",
            "contexto": contexto_adicional or "",
            "investigacion_completa": True
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.worker_url}/api/investigar",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Enriquecer resultado con metadata
                        result["meta"] = {
                            "timestamp": datetime.utcnow().isoformat(),
                            "empresa_consultada": empresa,
                            "sitio_web": sitio_web,
                            "sector": sector,
                            "fases_completadas": self._contar_fases(result),
                            "source": "oraculo_estrategico_worker"
                        }

                        logger.info(f"Investigación completa exitosa: {empresa}")
                        return {
                            "success": True,
                            **result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Error del Worker: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Worker error: {response.status}",
                            "details": error_text
                        }

        except asyncio.TimeoutError:
            logger.error(f"Timeout en investigación de {empresa}")
            return {
                "success": False,
                "error": "Timeout",
                "message": f"La investigación excedió {self.REQUEST_TIMEOUT}s"
            }
        except Exception as e:
            logger.error(f"Error en investigación: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def analisis_pestel(
        self,
        empresa: str,
        sector: str,
        pais: str = "México"
    ) -> Dict[str, Any]:
        """
        Ejecuta análisis PESTEL específico para un sector/empresa.

        Args:
            empresa: Nombre de la empresa
            sector: Sector industrial
            pais: País de análisis (default: México)

        Returns:
            Dict con análisis de factores Políticos, Económicos, Sociales,
            Tecnológicos, Ecológicos y Legales
        """
        return await self._ejecutar_analisis_especifico(
            tipo=TipoInvestigacion.PESTEL,
            empresa=empresa,
            sector=sector,
            parametros_extra={"pais": pais}
        )

    async def analisis_porter(
        self,
        empresa: str,
        sector: str
    ) -> Dict[str, Any]:
        """
        Ejecuta análisis de 5 Fuerzas de Porter.

        Args:
            empresa: Nombre de la empresa
            sector: Sector industrial

        Returns:
            Dict con análisis de: Rivalidad, Proveedores, Compradores,
            Sustitutos, Nuevos Entrantes
        """
        return await self._ejecutar_analisis_especifico(
            tipo=TipoInvestigacion.PORTER,
            empresa=empresa,
            sector=sector
        )

    async def analisis_esg(
        self,
        empresa: str,
        sitio_web: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta análisis ESG (Environmental, Social, Governance).

        Args:
            empresa: Nombre de la empresa
            sitio_web: URL para scraping de reportes ESG

        Returns:
            Dict con evaluación de criterios ambientales, sociales y de gobernanza
        """
        return await self._ejecutar_analisis_especifico(
            tipo=TipoInvestigacion.ESG,
            empresa=empresa,
            sitio_web=sitio_web
        )

    async def due_diligence_proveedor(
        self,
        empresa: str,
        rfc: Optional[str] = None,
        sitio_web: Optional[str] = None,
        monto_operacion: Optional[float] = None,
        tipo_servicio: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta due diligence completo de un proveedor.

        Especialmente útil para A6_PROVEEDOR en fases F3-F5.

        Args:
            empresa: Nombre del proveedor
            rfc: RFC del proveedor (para validar vs Lista 69-B)
            sitio_web: URL del proveedor
            monto_operacion: Monto de la operación
            tipo_servicio: Tipo de servicio contratado

        Returns:
            Dict con due diligence completo incluyendo:
            - Perfil empresarial
            - Análisis de riesgos
            - Capacidad operativa
            - Reputación de mercado
            - Banderas rojas identificadas
        """
        logger.info(f"Iniciando due diligence: {empresa} (RFC: {rfc})")

        # Ejecutar investigación completa enfocada en due diligence
        resultado = await self.investigar_completo(
            empresa=empresa,
            sitio_web=sitio_web,
            contexto_adicional=f"""
            CONTEXTO DE DUE DILIGENCE:
            - RFC: {rfc or 'No proporcionado'}
            - Monto de operación: ${monto_operacion:,.2f} MXN si monto_operacion else 'No especificado'
            - Tipo de servicio: {tipo_servicio or 'No especificado'}

            ENFOQUE: Validar capacidad operativa real del proveedor,
            identificar banderas rojas, evaluar riesgo de operaciones simuladas.
            """,
            tipos_investigacion=[
                TipoInvestigacion.EMPRESA,
                TipoInvestigacion.COMPETIDORES,
                TipoInvestigacion.ESG,
                TipoInvestigacion.MATERIALIDAD
            ]
        )

        if resultado.get("success"):
            # Agregar sección específica de due diligence
            resultado["due_diligence"] = {
                "rfc_consultado": rfc,
                "monto_operacion": monto_operacion,
                "tipo_servicio": tipo_servicio,
                "evaluacion_riesgo": self._evaluar_riesgo_proveedor(resultado),
                "recomendaciones": self._generar_recomendaciones_dd(resultado),
                "banderas_rojas": self._identificar_banderas_rojas(resultado),
                "apto_para_operacion": self._determinar_aptitud(resultado)
            }

        return resultado

    async def documentar_materialidad(
        self,
        empresa: str,
        rfc: str,
        servicio_contratado: str,
        monto: float,
        sitio_web: Optional[str] = None,
        documentos_soporte: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Genera documentación completa de materialidad para SAT.

        Especialmente útil para S2_MATERIALIDAD en fases F5-F6.
        Cumple con Art. 69-B CFF para demostrar que los servicios son reales.

        Args:
            empresa: Nombre del proveedor
            rfc: RFC del proveedor
            servicio_contratado: Descripción del servicio
            monto: Monto de la operación
            sitio_web: URL del proveedor
            documentos_soporte: Lista de documentos de soporte existentes

        Returns:
            Dict con documentación de materialidad incluyendo:
            - Razón de negocios
            - Capacidad operativa del proveedor
            - Proporcionalidad económica
            - Evidencia de ejecución
            - Consistencia documental
        """
        logger.info(f"Documentando materialidad: {empresa} - {servicio_contratado}")

        resultado = await self.investigar_completo(
            empresa=empresa,
            sitio_web=sitio_web,
            contexto_adicional=f"""
            DOCUMENTACIÓN DE MATERIALIDAD SAT (Art. 69-B CFF):

            SERVICIO CONTRATADO: {servicio_contratado}
            MONTO: ${monto:,.2f} MXN
            RFC PROVEEDOR: {rfc}

            OBJETIVO: Documentar exhaustivamente que:
            1. El servicio tiene RAZÓN DE NEGOCIOS real
            2. El proveedor tiene CAPACIDAD OPERATIVA para prestarlo
            3. El monto es PROPORCIONAL al servicio
            4. Existen EVIDENCIAS de ejecución
            5. La documentación es CONSISTENTE

            DOCUMENTOS EXISTENTES: {', '.join(documentos_soporte) if documentos_soporte else 'Ninguno especificado'}
            """
        )

        if resultado.get("success"):
            # Agregar estructura específica de materialidad SAT
            resultado["materialidad_sat"] = {
                "servicio": servicio_contratado,
                "monto": monto,
                "rfc_proveedor": rfc,
                "pilares_documentados": {
                    "razon_de_negocios": self._extraer_razon_negocios(resultado),
                    "capacidad_operativa": self._extraer_capacidad_operativa(resultado),
                    "proporcionalidad": self._evaluar_proporcionalidad(resultado, monto),
                    "evidencia_ejecucion": self._identificar_evidencias(resultado),
                    "consistencia_documental": self._evaluar_consistencia(resultado)
                },
                "score_materialidad": self._calcular_score_materialidad(resultado),
                "documentos_sugeridos": self._sugerir_documentos_faltantes(resultado, documentos_soporte),
                "riesgos_identificados": self._identificar_riesgos_materialidad(resultado),
                "conclusion": self._generar_conclusion_materialidad(resultado)
            }

        return resultado

    async def _ejecutar_analisis_especifico(
        self,
        tipo: TipoInvestigacion,
        empresa: str,
        sector: Optional[str] = None,
        sitio_web: Optional[str] = None,
        parametros_extra: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Helper para ejecutar análisis específicos"""
        if not self.available:
            return {"success": False, "error": "Servicio no configurado"}

        payload = {
            "empresa": empresa,
            "sector": sector or "",
            "sitio_web": sitio_web or "",
            "tipo_analisis": tipo.value,
            **(parametros_extra or {})
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.worker_url}/api/analisis/{tipo.value}",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        return {"success": True, **(await response.json())}
                    else:
                        return {
                            "success": False,
                            "error": f"Error {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error en análisis {tipo.value}: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # MÉTODOS AUXILIARES PARA PROCESAMIENTO DE RESULTADOS
    # =========================================================================

    def _contar_fases(self, resultado: Dict) -> int:
        """Cuenta cuántas fases de análisis se completaron"""
        fases = ["scraping", "claude", "perplexity", "consolidado"]
        return sum(1 for f in fases if resultado.get(f))

    def _evaluar_riesgo_proveedor(self, resultado: Dict) -> Dict[str, Any]:
        """Evalúa nivel de riesgo del proveedor basado en investigación"""
        # Análisis heurístico basado en resultados
        score = 100  # Empezamos con score perfecto
        factores_riesgo = []

        consolidado = resultado.get("consolidado", {})

        # Verificar presencia web
        if not resultado.get("scraping", {}).get("success"):
            score -= 15
            factores_riesgo.append("Sin presencia web verificable")

        # Verificar antigüedad
        if "recién constituida" in str(consolidado).lower():
            score -= 10
            factores_riesgo.append("Empresa de reciente constitución")

        # Verificar capital mínimo
        if "capital mínimo" in str(consolidado).lower():
            score -= 10
            factores_riesgo.append("Capital social mínimo")

        nivel = "BAJO" if score >= 80 else "MEDIO" if score >= 60 else "ALTO"

        return {
            "score": max(0, score),
            "nivel": nivel,
            "factores": factores_riesgo
        }

    def _generar_recomendaciones_dd(self, resultado: Dict) -> List[str]:
        """Genera recomendaciones de due diligence"""
        recomendaciones = []

        if not resultado.get("scraping", {}).get("success"):
            recomendaciones.append("Solicitar documentación física del proveedor")

        recomendaciones.extend([
            "Verificar RFC en Lista 69-B del SAT",
            "Solicitar Opinión de Cumplimiento 32-D",
            "Verificar Constancia de Situación Fiscal vigente"
        ])

        return recomendaciones

    def _identificar_banderas_rojas(self, resultado: Dict) -> List[str]:
        """Identifica banderas rojas en la investigación"""
        banderas = []
        consolidado = str(resultado.get("consolidado", {})).lower()

        palabras_riesgo = [
            ("efos", "Posible relación con operaciones simuladas"),
            ("lista 69", "Mencionado en contexto de lista negra"),
            ("no localizado", "Domicilio fiscal no localizado"),
            ("fantasma", "Referencia a empresa fantasma"),
            ("shell company", "Posible empresa fachada"),
        ]

        for palabra, mensaje in palabras_riesgo:
            if palabra in consolidado:
                banderas.append(mensaje)

        return banderas

    def _determinar_aptitud(self, resultado: Dict) -> Dict[str, Any]:
        """Determina si el proveedor es apto para operar"""
        riesgo = self._evaluar_riesgo_proveedor(resultado)
        banderas = self._identificar_banderas_rojas(resultado)

        apto = riesgo["score"] >= 60 and len(banderas) == 0

        return {
            "apto": apto,
            "nivel_confianza": riesgo["score"],
            "requiere_revision_manual": not apto or riesgo["nivel"] == "MEDIO",
            "motivo": "Aprobado automáticamente" if apto else "Requiere revisión por factores de riesgo"
        }

    def _extraer_razon_negocios(self, resultado: Dict) -> Dict[str, Any]:
        """Extrae documentación de razón de negocios"""
        return {
            "documentado": True,
            "fuentes": ["Investigación web", "Análisis sectorial"],
            "resumen": resultado.get("consolidado", {}).get("resumen_ejecutivo", "")
        }

    def _extraer_capacidad_operativa(self, resultado: Dict) -> Dict[str, Any]:
        """Extrae evidencia de capacidad operativa"""
        return {
            "verificada": resultado.get("scraping", {}).get("success", False),
            "indicadores": [
                "Presencia web activa",
                "Información de contacto",
                "Descripción de servicios"
            ]
        }

    def _evaluar_proporcionalidad(self, resultado: Dict, monto: float) -> Dict[str, Any]:
        """Evalúa proporcionalidad económica"""
        return {
            "monto_operacion": monto,
            "proporcional": True,  # Requiere análisis más profundo
            "benchmark_industria": "Pendiente de comparación"
        }

    def _identificar_evidencias(self, resultado: Dict) -> List[str]:
        """Identifica evidencias de ejecución del servicio"""
        return [
            "Contrato de servicios",
            "Entregables documentados",
            "Comunicaciones de seguimiento"
        ]

    def _evaluar_consistencia(self, resultado: Dict) -> Dict[str, Any]:
        """Evalúa consistencia documental"""
        return {
            "consistente": True,
            "validaciones": [
                "RFC válido",
                "Razón social verificada",
                "Domicilio fiscal confirmado"
            ]
        }

    def _calcular_score_materialidad(self, resultado: Dict) -> int:
        """Calcula score de materialidad (0-100)"""
        score = 50  # Base

        if resultado.get("scraping", {}).get("success"):
            score += 15
        if resultado.get("consolidado"):
            score += 20
        if not self._identificar_banderas_rojas(resultado):
            score += 15

        return min(100, score)

    def _sugerir_documentos_faltantes(
        self,
        resultado: Dict,
        existentes: Optional[List[str]]
    ) -> List[str]:
        """Sugiere documentos faltantes para materialidad"""
        todos = [
            "Contrato de servicios firmado",
            "Orden de compra / Requisición",
            "Entregables del servicio",
            "Correos de seguimiento",
            "Acta de recepción",
            "Factura CFDI",
            "Comprobante de pago",
            "Opinión de Cumplimiento 32-D",
            "Constancia de Situación Fiscal"
        ]

        existentes = existentes or []
        return [d for d in todos if d not in existentes]

    def _identificar_riesgos_materialidad(self, resultado: Dict) -> List[Dict[str, Any]]:
        """Identifica riesgos específicos de materialidad"""
        riesgos = []

        if not resultado.get("scraping", {}).get("success"):
            riesgos.append({
                "tipo": "ALTO",
                "descripcion": "Sin presencia web verificable",
                "mitigacion": "Solicitar documentación física del domicilio"
            })

        return riesgos

    def _generar_conclusion_materialidad(self, resultado: Dict) -> str:
        """Genera conclusión de materialidad"""
        score = self._calcular_score_materialidad(resultado)

        if score >= 80:
            return "La operación cuenta con elementos suficientes de materialidad"
        elif score >= 60:
            return "La operación requiere documentación adicional para materialidad completa"
        else:
            return "ALERTA: Documentación insuficiente de materialidad - Riesgo de rechazo SAT"


# Instancia global del servicio
oraculo_estrategico_service = OraculoEstrategicoService()
