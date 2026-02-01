"""
============================================================
PMO Subagent Orchestrator
============================================================

Orquestador de subagentes del PMO (Carlos Mendoza - A2).
Permite ejecutar subagentes en paralelo y gestionar pipelines
de procesamiento de informacion.

El PMO actua como oraculo/orquestador, consolidando la informacion
de todos los agentes principales (A1-A8) a traves de su equipo
de subagentes especializados.

============================================================
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from config.pmo_subagents_config import (
    SUBAGENTES_PMO,
    PIPELINES_PMO,
    CAPACIDADES_COMPARTIDAS,
    SubagenteConfig,
    TipoSubagente,
    Pipeline,
    PrioridadTarea,
    get_subagente_config,
    get_pipeline
)

logger = logging.getLogger(__name__)

# Try to import OpenAI for LLM calls
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - subagents will use fallback mode")


@dataclass
class TareaSubagente:
    """Tarea a ejecutar por un subagente"""
    id: str
    subagente_tipo: TipoSubagente
    input_data: Dict[str, Any]
    prioridad: PrioridadTarea = PrioridadTarea.NORMAL
    contexto_adicional: str = ""
    timeout: int = 30
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResultadoSubagente:
    """Resultado de la ejecucion de un subagente"""
    tarea_id: str
    subagente_id: str
    exito: bool
    resultado: Any
    error: Optional[str] = None
    tiempo_ejecucion_ms: int = 0
    tokens_usados: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class PMOSubagentOrchestrator:
    """
    Orquestador de subagentes del PMO.

    Capacidades:
    - Ejecutar subagentes individuales
    - Ejecutar pipelines (secuenciales o paralelos)
    - Compartir capacidades con otros agentes
    - Gestionar cola de tareas por prioridad
    """

    def __init__(self):
        self.client = None
        self._initialize_client()
        self.tareas_en_progreso: Dict[str, TareaSubagente] = {}
        self.resultados_cache: Dict[str, ResultadoSubagente] = {}

    def _initialize_client(self):
        """Inicializa el cliente de OpenAI si esta disponible"""
        if OPENAI_AVAILABLE:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info("PMO Subagent Orchestrator initialized with OpenAI")
            else:
                logger.warning("OPENAI_API_KEY not set - using fallback mode")
        else:
            logger.warning("OpenAI not available - using fallback mode")

    async def ejecutar_subagente(
        self,
        tipo: TipoSubagente,
        input_data: Dict[str, Any],
        contexto: str = ""
    ) -> ResultadoSubagente:
        """
        Ejecuta un subagente individual.

        Args:
            tipo: Tipo de subagente a ejecutar
            input_data: Datos de entrada para el subagente
            contexto: Contexto adicional para la tarea

        Returns:
            ResultadoSubagente con el resultado de la ejecucion
        """
        config = get_subagente_config(tipo)
        if not config:
            return ResultadoSubagente(
                tarea_id=f"err-{datetime.now().timestamp()}",
                subagente_id=tipo.value,
                exito=False,
                resultado=None,
                error=f"Subagente {tipo.value} no encontrado"
            )

        tarea_id = f"{tipo.value}-{datetime.now().timestamp()}"
        inicio = datetime.now()

        try:
            if self.client:
                resultado = await self._ejecutar_con_llm(config, input_data, contexto)
            else:
                resultado = await self._ejecutar_fallback(config, input_data, contexto)

            tiempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)

            return ResultadoSubagente(
                tarea_id=tarea_id,
                subagente_id=config.id,
                exito=True,
                resultado=resultado,
                tiempo_ejecucion_ms=tiempo_ms
            )

        except asyncio.TimeoutError:
            return ResultadoSubagente(
                tarea_id=tarea_id,
                subagente_id=config.id,
                exito=False,
                resultado=None,
                error=f"Timeout despues de {config.timeout_segundos}s"
            )
        except Exception as e:
            logger.error(f"Error ejecutando {config.id}: {e}")
            return ResultadoSubagente(
                tarea_id=tarea_id,
                subagente_id=config.id,
                exito=False,
                resultado=None,
                error=str(e)
            )

    async def _ejecutar_con_llm(
        self,
        config: SubagenteConfig,
        input_data: Dict[str, Any],
        contexto: str
    ) -> Dict[str, Any]:
        """Ejecuta el subagente usando el LLM"""

        # Construir el mensaje del usuario
        user_message = f"""
CONTEXTO:
{contexto}

DATOS DE ENTRADA:
{self._format_input(input_data)}

