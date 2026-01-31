"""
dynamic_agent_loader.py - Cargador Dinámico de Agentes para REVISAR.IA

Este servicio:
1. Carga configuraciones de agentes desde PostgreSQL (no hardcoded)
2. Sincroniza documentos de training desde pCloud
3. Inyecta aprendizajes previos en los prompts
4. Gestiona el ciclo de vida de agentes dinámicamente

Fecha: 2026-01-31
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID
import asyncpg
import httpx

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuración dinámica de un agente."""
    id: UUID
    agent_id: str
    nombre: str
    rol: str
    descripcion: str
    personalidad: str
    system_prompt: str
    context_template: Optional[str]
    output_format: Optional[Dict]
    capabilities: List[str]
    fases_activas: List[str]
    puede_bloquear: bool
    fases_bloqueo: List[str]
    documentos_rag: List[str]
    pcloud_path: Optional[str]
    tipo: str
    es_activo: bool
    version: int
    # Permisos CRUD
    puede_crear_agentes: bool = False
    puede_editar_agentes: bool = False
    puede_eliminar_agentes: bool = False
    puede_crear_documentos: bool = True
    puede_editar_documentos: bool = True
    puede_eliminar_documentos: bool = False
    # Aprendizajes inyectados
    learnings: List[Dict] = field(default_factory=list)
    # Métricas recientes
    metrics: Optional[Dict] = None


@dataclass
class SubagentConfig:
    """Configuración de un subagente."""
    id: UUID
    subagent_id: str
    nombre: str
    funcion: str
    descripcion: str
    system_prompt: str
    agente_padre_id: Optional[UUID]
    tipo: str
    capabilities: List[str]
    input_schema: Optional[Dict]
    output_schema: Optional[Dict]
    trigger_conditions: List[Dict]
    priority: int
    es_activo: bool


