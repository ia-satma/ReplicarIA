"""
Workers Hub Service - Conexión con Cloudflare Workers
Gestiona la comunicación bidireccional entre ReplicarIA y los Workers externos.

Funciones:
- Ejecutar tareas en Workers específicos
- Ejecutar pipelines de múltiples tareas
- Recibir callbacks de Workers completados
- Coordinar Workers con agentes del sistema

Última actualización: 2026-02-04
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class WorkerCapability(str, Enum):
    """Capacidades disponibles en los Workers"""
    # Oráculo Estratégico
    INVESTIGACION = "investigacion"
    DUE_DILIGENCE = "due_diligence"
    PESTEL = "pestel"
    PORTER = "porter"
    ESG = "esg"
    MATERIALIDAD = "materialidad"

    # Lector de documentos
    OCR = "ocr"
    EXTRACCION_TEXTO = "extraccion_texto"
    ANALISIS_PDF = "analisis_pdf"
    ANALISIS_IMAGEN = "analisis_imagen"

    # Redactor
    REDACCION_EMAIL = "redaccion_email"
    NOTIFICACIONES = "notificaciones"
    REPORTES = "reportes"
    RESUMEN = "resumen"

    # Validador SAT
    LISTA_69B = "lista_69b"
    CFDI = "cfdi"
    OPINION_CUMPLIMIENTO = "opinion_cumplimiento"
    RFC = "rfc"

    # Scraper
    SCRAPING = "scraping"
    MONITOREO_WEB = "monitoreo_web"


@dataclass
class WorkerTask:
    """Representa una tarea a ejecutar en un Worker"""
    tarea: str
    parametros: Dict[str, Any]
    agente_id: Optional[str] = None
    empresa_id: Optional[str] = None
    proyecto_id: Optional[str] = None
    callback: Optional[Callable] = None


@dataclass
class WorkerResult:
    """Resultado de una tarea de Worker"""
    success: bool
    worker_id: str
    tarea: str
    resultado: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class WorkersHubService:
    """
    Servicio central para comunicación con Workers Hub.

    Proporciona:
    - Ejecución de tareas individuales
    - Ejecución de pipelines
    - Callbacks y notificaciones
    - Integración con agentes del sistema
    """

    # URL del Workers Hub
    HUB_URL = os.getenv(
        "WORKERS_HUB_URL",
        "https://workers-hub.tu-cuenta.workers.dev"
    )

    # Timeout por defecto (5 minutos)
    DEFAULT_TIMEOUT = 300

    # Mapeo de agentes a capacidades preferidas
    AGENT_CAPABILITIES = {
        "A6_PROVEEDOR": [WorkerCapability.DUE_DILIGENCE, WorkerCapability.INVESTIGACION],
        "S2_MATERIALIDAD": [WorkerCapability.MATERIALIDAD, WorkerCapability.INVESTIGACION],
        "A3_FISCAL": [WorkerCapability.LISTA_69B, WorkerCapability.CFDI, WorkerCapability.PESTEL],
        "A1_SPONSOR": [WorkerCapability.PESTEL, WorkerCapability.PORTER, WorkerCapability.ESG],
        "A8_AUDITOR": [WorkerCapability.OCR, WorkerCapability.ANALISIS_PDF],
        "S_ANALIZADOR": [WorkerCapability.EXTRACCION_TEXTO, WorkerCapability.ANALISIS_PDF],
        "A7_DEFENSA": [WorkerCapability.REPORTES, WorkerCapability.RESUMEN],
        "A2_PMO": [WorkerCapability.NOTIFICACIONES, WorkerCapability.REDACCION_EMAIL],
        "S_REDACTOR": [WorkerCapability.REDACCION_EMAIL, WorkerCapability.REPORTES],
        "S_RESUMIDOR": [WorkerCapability.RESUMEN],
        "S3_RIESGOS": [WorkerCapability.LISTA_69B, WorkerCapability.INVESTIGACION],
        "KB_CURATOR": [WorkerCapability.SCRAPING, WorkerCapability.MONITOREO_WEB],
    }

    def __init__(self):
        self.hub_url = self.HUB_URL
        self.available = self._check_configuration()
        self._pending_callbacks: Dict[str, Callable] = {}

        if self.available:
            logger.info(f"WorkersHubService inicializado: {self.hub_url}")
        else:
            logger.warning("WorkersHubService: Hub URL no configurada")

    def _check_configuration(self) -> bool:
        """Verifica si el servicio está configurado"""
        return bool(self.hub_url and "workers.dev" in self.hub_url)

    # =========================================================================
    # MÉTODOS PRINCIPALES
    # =========================================================================

    async def ejecutar_tarea(
        self,
        tarea: str,
        parametros: Dict[str, Any],
        agente_id: Optional[str] = None,
        empresa_id: Optional[str] = None,
        proyecto_id: Optional[str] = None,
        callback_url: Optional[str] = None,
        timeout: int = None
    ) -> WorkerResult:
        """
        Ejecuta una tarea individual en el Worker apropiado.

        Args:
            tarea: Nombre de la tarea a ejecutar
            parametros: Parámetros para la tarea
            agente_id: ID del agente que solicita la tarea
            empresa_id: ID de la empresa (multi-tenant)
            proyecto_id: ID del proyecto relacionado
            callback_url: URL para notificar cuando termine
            timeout: Timeout en segundos

        Returns:
            WorkerResult con el resultado de la tarea
        """
        if not self.available:
            return WorkerResult(
                success=False,
                worker_id="none",
                tarea=tarea,
                resultado={},
                error="Workers Hub no configurado"
            )

        logger.info(f"Ejecutando tarea: {tarea} (agente: {agente_id})")

        payload = {
            "tarea": tarea,
            "parametros": parametros,
            "agente_id": agente_id,
            "empresa_id": empresa_id,
            "proyecto_id": proyecto_id,
            "callback_url": callback_url
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.hub_url}/execute",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout or self.DEFAULT_TIMEOUT),
                    headers={
                        "Content-Type": "application/json",
                        "X-Empresa-ID": empresa_id or "",
                        "X-Agent-ID": agente_id or ""
                    }
                ) as response:
                    data = await response.json()

                    if response.status == 200 and data.get("success"):
                        return WorkerResult(
                            success=True,
                            worker_id=data.get("worker_id", "unknown"),
                            tarea=tarea,
                            resultado=data
                        )
                    else:
                        return WorkerResult(
                            success=False,
                            worker_id=data.get("worker_id", "none"),
                            tarea=tarea,
                            resultado=data,
                            error=data.get("error", f"HTTP {response.status}")
                        )

        except asyncio.TimeoutError:
            logger.error(f"Timeout en tarea: {tarea}")
            return WorkerResult(
                success=False,
                worker_id="timeout",
                tarea=tarea,
                resultado={},
                error="Timeout esperando Worker"
            )
        except Exception as e:
            logger.error(f"Error ejecutando tarea {tarea}: {e}")
            return WorkerResult(
                success=False,
                worker_id="error",
                tarea=tarea,
                resultado={},
                error=str(e)
            )

    async def ejecutar_pipeline(
        self,
        pasos: List[Dict[str, Any]],
        empresa_id: Optional[str] = None,
        agente_id: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un pipeline de múltiples tareas en secuencia.

        Args:
            pasos: Lista de pasos [{tarea, parametros}, ...]
            empresa_id: ID de empresa
            agente_id: ID de agente
            callback_url: URL para callback final

        Returns:
            Dict con resultados de todos los pasos
        """
        if not self.available:
            return {
                "success": False,
                "error": "Workers Hub no configurado"
            }

        logger.info(f"Ejecutando pipeline de {len(pasos)} pasos")

        payload = {
            "pasos": pasos,
            "empresa_id": empresa_id,
            "agente_id": agente_id,
            "callback_url": callback_url
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Timeout largo para pipelines (10 minutos)
                async with session.post(
                    f"{self.hub_url}/pipeline",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as response:
                    return await response.json()

        except Exception as e:
            logger.error(f"Error en pipeline: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # MÉTODOS DE CONVENIENCIA PARA AGENTES
    # =========================================================================

    async def investigar_proveedor(
        self,
        empresa: str,
        rfc: Optional[str] = None,
        sitio_web: Optional[str] = None,
        monto: Optional[float] = None,
        tipo_servicio: Optional[str] = None,
        empresa_id: Optional[str] = None,
        proyecto_id: Optional[str] = None
    ) -> WorkerResult:
        """
        Método de conveniencia para A6_PROVEEDOR.
        Ejecuta due diligence completo.
        """
        return await self.ejecutar_tarea(
            tarea="due_diligence",
            parametros={
                "empresa": empresa,
                "rfc": rfc,
                "sitio_web": sitio_web,
                "monto_operacion": monto,
                "tipo_servicio": tipo_servicio
            },
            agente_id="A6_PROVEEDOR",
            empresa_id=empresa_id,
            proyecto_id=proyecto_id
        )

    async def documentar_materialidad(
        self,
        empresa: str,
        rfc: str,
        servicio: str,
        monto: float,
        sitio_web: Optional[str] = None,
        empresa_id: Optional[str] = None,
        proyecto_id: Optional[str] = None
    ) -> WorkerResult:
        """
        Método de conveniencia para S2_MATERIALIDAD.
        Genera documentación de materialidad SAT.
        """
        return await self.ejecutar_tarea(
            tarea="materialidad",
            parametros={
                "empresa": empresa,
                "rfc": rfc,
                "servicio_contratado": servicio,
                "monto": monto,
                "sitio_web": sitio_web
            },
            agente_id="S2_MATERIALIDAD",
            empresa_id=empresa_id,
            proyecto_id=proyecto_id
        )

    async def analizar_documento(
        self,
        documento_url: str,
        tipo_documento: str,
        empresa_id: Optional[str] = None,
        proyecto_id: Optional[str] = None
    ) -> WorkerResult:
        """
        Método de conveniencia para A8_AUDITOR.
        Analiza un documento PDF/imagen.
        """
        return await self.ejecutar_tarea(
            tarea="analisis_pdf",
            parametros={
                "url": documento_url,
                "tipo": tipo_documento
            },
            agente_id="A8_AUDITOR",
            empresa_id=empresa_id,
            proyecto_id=proyecto_id
        )

    async def verificar_lista_69b(
        self,
        rfc: str,
        empresa_id: Optional[str] = None
    ) -> WorkerResult:
        """
        Método de conveniencia para verificar RFC en lista 69-B.
        """
        return await self.ejecutar_tarea(
            tarea="lista_69b",
            parametros={"rfc": rfc},
            agente_id="A3_FISCAL",
            empresa_id=empresa_id
        )

    async def generar_reporte(
        self,
        tipo_reporte: str,
        datos: Dict[str, Any],
        empresa_id: Optional[str] = None,
        proyecto_id: Optional[str] = None
    ) -> WorkerResult:
        """
        Método de conveniencia para generar reportes.
        """
        return await self.ejecutar_tarea(
            tarea="reportes",
            parametros={
                "tipo": tipo_reporte,
                "datos": datos
            },
            agente_id="A7_DEFENSA",
            empresa_id=empresa_id,
            proyecto_id=proyecto_id
        )

    # =========================================================================
    # MÉTODOS DE GESTIÓN
    # =========================================================================

    async def get_workers_status(self) -> Dict[str, Any]:
        """Obtiene estado de todos los Workers"""
        if not self.available:
            return {"error": "Hub no configurado"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hub_url}/workers/health",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return await response.json()
        except Exception as e:
            return {"error": str(e)}

    async def get_available_capabilities(self) -> List[str]:
        """Obtiene lista de capacidades disponibles"""
        if not self.available:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.hub_url}/workers",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    data = await response.json()
                    capabilities = set()
                    for worker in data.get("workers", []):
                        capabilities.update(worker.get("capabilities", []))
                    return list(capabilities)
        except Exception as e:
            logger.error(f"Error obteniendo capacidades: {e}")
            return []

    def get_agent_capabilities(self, agent_id: str) -> List[WorkerCapability]:
        """Obtiene capacidades recomendadas para un agente"""
        return self.AGENT_CAPABILITIES.get(agent_id, [])

    # =========================================================================
    # WEBHOOK HANDLER
    # =========================================================================

    async def handle_worker_callback(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Maneja callbacks de Workers completados.
        Este método es llamado por el endpoint de webhook.
        """
        tarea = payload.get("tarea")
        resultado = payload.get("resultado", {})
        agente_id = payload.get("agente_id")
        empresa_id = payload.get("empresa_id")
        proyecto_id = payload.get("proyecto_id")

        logger.info(f"Callback recibido: {tarea} - Agente: {agente_id}")

        # Aquí puedes agregar lógica para:
        # 1. Actualizar estado del proyecto
        # 2. Notificar al agente
        # 3. Trigger siguiente paso del workflow
        # 4. Almacenar resultado en base de datos

        # Ejemplo: emitir evento para que el sistema reaccione
        try:
            from services.event_stream import event_emitter
            await event_emitter.emit("worker_task_completed", {
                "tarea": tarea,
                "resultado": resultado,
                "agente_id": agente_id,
                "empresa_id": empresa_id,
                "proyecto_id": proyecto_id
            })
        except Exception as e:
            logger.warning(f"No se pudo emitir evento: {e}")

        return {
            "processed": True,
            "tarea": tarea,
            "timestamp": datetime.utcnow().isoformat()
        }


# Instancia global del servicio
workers_hub_service = WorkersHubService()