Procesa estos datos segun tus instrucciones y responde en formato JSON.
"""

        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=config.modelo,
                temperature=config.temperatura,
                messages=[
                    {"role": "system", "content": config.prompt_sistema},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            ),
            timeout=config.timeout_segundos
        )

        content = response.choices[0].message.content

        # Parsear JSON
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}

    async def _ejecutar_fallback(
        self,
        config: SubagenteConfig,
        input_data: Dict[str, Any],
        contexto: str
    ) -> Dict[str, Any]:
        """Ejecuta logica de fallback cuando no hay LLM disponible"""

        # Fallback simple basado en tipo de subagente
        tipo = config.tipo

        if tipo == TipoSubagente.ANALIZADOR:
            return self._fallback_analizador(input_data)
        elif tipo == TipoSubagente.CLASIFICADOR:
            return self._fallback_clasificador(input_data)
        elif tipo == TipoSubagente.RESUMIDOR:
            return self._fallback_resumidor(input_data)
        elif tipo == TipoSubagente.IDENTIFICADOR:
            return self._fallback_identificador(input_data)
        elif tipo == TipoSubagente.VERIFICADOR:
            return self._fallback_verificador(input_data)
        else:
            return {"mensaje": "Procesado en modo fallback", "datos": input_data}

    def _fallback_analizador(self, input_data: Dict) -> Dict:
        """Fallback para el analizador"""
        return {
            "datos_extraidos": list(input_data.keys()),
            "campos_con_valor": sum(1 for v in input_data.values() if v),
            "campos_vacios": sum(1 for v in input_data.values() if not v),
            "modo": "fallback"
        }

    def _fallback_clasificador(self, input_data: Dict) -> Dict:
        """Fallback para el clasificador"""
        # Buscar palabras clave para clasificar
        texto = str(input_data).lower()

        if any(kw in texto for kw in ["69-b", "efos", "rechazo", "bandera roja"]):
            severidad = "critico"
        elif any(kw in texto for kw in ["alerta", "revisar", "incompleto"]):
            severidad = "importante"
        else:
            severidad = "informativo"

        return {
            "severidad": severidad,
            "tipo": "general",
            "modo": "fallback"
        }

    def _fallback_resumidor(self, input_data: Dict) -> Dict:
        """Fallback para el resumidor"""
        # Crear resumen simple
        keys = list(input_data.keys())[:5]
        return {
            "resumen": f"Datos procesados: {', '.join(keys)}",
            "campos_principales": keys,
            "modo": "fallback"
        }

    def _fallback_identificador(self, input_data: Dict) -> Dict:
        """Fallback para el identificador"""
        banderas = []
        alertas = []

        texto = str(input_data).lower()

        if "69-b" in texto or "efos" in texto:
            banderas.append("Posible proveedor en lista 69-B")
        if "sin evidencia" in texto or "no disponible" in texto:
            alertas.append("Evidencia posiblemente incompleta")

        return {
            "banderas_rojas": banderas,
            "alertas": alertas,
            "oportunidades": [],
            "modo": "fallback"
        }

    def _fallback_verificador(self, input_data: Dict) -> Dict:
        """Fallback para el verificador"""
        campos_llenos = sum(1 for v in input_data.values() if v)
        total_campos = len(input_data)
        completitud = (campos_llenos / total_campos * 100) if total_campos else 0

        return {
            "completitud": {
                "score": round(completitud, 1),
                "faltantes": [k for k, v in input_data.items() if not v]
            },
            "modo": "fallback"
        }

    def _format_input(self, data: Dict) -> str:
        """Formatea los datos de entrada para el prompt"""
        import json
        try:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        except:
            return str(data)

    async def ejecutar_pipeline(
        self,
        nombre_pipeline: str,
        input_data: Dict[str, Any],
        contexto: str = ""
    ) -> Dict[str, Any]:
        """
        Ejecuta un pipeline completo de subagentes.

        Args:
            nombre_pipeline: Nombre del pipeline a ejecutar
            input_data: Datos iniciales
            contexto: Contexto adicional

        Returns:
            Diccionario con resultados de cada paso
        """
        pipeline = get_pipeline(nombre_pipeline)
        if not pipeline:
            return {
                "exito": False,
                "error": f"Pipeline '{nombre_pipeline}' no encontrado"
            }

        logger.info(f"[PMO] Iniciando pipeline: {pipeline.nombre}")

        resultados = {}
        datos_actuales = input_data

        if pipeline.paralelo:
            # Ejecutar todos los pasos en paralelo
            tareas = [
                self.ejecutar_subagente(paso, datos_actuales, contexto)
                for paso in pipeline.pasos
            ]
            resultados_paralelos = await asyncio.gather(*tareas)

            for i, resultado in enumerate(resultados_paralelos):
                paso = pipeline.pasos[i]
                resultados[paso.value] = resultado

        else:
            # Ejecutar secuencialmente, pasando output de uno al siguiente
            for paso in pipeline.pasos:
                resultado = await self.ejecutar_subagente(
                    paso, datos_actuales, contexto
                )
                resultados[paso.value] = resultado

                if resultado.exito and resultado.resultado:
                    # El output de este paso es input del siguiente
                    if isinstance(resultado.resultado, dict):
                        datos_actuales = {**datos_actuales, **resultado.resultado}

        # Consolidar resultados
        exito_total = all(r.exito for r in resultados.values())

        return {
            "exito": exito_total,
            "pipeline": nombre_pipeline,
            "pasos_ejecutados": len(pipeline.pasos),
            "resultados": {
                k: {
                    "exito": v.exito,
                    "resultado": v.resultado,
                    "tiempo_ms": v.tiempo_ejecucion_ms
                }
                for k, v in resultados.items()
            },
            "datos_consolidados": datos_actuales
        }

    async def ejecutar_capacidad(
        self,
        capacidad: str,
        input_data: Dict[str, Any],
        contexto: str = ""
    ) -> ResultadoSubagente:
        """
        Ejecuta una capacidad compartida.
        Otros agentes pueden llamar este metodo para usar los subagentes del PMO.

        Args:
            capacidad: Nombre de la capacidad (ej: "analizar_datos", "clasificar_hallazgo")
            input_data: Datos de entrada
            contexto: Contexto adicional

        Returns:
            ResultadoSubagente
        """
        tipo = CAPACIDADES_COMPARTIDAS.get(capacidad)
        if not tipo:
            return ResultadoSubagente(
                tarea_id=f"cap-{datetime.now().timestamp()}",
                subagente_id="UNKNOWN",
                exito=False,
                resultado=None,
                error=f"Capacidad '{capacidad}' no encontrada. "
                      f"Disponibles: {list(CAPACIDADES_COMPARTIDAS.keys())}"
            )

        return await self.ejecutar_subagente(tipo, input_data, contexto)

    async def procesar_para_abogado_diablo(
        self,
        agent_outputs: Dict[str, Dict[str, Any]],
        proyecto_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa los outputs de agentes para el Abogado del Diablo.
        Usa el pipeline especializado para generar las respuestas.

        Args:
            agent_outputs: Outputs de los agentes A1-A8
            proyecto_data: Datos del proyecto

        Returns:
            Datos procesados listos para el reporte
        """
        logger.info("[PMO] Procesando datos para Abogado del Diablo...")

        # Paso 1: Analizar todos los outputs en paralelo
        tareas_analisis = []
        for agente_id, output in agent_outputs.items():
            tareas_analisis.append(
                self.ejecutar_subagente(
                    TipoSubagente.ANALIZADOR,
                    {"agente": agente_id, "output": output},
                    f"Analizar output del agente {agente_id}"
                )
            )

        resultados_analisis = await asyncio.gather(*tareas_analisis)

        # Consolidar analisis
        analisis_consolidado = {
            agent_outputs.keys()[i] if i < len(agent_outputs) else f"agente_{i}":
                r.resultado for i, r in enumerate(resultados_analisis) if r.exito
        }

        # Paso 2: Identificar riesgos y banderas rojas
        resultado_identificacion = await self.ejecutar_subagente(
            TipoSubagente.IDENTIFICADOR,
            {"analisis": analisis_consolidado, "proyecto": proyecto_data},
            "Identificar riesgos y banderas rojas para el Abogado del Diablo"
        )

        # Paso 3: Clasificar hallazgos
        resultado_clasificacion = await self.ejecutar_subagente(
            TipoSubagente.CLASIFICADOR,
            {
                "hallazgos": resultado_identificacion.resultado,
                "proyecto": proyecto_data
            },
            "Clasificar hallazgos por severidad"
        )

        # Paso 4: Verificar completitud
        resultado_verificacion = await self.ejecutar_subagente(
            TipoSubagente.VERIFICADOR,
            {"datos": analisis_consolidado, "proyecto": proyecto_data},
            "Verificar completitud de la informacion"
        )

        # Paso 5: Generar resumen ejecutivo
        resultado_resumen = await self.ejecutar_subagente(
            TipoSubagente.RESUMIDOR,
            {
                "analisis": analisis_consolidado,
                "riesgos": resultado_identificacion.resultado,
                "clasificacion": resultado_clasificacion.resultado
            },
            "Generar resumen ejecutivo para el Abogado del Diablo"
        )

        return {
            "analisis_por_agente": analisis_consolidado,
            "riesgos_identificados": resultado_identificacion.resultado,
            "clasificacion": resultado_clasificacion.resultado,
            "verificacion": resultado_verificacion.resultado,
            "resumen_ejecutivo": resultado_resumen.resultado,
            "procesado_por": "PMO_SUBAGENT_ORCHESTRATOR",
            "timestamp": datetime.now().isoformat()
        }

    def listar_subagentes_disponibles(self) -> List[Dict[str, Any]]:
        """Lista todos los subagentes disponibles"""
        from config.pmo_subagents_config import listar_subagentes
        return listar_subagentes()

    def listar_capacidades(self) -> List[str]:
        """Lista todas las capacidades disponibles"""
        from config.pmo_subagents_config import listar_capacidades_disponibles
        return listar_capacidades_disponibles()

    def listar_pipelines(self) -> List[Dict[str, Any]]:
        """Lista todos los pipelines disponibles"""
        return [
            {
                "nombre": nombre,
                "descripcion": p.descripcion,
                "pasos": [paso.value for paso in p.pasos],
                "paralelo": p.paralelo
            }
            for nombre, p in PIPELINES_PMO.items()
        ]


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

pmo_subagent_orchestrator = PMOSubagentOrchestrator()


def get_pmo_subagent_orchestrator() -> PMOSubagentOrchestrator:
    """Obtiene la instancia del orquestador de subagentes del PMO"""
    return pmo_subagent_orchestrator