class DynamicAgentLoader:
    """
    Cargador dinámico de agentes que reemplaza la configuración hardcodeada.
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL', '')
        self._pool: Optional[asyncpg.Pool] = None
        self._agents_cache: Dict[str, AgentConfig] = {}
        self._subagents_cache: Dict[str, SubagentConfig] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_update: Optional[datetime] = None
        self._pcloud_service = None

    async def initialize(self):
        """Inicializar conexión a base de datos."""
        if not self.database_url:
            logger.warning("DATABASE_URL not set, using fallback mode")
            return False

        try:
            # Limpiar URL para asyncpg
            db_url = self.database_url
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)

            # Remover parámetros no soportados
            import re
            db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)

            self._pool = await asyncpg.create_pool(
                db_url,
                ssl='require',
                min_size=2,
                max_size=10
            )
            logger.info("DynamicAgentLoader: Database pool initialized")

            # Ejecutar migración si es necesario
            await self._ensure_tables_exist()

            return True
        except Exception as e:
            logger.error(f"DynamicAgentLoader initialization error: {e}")
            return False

    async def _ensure_tables_exist(self):
        """Verificar que las tablas existan, ejecutar migración si no."""
        async with self._pool.acquire() as conn:
            # Verificar si existe la tabla agent_configs
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'agent_configs'
                )
            """)

            if not exists:
                logger.info("Tables not found, running migration...")
                migration_path = os.path.join(
                    os.path.dirname(__file__),
                    '../migrations/002_agent_dynamic_system.sql'
                )
                if os.path.exists(migration_path):
                    with open(migration_path, 'r') as f:
                        migration_sql = f.read()
                    await conn.execute(migration_sql)
                    logger.info("Migration 002_agent_dynamic_system.sql executed successfully")

    async def close(self):
        """Cerrar conexiones."""
        if self._pool:
            await self._pool.close()

    # =========================================================================
    # CARGA DE AGENTES
    # =========================================================================

    async def load_agent(self, agent_id: str, include_learnings: bool = True) -> Optional[AgentConfig]:
        """
        Cargar configuración de un agente específico.

        Args:
            agent_id: ID del agente (ej: 'A1_ESTRATEGIA')
            include_learnings: Si incluir aprendizajes en el prompt

        Returns:
            AgentConfig o None si no existe
        """
        # Verificar cache
        if self._is_cache_valid() and agent_id in self._agents_cache:
            agent = self._agents_cache[agent_id]
            if include_learnings:
                agent.learnings = await self._load_agent_learnings(agent_id)
            return agent

        if not self._pool:
            return self._get_fallback_agent(agent_id)

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM agent_configs
                    WHERE agent_id = $1 AND es_activo = TRUE
                """, agent_id)

                if not row:
                    logger.warning(f"Agent {agent_id} not found in database")
                    return self._get_fallback_agent(agent_id)

                agent = self._row_to_agent_config(row)

                # Cargar aprendizajes si se requiere
                if include_learnings:
                    agent.learnings = await self._load_agent_learnings(agent_id)

                # Cargar métricas recientes
                agent.metrics = await self._load_agent_metrics(agent_id)

                # Actualizar cache
                self._agents_cache[agent_id] = agent

                return agent

        except Exception as e:
            logger.error(f"Error loading agent {agent_id}: {e}")
            return self._get_fallback_agent(agent_id)

    async def load_all_agents(self, tipo: str = None) -> List[AgentConfig]:
        """
        Cargar todos los agentes activos.

        Args:
            tipo: Filtrar por tipo (principal, subagente, orquestador, codigo)
        """
        if not self._pool:
            return list(self._get_all_fallback_agents().values())

        try:
            async with self._pool.acquire() as conn:
                if tipo:
                    rows = await conn.fetch("""
                        SELECT * FROM agent_configs
                        WHERE es_activo = TRUE AND tipo = $1
                        ORDER BY agent_id
                    """, tipo)
                else:
                    rows = await conn.fetch("""
                        SELECT * FROM agent_configs
                        WHERE es_activo = TRUE
                        ORDER BY agent_id
                    """)

                agents = [self._row_to_agent_config(row) for row in rows]

                # Actualizar cache
                for agent in agents:
                    self._agents_cache[agent.agent_id] = agent

                self._last_cache_update = datetime.now()

                return agents

        except Exception as e:
            logger.error(f"Error loading all agents: {e}")
            return list(self._get_all_fallback_agents().values())

    async def load_subagents(self, agente_padre_id: str = None) -> List[SubagentConfig]:
        """Cargar subagentes, opcionalmente filtrados por agente padre."""
        if not self._pool:
            return []

        try:
            async with self._pool.acquire() as conn:
                if agente_padre_id:
                    # Obtener UUID del padre
                    padre_uuid = await conn.fetchval("""
                        SELECT id FROM agent_configs WHERE agent_id = $1
                    """, agente_padre_id)

                    if padre_uuid:
                        rows = await conn.fetch("""
                            SELECT * FROM subagent_configs
                            WHERE es_activo = TRUE AND agente_padre_id = $1
                            ORDER BY priority
                        """, padre_uuid)
                    else:
                        rows = []
                else:
                    rows = await conn.fetch("""
                        SELECT * FROM subagent_configs
                        WHERE es_activo = TRUE
                        ORDER BY tipo, priority
                    """)

                return [self._row_to_subagent_config(row) for row in rows]

        except Exception as e:
            logger.error(f"Error loading subagents: {e}")
            return []

    # =========================================================================
    # GENERACIÓN DE PROMPTS DINÁMICOS
    # =========================================================================

    async def get_dynamic_prompt(
        self,
        agent_id: str,
        context: Dict[str, Any] = None,
        include_learnings: bool = True
    ) -> str:
        """
        Generar prompt dinámico para un agente, incluyendo:
        - System prompt base
        - Contexto del proyecto/empresa
        - Aprendizajes previos
        - Documentos RAG relevantes
        """
        agent = await self.load_agent(agent_id, include_learnings)
        if not agent:
            return f"Eres un agente de REVISAR.IA con ID {agent_id}."

        prompt_parts = []

        # 1. System prompt base
        prompt_parts.append(agent.system_prompt)

        # 2. Personalidad
        if agent.personalidad:
            prompt_parts.append(f"\n\nPERSONALIDAD:\n{agent.personalidad}")

        # 3. Capacidades
        if agent.capabilities:
            caps = ", ".join(agent.capabilities)
            prompt_parts.append(f"\n\nTUS CAPACIDADES: {caps}")

        # 4. Fases activas
        if agent.fases_activas:
            fases = ", ".join(agent.fases_activas)
            prompt_parts.append(f"\n\nFASES EN LAS QUE PARTICIPAS: {fases}")

        # 5. Permisos CRUD
        permisos = []
        if agent.puede_crear_agentes:
            permisos.append("crear agentes")
        if agent.puede_editar_agentes:
            permisos.append("editar agentes")
        if agent.puede_eliminar_agentes:
            permisos.append("eliminar agentes")
        if agent.puede_crear_documentos:
            permisos.append("crear documentos")
        if agent.puede_editar_documentos:
            permisos.append("editar documentos")
        if agent.puede_eliminar_documentos:
            permisos.append("eliminar documentos")

        if permisos:
            prompt_parts.append(f"\n\nPERMISOS: Puedes {', '.join(permisos)}.")

        # 6. Aprendizajes previos (si hay)
        if include_learnings and agent.learnings:
            learnings_text = self._format_learnings(agent.learnings)
            prompt_parts.append(f"\n\nAPRENDIZAJES PREVIOS:\n{learnings_text}")

        # 7. Métricas (para auto-awareness)
        if agent.metrics:
            metrics_text = self._format_metrics(agent.metrics)
            prompt_parts.append(f"\n\nTUS MÉTRICAS RECIENTES:\n{metrics_text}")

        # 8. Contexto específico (si se proporciona)
        if context:
            if agent.context_template:
                context_text = agent.context_template.format(**context)
            else:
                context_text = json.dumps(context, ensure_ascii=False, indent=2)
            prompt_parts.append(f"\n\nCONTEXTO ACTUAL:\n{context_text}")

        return "\n".join(prompt_parts)

    def _format_learnings(self, learnings: List[Dict]) -> str:
        """Formatear aprendizajes para incluir en prompt."""
        if not learnings:
            return "No hay aprendizajes registrados aún."

        lines = []
        for i, learning in enumerate(learnings[:10], 1):  # Máximo 10 aprendizajes
            pattern = learning.get('pattern_description', '')
            action = learning.get('recommended_action', '')
            effectiveness = learning.get('effectiveness_score', 0)
            lines.append(f"{i}. [{effectiveness*100:.0f}%] {pattern} → {action}")

        return "\n".join(lines)

    def _format_metrics(self, metrics: Dict) -> str:
        """Formatear métricas para incluir en prompt."""
        lines = []
        if metrics.get('accuracy_rate'):
            lines.append(f"- Precisión: {metrics['accuracy_rate']*100:.1f}%")
        if metrics.get('avg_confidence'):
            lines.append(f"- Confianza promedio: {metrics['avg_confidence']*100:.1f}%")
        if metrics.get('total_decisions'):
            lines.append(f"- Decisiones tomadas: {metrics['total_decisions']}")
        if metrics.get('avg_rating'):
            lines.append(f"- Rating promedio: {metrics['avg_rating']:.1f}/5")
        return "\n".join(lines) if lines else "Sin métricas disponibles."

    # =========================================================================
    # APRENDIZAJES Y FEEDBACK
    # =========================================================================

    async def _load_agent_learnings(self, agent_id: str) -> List[Dict]:
        """Cargar aprendizajes activos de un agente."""
        if not self._pool:
            return []

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT pattern_description, recommended_action,
                           effectiveness_score, times_applied
                    FROM agent_learnings
                    WHERE agent_id = $1 AND es_activo = TRUE
                    ORDER BY effectiveness_score DESC, times_applied DESC
                    LIMIT 10
                """, agent_id)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error loading learnings for {agent_id}: {e}")
            return []

    async def _load_agent_metrics(self, agent_id: str) -> Optional[Dict]:
        """Cargar métricas recientes de un agente."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM agent_metrics
                    WHERE agent_id = $1
                    ORDER BY period_end DESC
                    LIMIT 1
                """, agent_id)

                return dict(row) if row else None

        except Exception as e:
            logger.error(f"Error loading metrics for {agent_id}: {e}")
            return None

    async def record_decision(
        self,
        agent_id: str,
        empresa_id: UUID,
        project_id: UUID,
        decision_type: str,
        decision_value: str,
        reasoning: str,
        confidence: float,
        context_used: Dict = None,
        fase: str = None
    ) -> Optional[UUID]:
        """Registrar una decisión de un agente para tracking."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                decision_id = await conn.fetchval("""
                    INSERT INTO agent_decisions (
                        empresa_id, project_id, agent_id,
                        decision_type, decision_value, reasoning, confidence,
                        context_used, fase
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """, empresa_id, project_id, agent_id,
                   decision_type, decision_value, reasoning, confidence,
                   json.dumps(context_used) if context_used else None, fase)

                return decision_id

        except Exception as e:
            logger.error(f"Error recording decision: {e}")
            return None

    async def record_outcome(
        self,
        decision_id: UUID,
        actual_outcome: str,
        was_correct: bool,
        validated_by: str = 'system',
        lessons_learned: str = None
    ) -> bool:
        """Registrar el outcome real de una decisión para feedback loop."""
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_outcomes (
                        decision_id, actual_outcome, was_correct,
                        validated_by, validation_date, lessons_learned
                    ) VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP, $5)
                """, decision_id, actual_outcome, was_correct,
                   validated_by, lessons_learned)

                # Si fue incorrecto, crear un aprendizaje automático
                if not was_correct and lessons_learned:
                    decision = await conn.fetchrow("""
                        SELECT agent_id, decision_type, reasoning
                        FROM agent_decisions WHERE id = $1
                    """, decision_id)

                    if decision:
                        await conn.execute("""
                            INSERT INTO agent_learnings (
                                agent_id, learning_type, decision_type,
                                pattern_description, recommended_action,
                                effectiveness_score
                            ) VALUES ($1, 'patron_fallido', $2, $3, $4, 0.5)
                        """, decision['agent_id'], decision['decision_type'],
                           f"Decisión incorrecta: {decision['reasoning'][:200]}",
                           lessons_learned)

                return True

        except Exception as e:
            logger.error(f"Error recording outcome: {e}")
            return False

    async def record_feedback(
        self,
        agent_id: str,
        empresa_id: UUID,
        user_id: UUID,
        feedback_type: str,
        rating: int,
        feedback_content: str,
        decision_id: UUID = None,
        suggested_decision: str = None
    ) -> bool:
        """Registrar feedback de usuario sobre un agente."""
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_feedback (
                        empresa_id, user_id, agent_id, decision_id,
                        feedback_type, rating, feedback_content,
                        suggested_decision
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, empresa_id, user_id, agent_id, decision_id,
                   feedback_type, rating, feedback_content, suggested_decision)

                return True

        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False

    # =========================================================================
    # SINCRONIZACIÓN CON PCLOUD
    # =========================================================================

    async def sync_agent_documents_from_pcloud(self, agent_id: str) -> Tuple[int, int]:
        """
        Sincronizar documentos de entrenamiento desde pCloud.

        Returns:
            Tuple de (documentos_nuevos, documentos_actualizados)
        """
        # Import pcloud service
        try:
            from .pcloud_service import PCloudService
            pcloud = PCloudService()
        except ImportError:
            logger.warning("PCloudService not available")
            return (0, 0)

        agent = await self.load_agent(agent_id, include_learnings=False)
        if not agent or not agent.pcloud_path:
            logger.warning(f"Agent {agent_id} has no pcloud_path configured")
            return (0, 0)

        try:
            # Listar archivos en pCloud
            files = await pcloud.list_folder(agent.pcloud_path)
            if not files:
                return (0, 0)

            nuevos = 0
            actualizados = 0

            async with self._pool.acquire() as conn:
                for file_info in files:
                    # Verificar si ya existe
                    existing = await conn.fetchrow("""
                        SELECT id, checksum FROM agent_documents
                        WHERE agent_id = $1 AND pcloud_path = $2
                    """, agent_id, file_info['path'])

                    if existing:
                        # Verificar si cambió
                        if existing['checksum'] != file_info.get('checksum'):
                            # Descargar y actualizar
                            content = await pcloud.download_file(file_info['path'])
                            await conn.execute("""
                                UPDATE agent_documents
                                SET content = $1, checksum = $2, last_synced = CURRENT_TIMESTAMP
                                WHERE id = $3
                            """, content, file_info.get('checksum'), existing['id'])
                            actualizados += 1
                    else:
                        # Nuevo documento
                        content = await pcloud.download_file(file_info['path'])
                        await conn.execute("""
                            INSERT INTO agent_documents (
                                agent_id, document_type, title, content,
                                pcloud_path, file_type, checksum, last_synced
                            ) VALUES ($1, 'training', $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                        """, agent_id, file_info['name'], content,
                           file_info['path'], file_info.get('type', 'unknown'),
                           file_info.get('checksum'))
                        nuevos += 1

            logger.info(f"Synced {agent_id}: {nuevos} new, {actualizados} updated")
            return (nuevos, actualizados)

        except Exception as e:
            logger.error(f"Error syncing pcloud for {agent_id}: {e}")
            return (0, 0)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _row_to_agent_config(self, row) -> AgentConfig:
        """Convertir row de DB a AgentConfig."""
        return AgentConfig(
            id=row['id'],
            agent_id=row['agent_id'],
            nombre=row['nombre'],
            rol=row['rol'],
            descripcion=row['descripcion'] or '',
            personalidad=row['personalidad'] or '',
            system_prompt=row['system_prompt'],
            context_template=row['context_template'],
            output_format=row['output_format'],
            capabilities=row['capabilities'] or [],
            fases_activas=row['fases_activas'] or [],
            puede_bloquear=row['puede_bloquear'],
            fases_bloqueo=row['fases_bloqueo'] or [],
            documentos_rag=row['documentos_rag'] or [],
            pcloud_path=row['pcloud_path'],
            tipo=row['tipo'],
            es_activo=row['es_activo'],
            version=row['version'],
            puede_crear_agentes=row['puede_crear_agentes'],
            puede_editar_agentes=row['puede_editar_agentes'],
            puede_eliminar_agentes=row['puede_eliminar_agentes'],
            puede_crear_documentos=row['puede_crear_documentos'],
            puede_editar_documentos=row['puede_editar_documentos'],
            puede_eliminar_documentos=row['puede_eliminar_documentos']
        )

    def _row_to_subagent_config(self, row) -> SubagentConfig:
        """Convertir row de DB a SubagentConfig."""
        return SubagentConfig(
            id=row['id'],
            subagent_id=row['subagent_id'],
            nombre=row['nombre'],
            funcion=row['funcion'],
            descripcion=row['descripcion'] or '',
            system_prompt=row['system_prompt'],
            agente_padre_id=row['agente_padre_id'],
            tipo=row['tipo'],
            capabilities=row['capabilities'] or [],
            input_schema=row['input_schema'],
            output_schema=row['output_schema'],
            trigger_conditions=row['trigger_conditions'] or [],
            priority=row['priority'],
            es_activo=row['es_activo']
        )

    def _is_cache_valid(self) -> bool:
        """Verificar si el cache es válido."""
        if not self._last_cache_update:
            return False
        return datetime.now() - self._last_cache_update < self._cache_ttl

    def _get_fallback_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Obtener configuración fallback de un agente (hardcoded)."""
        fallback_agents = self._get_all_fallback_agents()
        return fallback_agents.get(agent_id)

    def _get_all_fallback_agents(self) -> Dict[str, AgentConfig]:
        """Configuración fallback hardcodeada para cuando DB no está disponible."""
        from uuid import uuid4

        return {
            "A1_ESTRATEGIA": AgentConfig(
                id=uuid4(),
                agent_id="A1_ESTRATEGIA",
                nombre="María Rodríguez",
                rol="Sponsor / Evaluador de Razón de Negocios",
                descripcion="Evalúa razón de negocios y BEE",
                personalidad="Ejecutiva de Monterrey, MBA EGADE",
                system_prompt="Eres María Rodríguez, Directora de Estrategia. Evalúas razón de negocios conforme Art. 5-A CFF.",
                context_template=None,
                output_format=None,
                capabilities=["razon_negocios", "bee", "estrategia"],
                fases_activas=["F0", "F4", "F5", "F9"],
                puede_bloquear=True,
                fases_bloqueo=["F0"],
                documentos_rag=[],
                pcloud_path="/agentes/A1_ESTRATEGIA",
                tipo="principal",
                es_activo=True,
                version=1
            ),
            # ... otros agentes fallback se pueden agregar aquí
        }


# Singleton instance
_loader_instance: Optional[DynamicAgentLoader] = None


async def get_agent_loader() -> DynamicAgentLoader:
    """Obtener instancia singleton del loader."""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DynamicAgentLoader()
        await _loader_instance.initialize()
    return _loader_instance
