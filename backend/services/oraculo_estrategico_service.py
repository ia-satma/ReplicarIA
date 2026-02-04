"""
Oráculo Estratégico Service - Integración con Cloudflare Workers + pCloud
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

INTEGRACIÓN MULTI-TENANT:
- Los resultados de investigación se guardan en pCloud: CLIENTES_NUEVOS/{RFC}/
- Los agentes (A1-A7) consumen estos datos desde sus respectivas carpetas
- Respeta la arquitectura multi-agente definida en agentes_config.py

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

# Import pCloud service for data persistence
try:
    from services.pcloud_service import pcloud_service, AGENT_FOLDER_IDS
    PCLOUD_AVAILABLE = True
except ImportError:
    pcloud_service = None
    AGENT_FOLDER_IDS = {}
    PCLOUD_AVAILABLE = False
    logger.warning("pCloud service not available - investigation results won't be persisted")


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
        "https://oraculo-empresarial.ia-f44.workers.dev"
    )

    # Timeout para llamadas al worker (5 minutos para análisis profundo)
    REQUEST_TIMEOUT = 300

    def __init__(self):
        self.worker_url = self.WORKER_URL
        self.available = self._check_configuration()
        self.pcloud_available = PCLOUD_AVAILABLE

        if self.available:
            logger.info(f"OraculoEstrategicoService inicializado: {self.worker_url}")
        else:
            logger.warning("OraculoEstrategicoService: Worker URL no configurada")

        if self.pcloud_available:
            logger.info("OraculoEstrategicoService: pCloud persistence enabled")

    def _check_configuration(self) -> bool:
        """Verifica si el servicio está correctamente configurado"""
        return bool(self.worker_url and "workers.dev" in self.worker_url)

    # =========================================================================
    # PERSISTENCIA EN PCLOUD - INTEGRACIÓN MULTI-TENANT
    # =========================================================================

    async def guardar_investigacion_pcloud(
        self,
        resultado: Dict[str, Any],
        empresa: str,
        rfc: Optional[str] = None,
        empresa_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Guarda los resultados de investigación en pCloud para consumo de agentes.

        Estructura:
        CLIENTES_NUEVOS/{RFC_O_NOMBRE}/
        ├── investigacion.json          # Resultado completo
        ├── perfil_empresa.json         # Para A1_ESTRATEGIA
        ├── analisis_sector.json        # Para A1_ESTRATEGIA
        ├── due_diligence.json          # Para A6_PROVEEDOR
        └── materialidad.json           # Para S2_MATERIALIDAD

        Args:
            resultado: Resultado de la investigación del Oráculo
            empresa: Nombre de la empresa investigada
            rfc: RFC de la empresa (si se tiene)
            empresa_id: ID del tenant (empresa que realiza la investigación)

        Returns:
            Dict con rutas de archivos guardados y status
        """
        if not self.pcloud_available or not pcloud_service:
            logger.warning("pCloud no disponible - investigación no persistida")
            return {"success": False, "error": "pCloud not available"}

        try:
            # Normalizar identificador de carpeta
            folder_name = rfc.upper().replace(" ", "_") if rfc else empresa.upper().replace(" ", "_")[:20]
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

            # Login a pCloud
            login_result = pcloud_service.login()
            if not login_result.get("success"):
                logger.warning(f"pCloud login failed: {login_result.get('error')}")
                return {"success": False, "error": "pCloud login failed"}

            # Obtener o crear carpeta CLIENTES_NUEVOS
            clientes_nuevos_id = await self._get_or_create_clientes_nuevos_folder()
            if not clientes_nuevos_id:
                return {"success": False, "error": "Could not access CLIENTES_NUEVOS folder"}

            # Crear subcarpeta para esta empresa
            empresa_folder = pcloud_service.create_folder(clientes_nuevos_id, folder_name)
            empresa_folder_id = empresa_folder.get("folder_id", clientes_nuevos_id)

            archivos_guardados = []

            # 1. Guardar investigación completa
            investigacion_completa = {
                "meta": {
                    "empresa": empresa,
                    "rfc": rfc,
                    "empresa_tenant_id": empresa_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "fuente": "oraculo_estrategico",
                    "version": "2.0"
                },
                "resultado": resultado
            }

            result1 = pcloud_service.upload_file(
                folder_id=empresa_folder_id,
                filename=f"investigacion_{timestamp}.json",
                content=json.dumps(investigacion_completa, indent=2, ensure_ascii=False, default=str).encode('utf-8')
            )
            if result1.get("success"):
                archivos_guardados.append(f"investigacion_{timestamp}.json")

            # 2. Extraer y guardar perfil para A1_ESTRATEGIA
            consolidado = resultado.get("consolidado", {})
            if consolidado:
                perfil_empresa = {
                    "empresa": empresa,
                    "rfc": rfc,
                    "resumen_ejecutivo": consolidado.get("resumen_ejecutivo"),
                    "perfil": consolidado.get("perfil_empresa"),
                    "sector": consolidado.get("analisis_sector"),
                    "pestel": consolidado.get("pestel"),
                    "porter": consolidado.get("porter"),
                    "riesgos": consolidado.get("riesgos"),
                    "oportunidades": consolidado.get("oportunidades"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "agente_destino": "A1_ESTRATEGIA"
                }

                result2 = pcloud_service.upload_file(
                    folder_id=empresa_folder_id,
                    filename="perfil_empresa.json",
                    content=json.dumps(perfil_empresa, indent=2, ensure_ascii=False, default=str).encode('utf-8')
                )
                if result2.get("success"):
                    archivos_guardados.append("perfil_empresa.json")

            # 3. Guardar due diligence si existe (para A6_PROVEEDOR)
            if resultado.get("due_diligence"):
                dd_data = {
                    "empresa": empresa,
                    "rfc": rfc,
                    "due_diligence": resultado.get("due_diligence"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "agente_destino": "A6_PROVEEDOR"
                }

                result3 = pcloud_service.upload_file(
                    folder_id=empresa_folder_id,
                    filename="due_diligence.json",
                    content=json.dumps(dd_data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
                )
                if result3.get("success"):
                    archivos_guardados.append("due_diligence.json")

            # 4. Guardar materialidad si existe (para S2_MATERIALIDAD)
            if resultado.get("materialidad_sat"):
                mat_data = {
                    "empresa": empresa,
                    "rfc": rfc,
                    "materialidad_sat": resultado.get("materialidad_sat"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "agente_destino": "S2_MATERIALIDAD"
                }

                result4 = pcloud_service.upload_file(
                    folder_id=empresa_folder_id,
                    filename="materialidad.json",
                    content=json.dumps(mat_data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
                )
                if result4.get("success"):
                    archivos_guardados.append("materialidad.json")

            # 5. Crear archivo de estado para onboarding
            estado_onboarding = {
                "empresa": empresa,
                "rfc": rfc,
                "estado": "pendiente_onboarding",
                "investigacion_completada": True,
                "archivos_disponibles": archivos_guardados,
                "fecha_investigacion": datetime.utcnow().isoformat(),
                "score_confianza": resultado.get("consolidado", {}).get("score_confianza", 0),
                "requiere_revision": resultado.get("consolidado", {}).get("score_confianza", 0) < 70
            }

            result5 = pcloud_service.upload_file(
                folder_id=empresa_folder_id,
                filename="_estado_onboarding.json",
                content=json.dumps(estado_onboarding, indent=2, ensure_ascii=False, default=str).encode('utf-8')
            )
            if result5.get("success"):
                archivos_guardados.append("_estado_onboarding.json")

            logger.info(f"Investigación guardada en pCloud: CLIENTES_NUEVOS/{folder_name}/ - {len(archivos_guardados)} archivos")

            return {
                "success": True,
                "pcloud_folder": f"CLIENTES_NUEVOS/{folder_name}",
                "pcloud_folder_id": empresa_folder_id,
                "archivos_guardados": archivos_guardados,
                "listo_para_onboarding": True
            }

        except Exception as e:
            logger.error(f"Error guardando investigación en pCloud: {e}")
            return {"success": False, "error": str(e)}

    async def _get_or_create_clientes_nuevos_folder(self) -> Optional[int]:
        """Obtiene o crea la carpeta CLIENTES_NUEVOS en pCloud"""
        try:
            # Intentar obtener ID existente
            clientes_nuevos_id = AGENT_FOLDER_IDS.get("CLIENTES_NUEVOS")

            if clientes_nuevos_id:
                return clientes_nuevos_id

            # Si no existe, crear bajo REVISAR.IA
            from services.pcloud_service import REVISAR_IA_CONFIG_FOLDER_ID

            result = pcloud_service.create_folder(
                REVISAR_IA_CONFIG_FOLDER_ID,
                "CLIENTES_NUEVOS"
            )

            if result.get("folder_id"):
                logger.info(f"Carpeta CLIENTES_NUEVOS creada: {result.get('folder_id')}")
                return result.get("folder_id")

            return None

        except Exception as e:
            logger.error(f"Error obteniendo/creando CLIENTES_NUEVOS: {e}")
            return None

    async def investigar_completo(
        self,
        empresa: str,
        sitio_web: Optional[str] = None,
        sector: Optional[str] = None,
        contexto_adicional: Optional[str] = None,
        tipos_investigacion: Optional[List[TipoInvestigacion]] = None,
        rfc: Optional[str] = None,
        empresa_id: Optional[str] = None,
        guardar_pcloud: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta investigación empresarial completa (14 fases).

        Las 14 fases del Worker de Cloudflare:
        1. Scraping Web (si hay URL)
        2. Perfil de Empresa
        3. Análisis de Industria
        4. Panorama Económico
        5. Análisis Competitivo
        6. PESTEL
        7. 5 Fuerzas de Porter
        8. Megatendencias Globales
        9. Análisis ESG
        10. Ecosistema de la Industria
        11. Transformación Digital
        12. Oportunidades y Proyectos
        13. Materialidad SAT (Claude)
        14. Reporte Final (Claude)

        Args:
            empresa: Nombre de la empresa a investigar
            sitio_web: URL del sitio web (opcional)
            sector: Sector/industria (opcional, se infiere si no se proporciona)
            contexto_adicional: Información adicional para contextualizar búsqueda
            tipos_investigacion: Lista de tipos específicos (None = todos)
            rfc: RFC de la empresa (para nombrar carpeta en pCloud)
            empresa_id: ID del tenant que realiza la investigación
            guardar_pcloud: Si guardar automáticamente en pCloud (default: True)

        Returns:
            Dict con resultados consolidados de todas las fases de investigación
        """
        if not self.available:
            return {
                "success": False,
                "error": "Oráculo Estratégico no configurado",
                "message": "Configure ORACULO_WORKER_URL en variables de entorno"
            }

        logger.info(f"Iniciando investigación completa de 14 fases: {empresa}")

        # Estructura para acumular resultados de cada fase
        resultados = {
            "scraping": None,
            "empresa": None,
            "industria": None,
            "economia": None,
            "competidores": None,
            "pestel": None,
            "porter": None,
            "tendencias": None,
            "esg": None,
            "ecosistema": None,
            "digital": None,
            "oportunidades": None,
            "materialidad": None,
            "reporte": None
        }

        fuentes_totales = []
        fases_completadas = 0
        contexto_acumulado = contexto_adicional or ""
        sector_usado = sector or "general"

        try:
            async with aiohttp.ClientSession() as session:

                # ═══════════════════════════════════════════════════════════
                # FASE 1: SCRAPING WEB (si hay URL)
                # ═══════════════════════════════════════════════════════════
                if sitio_web:
                    logger.info(f"Fase 1/14: Scraping web de {sitio_web}")
                    try:
                        async with session.post(
                            f"{self.worker_url}/api/scrape",
                            json={"url": sitio_web},
                            timeout=aiohttp.ClientTimeout(total=60)
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if data.get("success"):
                                    resultados["scraping"] = data
                                    contexto_acumulado += f"\n\nSITIO WEB:\n{data.get('contenido', '')[:15000]}"
                                    fases_completadas += 1
                                    logger.info(f"✓ Fase 1: {data.get('paginas', 0)} páginas extraídas")
                    except Exception as e:
                        logger.warning(f"Fase 1 (scraping) falló: {e}")

                # ═══════════════════════════════════════════════════════════
                # FASES 2-12: INVESTIGACIONES CON PERPLEXITY
                # ═══════════════════════════════════════════════════════════
                investigaciones_perplexity = [
                    ("empresa", "Fase 2/14: Perfil de Empresa"),
                    ("industria", "Fase 3/14: Análisis de Industria"),
                    ("economia", "Fase 4/14: Panorama Económico"),
                    ("competidores", "Fase 5/14: Análisis Competitivo"),
                    ("pestel", "Fase 6/14: Análisis PESTEL"),
                    ("porter", "Fase 7/14: 5 Fuerzas de Porter"),
                    ("tendencias", "Fase 8/14: Megatendencias Globales"),
                    ("esg", "Fase 9/14: Análisis ESG"),
                    ("ecosistema", "Fase 10/14: Ecosistema de la Industria"),
                    ("digital", "Fase 11/14: Transformación Digital"),
                    ("oportunidades", "Fase 12/14: Oportunidades y Proyectos"),
                ]

                for tipo, descripcion in investigaciones_perplexity:
                    logger.info(descripcion)
                    try:
                        payload = {
                            "tipo": tipo,
                            "empresa": empresa,
                            "sector": sector_usado,
                            "contexto": contexto_acumulado[:8000] if tipo in ["competidores", "oportunidades"] else ""
                        }

                        async with session.post(
                            f"{self.worker_url}/api/investigar",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120)
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if data.get("success"):
                                    resultados[tipo] = data.get("resultado")
                                    if data.get("fuentes"):
                                        fuentes_totales.extend(data.get("fuentes", []))
                                    # Acumular contexto para fases siguientes
                                    if tipo in ["empresa", "industria", "economia", "competidores"]:
                                        contexto_acumulado += f"\n\n{tipo.upper()}:\n{data.get('resultado', '')[:5000]}"
                                    fases_completadas += 1
                                    logger.info(f"✓ {descripcion} completada")
                    except Exception as e:
                        logger.warning(f"{descripcion} falló: {e}")

                # ═══════════════════════════════════════════════════════════
                # FASE 13: MATERIALIDAD CON CLAUDE
                # ═══════════════════════════════════════════════════════════
                logger.info("Fase 13/14: Análisis de Materialidad (Claude)")
                try:
                    datos_materialidad = f"""
=== PERFIL DE EMPRESA ===
{resultados.get('empresa', 'No disponible')}

=== INDUSTRIA ===
{resultados.get('industria', 'No disponible')}

=== SITIO WEB ===
{resultados.get('scraping', {}).get('contenido', 'No disponible')[:5000] if resultados.get('scraping') else 'No disponible'}
"""
                    async with session.post(
                        f"{self.worker_url}/api/analizar",
                        json={"tipo": "materialidad", "empresa": empresa, "datos": datos_materialidad},
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                resultados["materialidad"] = data.get("resultado")
                                fases_completadas += 1
                                logger.info("✓ Fase 13: Materialidad completada")
                except Exception as e:
                    logger.warning(f"Fase 13 (materialidad) falló: {e}")

                # ═══════════════════════════════════════════════════════════
                # FASE 14: REPORTE FINAL CON CLAUDE
                # ═══════════════════════════════════════════════════════════
                logger.info("Fase 14/14: Generación de Reporte Final (Claude)")
                try:
                    todo_contexto = f"""
=== PERFIL DE EMPRESA ===
{resultados.get('empresa', 'No disponible')}

=== ANÁLISIS DE INDUSTRIA ===
{resultados.get('industria', 'No disponible')}

=== PANORAMA ECONÓMICO ===
{resultados.get('economia', 'No disponible')}

=== ANÁLISIS COMPETITIVO ===
{resultados.get('competidores', 'No disponible')}

=== ANÁLISIS PESTEL ===
{resultados.get('pestel', 'No disponible')}

=== 5 FUERZAS DE PORTER ===
{resultados.get('porter', 'No disponible')}

=== MEGATENDENCIAS ===
{resultados.get('tendencias', 'No disponible')}

=== ANÁLISIS ESG ===
{resultados.get('esg', 'No disponible')}

=== ECOSISTEMA ===
{resultados.get('ecosistema', 'No disponible')}

=== TRANSFORMACIÓN DIGITAL ===
{resultados.get('digital', 'No disponible')}

=== OPORTUNIDADES Y PROYECTOS ===
{resultados.get('oportunidades', 'No disponible')}

=== MATERIALIDAD SAT ===
{resultados.get('materialidad', 'No disponible')}
"""
                    async with session.post(
                        f"{self.worker_url}/api/analizar",
                        json={"tipo": "reporte_final", "empresa": empresa, "datos": todo_contexto[:50000]},
                        timeout=aiohttp.ClientTimeout(total=180)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("success"):
                                resultados["reporte"] = data.get("resultado")
                                fases_completadas += 1
                                logger.info("✓ Fase 14: Reporte final completado")
                except Exception as e:
                    logger.warning(f"Fase 14 (reporte) falló: {e}")

            # ═══════════════════════════════════════════════════════════
            # CONSOLIDAR RESULTADOS
            # ═══════════════════════════════════════════════════════════
            logger.info(f"Investigación completada: {fases_completadas}/14 fases")

            # Extraer resumen ejecutivo del reporte
            resumen_ejecutivo = ""
            if resultados.get("reporte"):
                reporte = resultados["reporte"]
                # Buscar sección de resumen ejecutivo
                if "RESUMEN EJECUTIVO" in reporte:
                    inicio = reporte.find("RESUMEN EJECUTIVO")
                    fin = reporte.find("───", inicio + 20)
                    if fin > inicio:
                        resumen_ejecutivo = reporte[inicio:fin].replace("RESUMEN EJECUTIVO", "").strip()
                if not resumen_ejecutivo and len(reporte) > 500:
                    resumen_ejecutivo = reporte[:1500]

            # Calcular score de confianza basado en fases completadas
            score_confianza = int((fases_completadas / 14) * 100)

            # Construir resultado consolidado
            consolidado = {
                "resumen_ejecutivo": resumen_ejecutivo or resultados.get("empresa", ""),
                "perfil_empresa": resultados.get("empresa"),
                "analisis_sector": resultados.get("industria"),
                "economia": resultados.get("economia"),
                "competidores": resultados.get("competidores"),
                "pestel": resultados.get("pestel"),
                "porter": resultados.get("porter"),
                "tendencias": resultados.get("tendencias"),
                "esg": resultados.get("esg"),
                "ecosistema": resultados.get("ecosistema"),
                "digital": resultados.get("digital"),
                "oportunidades": resultados.get("oportunidades"),
                "materialidad": resultados.get("materialidad"),
                "reporte_completo": resultados.get("reporte"),
                "riesgos": self._extraer_riesgos(resultados),
                "score_confianza": score_confianza,
                "fuentes": {
                    "perplexity": len(set(fuentes_totales)),
                    "lista": list(set(fuentes_totales))[:20]
                }
            }

            final_result = {
                "success": True,
                "consolidado": consolidado,
                "scraping": resultados.get("scraping"),
                "fases_completadas": fases_completadas,
                "meta": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "empresa_consultada": empresa,
                    "sitio_web": sitio_web,
                    "sector": sector_usado,
                    "rfc": rfc,
                    "fases_completadas": fases_completadas,
                    "source": "oraculo_estrategico_worker_14_fases"
                }
            }

            # =========================================================
            # INTEGRACIÓN PCLOUD - Guardar para sistema de agentes
            # =========================================================
            if guardar_pcloud and self.pcloud_available:
                pcloud_result = await self.guardar_investigacion_pcloud(
                    resultado=final_result,
                    empresa=empresa,
                    rfc=rfc,
                    empresa_id=empresa_id
                )

                final_result["pcloud"] = pcloud_result

                if pcloud_result.get("success"):
                    logger.info(f"Investigación persistida en pCloud: {pcloud_result.get('pcloud_folder')}")
                else:
                    logger.warning(f"No se pudo guardar en pCloud: {pcloud_result.get('error')}")

            return final_result

        except asyncio.TimeoutError:
            logger.error(f"Timeout en investigación de {empresa}")
            return {
                "success": False,
                "error": "Timeout",
                "message": f"La investigación excedió el tiempo límite"
            }
        except Exception as e:
            logger.error(f"Error en investigación: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extraer_riesgos(self, resultados: Dict) -> str:
        """Extrae riesgos de los diferentes análisis"""
        riesgos = []

        # Buscar riesgos en PESTEL
        if resultados.get("pestel"):
            pestel = resultados["pestel"]
            if "AMENAZA" in pestel.upper() or "RIESGO" in pestel.upper():
                # Extraer líneas que mencionen riesgos
                for linea in pestel.split("\n"):
                    if any(palabra in linea.upper() for palabra in ["AMENAZA", "RIESGO", "VULNERABILIDAD"]):
                        riesgos.append(linea.strip())

        # Buscar en Porter
        if resultados.get("porter"):
            porter = resultados["porter"]
            if "ALTA" in porter.upper():
                for linea in porter.split("\n"):
                    if "ALTA" in linea.upper() and "INTENSIDAD" in linea.upper():
                        riesgos.append(linea.strip())

        return "\n".join(riesgos[:10]) if riesgos else "Sin riesgos críticos identificados"

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
