"""
agent_learning_service.py - Servicio de Aprendizaje de Agentes

Este servicio implementa el feedback loop que permite a los agentes:
- Aprender de decisiones pasadas
- Mejorar basándose en outcomes reales
- Ajustar prompts dinámicamente
- Calcular y actualizar métricas

Fecha: 2026-01-31
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class LearningPattern:
    """Patrón de aprendizaje identificado."""
    pattern_id: UUID
    agent_id: str
    learning_type: str  # patron_exitoso, patron_fallido, mejora_prompt, nuevo_criterio
    decision_type: str
    pattern_description: str
    recommended_action: str
    effectiveness_score: float
    times_applied: int
    success_rate: float
    context_indicators: Dict[str, Any]
    es_activo: bool
    auto_apply: bool


@dataclass
class AgentMetrics:
    """Métricas de un agente."""
    agent_id: str
    period_start: datetime
    period_end: datetime
    total_decisions: int
    correct_decisions: int
    accuracy_rate: float
    avg_confidence: float
    confidence_calibration: float
    positive_feedback_count: int
    negative_feedback_count: int
    avg_rating: float
    learnings_applied: int
    improvement_trend: float


class AgentLearningService:
    """
    Servicio de aprendizaje continuo para agentes.
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL', '')
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Inicializar conexión a base de datos."""
        if not self.database_url:
            logger.warning("DATABASE_URL not set")
            return False

        try:
            db_url = self.database_url
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)

            import re
            db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)

            self._pool = await asyncpg.create_pool(
                db_url,
                ssl='require',
                min_size=2,
                max_size=10
            )
            return True
        except Exception as e:
            logger.error(f"Learning service initialization error: {e}")
            return False

    async def close(self):
        """Cerrar conexiones."""
        if self._pool:
            await self._pool.close()

    # =========================================================================
    # PROCESAMIENTO DE FEEDBACK
    # =========================================================================

    async def process_pending_feedback(self) -> Dict[str, int]:
        """
        Procesar feedback pendiente y generar aprendizajes.

        Returns:
            Dict con conteo de feedback procesado por agente
        """
        if not self._pool:
            return {}

        try:
            async with self._pool.acquire() as conn:
                # Obtener feedback no procesado
                feedback_rows = await conn.fetch("""
                    SELECT f.*, d.decision_type, d.decision_value, d.reasoning, d.confidence
                    FROM agent_feedback f
                    LEFT JOIN agent_decisions d ON f.decision_id = d.id
                    WHERE f.processed = FALSE
                    ORDER BY f.created_at
                    LIMIT 100
                """)

                processed_count = {}

                for row in feedback_rows:
                    agent_id = row['agent_id']

                    # Procesar según tipo de feedback
                    if row['feedback_type'] == 'negative':
                        await self._process_negative_feedback(conn, row)
                    elif row['feedback_type'] == 'correction':
                        await self._process_correction_feedback(conn, row)
                    elif row['feedback_type'] == 'positive':
                        await self._process_positive_feedback(conn, row)

                    # Marcar como procesado
                    await conn.execute("""
                        UPDATE agent_feedback SET processed = TRUE WHERE id = $1
                    """, row['id'])

                    processed_count[agent_id] = processed_count.get(agent_id, 0) + 1

                return processed_count

        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return {}

    async def _process_negative_feedback(self, conn, feedback: dict):
        """Procesar feedback negativo y crear patrón de aprendizaje."""
        agent_id = feedback['agent_id']
        decision_type = feedback.get('decision_type', 'unknown')
        reasoning = feedback.get('reasoning', '')

        # Crear aprendizaje de patrón fallido
        await conn.execute("""
            INSERT INTO agent_learnings (
                agent_id, learning_type, decision_type,
                pattern_description, recommended_action,
                effectiveness_score, context_indicators
            ) VALUES ($1, 'patron_fallido', $2, $3, $4, 0.3, $5)
        """,
            agent_id, decision_type,
            f"Decisión rechazada por usuario: {reasoning[:200]}",
            f"Revisar criterios para decisiones tipo {decision_type}. Feedback: {feedback.get('feedback_content', '')[:200]}",
            json.dumps({'rating': feedback.get('rating'), 'feedback_type': 'negative'})
        )

    async def _process_correction_feedback(self, conn, feedback: dict):
        """Procesar feedback de corrección y crear aprendizaje específico."""
        agent_id = feedback['agent_id']
        decision_type = feedback.get('decision_type', 'unknown')
        suggested = feedback.get('suggested_decision', '')

        if suggested:
            await conn.execute("""
                INSERT INTO agent_learnings (
                    agent_id, learning_type, decision_type,
                    pattern_description, recommended_action,
                    effectiveness_score, auto_apply
                ) VALUES ($1, 'nuevo_criterio', $2, $3, $4, 0.5, FALSE)
            """,
                agent_id, decision_type,
                f"Corrección sugerida por usuario para {decision_type}",
                f"Considerar: {suggested}. Contexto: {feedback.get('feedback_content', '')[:200]}",
            )

    async def _process_positive_feedback(self, conn, feedback: dict):
        """Procesar feedback positivo y reforzar patrones exitosos."""
        agent_id = feedback['agent_id']
        decision_type = feedback.get('decision_type', 'unknown')
        reasoning = feedback.get('reasoning', '')

        # Buscar si ya existe un patrón exitoso similar
        existing = await conn.fetchrow("""
            SELECT id, times_applied, effectiveness_score
            FROM agent_learnings
            WHERE agent_id = $1 AND decision_type = $2 AND learning_type = 'patron_exitoso'
            ORDER BY created_at DESC LIMIT 1
        """, agent_id, decision_type)

        if existing:
            # Reforzar patrón existente
            new_score = min(1.0, existing['effectiveness_score'] + 0.05)
            await conn.execute("""
                UPDATE agent_learnings
                SET times_applied = times_applied + 1,
                    effectiveness_score = $1
                WHERE id = $2
            """, new_score, existing['id'])
        else:
            # Crear nuevo patrón exitoso
            await conn.execute("""
                INSERT INTO agent_learnings (
                    agent_id, learning_type, decision_type,
                    pattern_description, recommended_action,
                    effectiveness_score, times_applied
                ) VALUES ($1, 'patron_exitoso', $2, $3, $4, 0.7, 1)
            """,
                agent_id, decision_type,
                f"Patrón exitoso identificado en {decision_type}",
                f"Continuar aplicando criterios similares. Razonamiento validado: {reasoning[:200]}"
            )

    # =========================================================================
    # PROCESAMIENTO DE OUTCOMES
    # =========================================================================

    async def process_outcomes_for_learning(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Analizar outcomes recientes y generar aprendizajes.

        Args:
            days_back: Días hacia atrás para analizar

        Returns:
            Estadísticas del procesamiento
        """
        if not self._pool:
            return {}

        try:
            async with self._pool.acquire() as conn:
                # Obtener outcomes recientes con decisiones
                outcomes = await conn.fetch("""
                    SELECT o.*, d.agent_id, d.decision_type, d.decision_value,
                           d.reasoning, d.confidence
                    FROM agent_outcomes o
                    JOIN agent_decisions d ON o.decision_id = d.id
                    WHERE o.created_at > NOW() - INTERVAL '%s days'
                    AND NOT EXISTS (
                        SELECT 1 FROM agent_learnings l
                        WHERE l.agent_id = d.agent_id
                        AND l.created_at > o.created_at
                        AND l.decision_type = d.decision_type
                    )
                """ % days_back)

                stats = {
                    'outcomes_processed': 0,
                    'learnings_created': 0,
                    'patterns_identified': []
                }

                # Agrupar por agente y tipo de decisión
                agent_outcomes = {}
                for o in outcomes:
                    key = (o['agent_id'], o['decision_type'])
                    if key not in agent_outcomes:
                        agent_outcomes[key] = []
                    agent_outcomes[key].append(o)

                # Analizar patrones
                for (agent_id, decision_type), agent_os in agent_outcomes.items():
                    if len(agent_os) < 3:
                        continue

                    correct = sum(1 for o in agent_os if o['was_correct'])
                    total = len(agent_os)
                    accuracy = correct / total

                    # Identificar patrón significativo
                    if accuracy < 0.5:
                        # Patrón de bajo rendimiento
                        await conn.execute("""
                            INSERT INTO agent_learnings (
                                agent_id, learning_type, decision_type,
                                pattern_description, recommended_action,
                                effectiveness_score
                            ) VALUES ($1, 'patron_fallido', $2, $3, $4, $5)
                        """,
                            agent_id, decision_type,
                            f"Bajo rendimiento detectado en {decision_type}: {accuracy*100:.0f}% de acierto",
                            "Revisar criterios de decisión y consultar casos de éxito",
                            accuracy
                        )
                        stats['learnings_created'] += 1
                        stats['patterns_identified'].append({
                            'agent_id': agent_id,
                            'decision_type': decision_type,
                            'type': 'low_performance',
                            'accuracy': accuracy
                        })

                    elif accuracy > 0.85:
                        # Patrón de alto rendimiento
                        await conn.execute("""
                            INSERT INTO agent_learnings (
                                agent_id, learning_type, decision_type,
                                pattern_description, recommended_action,
                                effectiveness_score, auto_apply
                            ) VALUES ($1, 'patron_exitoso', $2, $3, $4, $5, TRUE)
                        """,
                            agent_id, decision_type,
                            f"Alto rendimiento en {decision_type}: {accuracy*100:.0f}% de acierto",
                            "Mantener criterios actuales. Patrón validado.",
                            accuracy
                        )
                        stats['learnings_created'] += 1
                        stats['patterns_identified'].append({
                            'agent_id': agent_id,
                            'decision_type': decision_type,
                            'type': 'high_performance',
                            'accuracy': accuracy
                        })

                    stats['outcomes_processed'] += total

                return stats

        except Exception as e:
            logger.error(f"Error processing outcomes: {e}")
            return {}

    # =========================================================================
    # ACTUALIZACIÓN DE MÉTRICAS
    # =========================================================================

    async def update_agent_metrics(self, agent_id: str = None, period_days: int = 30) -> bool:
        """
        Actualizar métricas de agentes.

        Args:
            agent_id: ID del agente específico (None para todos)
            period_days: Período de días para calcular métricas

        Returns:
            True si se actualizaron correctamente
        """
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                # Obtener agentes a actualizar
                if agent_id:
                    agents = [{'agent_id': agent_id}]
                else:
                    agents = await conn.fetch("""
                        SELECT DISTINCT agent_id FROM agent_decisions
                        WHERE created_at > NOW() - INTERVAL '%s days'
                    """ % period_days)

                period_start = datetime.now() - timedelta(days=period_days)
                period_end = datetime.now()

                for agent_row in agents:
                    aid = agent_row['agent_id']

                    # Calcular métricas de decisiones
                    decision_stats = await conn.fetchrow("""
                        SELECT
                            COUNT(*) as total_decisions,
                            AVG(confidence) as avg_confidence
                        FROM agent_decisions
                        WHERE agent_id = $1 AND created_at > $2
                    """, aid, period_start)

                    # Calcular precisión (necesita outcomes)
                    accuracy_stats = await conn.fetchrow("""
                        SELECT
                            COUNT(*) as total_with_outcome,
                            SUM(CASE WHEN o.was_correct THEN 1 ELSE 0 END) as correct
                        FROM agent_decisions d
                        JOIN agent_outcomes o ON d.id = o.decision_id
                        WHERE d.agent_id = $1 AND d.created_at > $2
                    """, aid, period_start)

                    # Calcular feedback stats
                    feedback_stats = await conn.fetchrow("""
                        SELECT
                            SUM(CASE WHEN feedback_type = 'positive' THEN 1 ELSE 0 END) as positive,
                            SUM(CASE WHEN feedback_type = 'negative' THEN 1 ELSE 0 END) as negative,
                            AVG(rating) as avg_rating
                        FROM agent_feedback
                        WHERE agent_id = $1 AND created_at > $2
                    """, aid, period_start)

                    # Calcular learnings aplicados
                    learnings_stats = await conn.fetchrow("""
                        SELECT SUM(times_applied) as total_applied
                        FROM agent_learnings
                        WHERE agent_id = $1 AND es_activo = TRUE
                    """, aid)

                    # Calcular accuracy rate
                    total_with_outcome = accuracy_stats['total_with_outcome'] or 0
                    correct = accuracy_stats['correct'] or 0
                    accuracy_rate = correct / total_with_outcome if total_with_outcome > 0 else None

                    # Calcular calibración de confianza
                    confidence_calibration = None
                    if accuracy_rate is not None and decision_stats['avg_confidence']:
                        # Qué tan cerca está la confianza promedio de la precisión real
                        confidence_calibration = 1 - abs(decision_stats['avg_confidence'] - accuracy_rate)

                    # Calcular tendencia de mejora
                    improvement_trend = await self._calculate_improvement_trend(conn, aid, period_start)

                    # Insertar o actualizar métricas
                    await conn.execute("""
                        INSERT INTO agent_metrics (
                            agent_id, period_start, period_end,
                            total_decisions, correct_decisions, accuracy_rate,
                            avg_confidence, confidence_calibration,
                            positive_feedback_count, negative_feedback_count, avg_rating,
                            learnings_applied, improvement_trend
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """,
                        aid, period_start, period_end,
                        decision_stats['total_decisions'] or 0,
                        correct,
                        accuracy_rate,
                        decision_stats['avg_confidence'],
                        confidence_calibration,
                        feedback_stats['positive'] or 0,
                        feedback_stats['negative'] or 0,
                        feedback_stats['avg_rating'],
                        learnings_stats['total_applied'] or 0,
                        improvement_trend
                    )

                    logger.info(f"Updated metrics for agent {aid}")

                return True

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            return False

    async def _calculate_improvement_trend(
        self,
        conn,
        agent_id: str,
        period_start: datetime
    ) -> Optional[float]:
        """Calcular tendencia de mejora comparando períodos."""
        try:
            # Período actual
            current = await conn.fetchval("""
                SELECT AVG(CASE WHEN o.was_correct THEN 1.0 ELSE 0.0 END)
                FROM agent_decisions d
                JOIN agent_outcomes o ON d.id = o.decision_id
                WHERE d.agent_id = $1 AND d.created_at > $2
            """, agent_id, period_start)

            # Período anterior (mismo rango)
            days_back = (datetime.now() - period_start).days
            previous_start = period_start - timedelta(days=days_back)

            previous = await conn.fetchval("""
                SELECT AVG(CASE WHEN o.was_correct THEN 1.0 ELSE 0.0 END)
                FROM agent_decisions d
                JOIN agent_outcomes o ON d.id = o.decision_id
                WHERE d.agent_id = $1
                AND d.created_at > $2 AND d.created_at <= $3
            """, agent_id, previous_start, period_start)

            if current is not None and previous is not None:
                return float(current - previous)

            return None

        except Exception:
            return None

    # =========================================================================
    # OBTENCIÓN DE APRENDIZAJES
    # =========================================================================

    async def get_active_learnings(
        self,
        agent_id: str,
        decision_type: str = None,
        limit: int = 10
    ) -> List[LearningPattern]:
        """
        Obtener aprendizajes activos de un agente.

        Args:
            agent_id: ID del agente
            decision_type: Filtrar por tipo de decisión
            limit: Máximo de aprendizajes a retornar
        """
        if not self._pool:
            return []

        try:
            async with self._pool.acquire() as conn:
                if decision_type:
                    rows = await conn.fetch("""
                        SELECT * FROM agent_learnings
                        WHERE agent_id = $1 AND decision_type = $2 AND es_activo = TRUE
                        ORDER BY effectiveness_score DESC, times_applied DESC
                        LIMIT $3
                    """, agent_id, decision_type, limit)
                else:
                    rows = await conn.fetch("""
                        SELECT * FROM agent_learnings
                        WHERE agent_id = $1 AND es_activo = TRUE
                        ORDER BY effectiveness_score DESC, times_applied DESC
                        LIMIT $2
                    """, agent_id, limit)

                return [
                    LearningPattern(
                        pattern_id=row['id'],
                        agent_id=row['agent_id'],
                        learning_type=row['learning_type'],
                        decision_type=row['decision_type'] or '',
                        pattern_description=row['pattern_description'],
                        recommended_action=row['recommended_action'] or '',
                        effectiveness_score=row['effectiveness_score'] or 0,
                        times_applied=row['times_applied'] or 0,
                        success_rate=row['success_rate'] or 0,
                        context_indicators=row['context_indicators'] or {},
                        es_activo=row['es_activo'],
                        auto_apply=row['auto_apply'] or False
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Error getting learnings: {e}")
            return []

    async def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Obtener métricas más recientes de un agente."""
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

                if not row:
                    return None

                return AgentMetrics(
                    agent_id=row['agent_id'],
                    period_start=row['period_start'],
                    period_end=row['period_end'],
                    total_decisions=row['total_decisions'],
                    correct_decisions=row['correct_decisions'],
                    accuracy_rate=row['accuracy_rate'] or 0,
                    avg_confidence=row['avg_confidence'] or 0,
                    confidence_calibration=row['confidence_calibration'] or 0,
                    positive_feedback_count=row['positive_feedback_count'],
                    negative_feedback_count=row['negative_feedback_count'],
                    avg_rating=row['avg_rating'] or 0,
                    learnings_applied=row['learnings_applied'],
                    improvement_trend=row['improvement_trend'] or 0
                )

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return None


# Singleton
_learning_instance: Optional[AgentLearningService] = None


async def get_learning_service() -> AgentLearningService:
    """Obtener instancia singleton del servicio de aprendizaje."""
    global _learning_instance
    if _learning_instance is None:
        _learning_instance = AgentLearningService()
        await _learning_instance.initialize()
    return _learning_instance
