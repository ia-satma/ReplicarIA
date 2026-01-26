"""
Servicio de Deliberaciones PostgreSQL - Maneja las opiniones y decisiones de los agentes.
Complementa el deliberation_service.py existente con persistencia PostgreSQL.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class DeliberationPGService:
    """Gestión de deliberaciones usando PostgreSQL."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def create_deliberation(
        self,
        project_id: str,
        empresa_id: str,
        fase: int,
        agente_id: str,
        tipo: str,
        contenido: str,
        decision: Optional[dict] = None,
        resumen: Optional[str] = None,
        referencias: Optional[List[dict]] = None,
        documentos_referenciados: Optional[List[str]] = None,
        tokens_usados: Optional[int] = None,
        modelo_usado: Optional[str] = None,
        duracion_ms: Optional[int] = None
    ) -> dict:
        """Crear nueva deliberación."""
        
        if not resumen and contenido:
            resumen = contenido[:200] + "..." if len(contenido) > 200 else contenido
        
        row = await self.db.fetchrow("""
            INSERT INTO deliberations (
                project_id, empresa_id, fase, agente_id,
                tipo, contenido, resumen, decision,
                referencias, documentos_referenciados,
                tokens_usados, modelo_usado, duracion_ms
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8::jsonb,
                $9::jsonb, $10::jsonb,
                $11, $12, $13
            )
            RETURNING *
        """,
            project_id, empresa_id, fase, agente_id,
            tipo, contenido, resumen, json.dumps(decision) if decision else None,
            json.dumps(referencias or []), json.dumps(documentos_referenciados or []),
            tokens_usados, modelo_usado, duracion_ms
        )
        
        return self._row_to_dict(row)
    
    async def get_by_project(
        self,
        project_id: str,
        empresa_id: str,
        fase: Optional[int] = None,
        agente_id: Optional[str] = None,
        tipo: Optional[str] = None
    ) -> List[dict]:
        """Obtener deliberaciones filtradas."""
        
        conditions: List[str] = ["project_id = $1", "empresa_id = $2"]
        params: List[Any] = [project_id, empresa_id]
        idx = 2
        
        if fase is not None:
            idx += 1
            conditions.append(f"fase = ${idx}")
            params.append(fase)
        
        if agente_id:
            idx += 1
            conditions.append(f"agente_id = ${idx}")
            params.append(agente_id)
        
        if tipo:
            idx += 1
            conditions.append(f"tipo = ${idx}")
            params.append(tipo)
        
        rows = await self.db.fetch(f"""
            SELECT * FROM deliberations
            WHERE {' AND '.join(conditions)}
            ORDER BY fase ASC, created_at ASC
        """, *params)
        
        return [self._row_to_dict(row) for row in rows]
    
    async def get_decisions_by_phase(
        self,
        project_id: str,
        empresa_id: str
    ) -> Dict[int, List[dict]]:
        """Obtener decisiones agrupadas por fase."""
        
        rows = await self.db.fetch("""
            SELECT * FROM deliberations
            WHERE project_id = $1 
            AND empresa_id = $2 
            AND tipo = 'decision'
            ORDER BY fase, created_at
        """, project_id, empresa_id)
        
        result: Dict[int, List[dict]] = {}
        for row in rows:
            fase = row["fase"]
            if fase not in result:
                result[fase] = []
            result[fase].append(self._row_to_dict(row))
        
        return result
    
    async def get_agent_opinion(
        self,
        project_id: str,
        empresa_id: str,
        agente_id: str,
        fase: int
    ) -> Optional[dict]:
        """Obtener opinión de un agente específico en una fase."""
        
        row = await self.db.fetchrow("""
            SELECT * FROM deliberations
            WHERE project_id = $1 
            AND empresa_id = $2
            AND agente_id = $3
            AND fase = $4
            ORDER BY created_at DESC
            LIMIT 1
        """, project_id, empresa_id, agente_id, fase)
        
        return self._row_to_dict(row) if row else None
    
    async def check_phase_approved(
        self,
        project_id: str,
        empresa_id: str,
        fase: int,
        required_agents: List[str]
    ) -> dict:
        """Verificar si una fase tiene todas las aprobaciones necesarias."""
        
        rows = await self.db.fetch("""
            SELECT agente_id, decision
            FROM deliberations
            WHERE project_id = $1 
            AND empresa_id = $2
            AND fase = $3
            AND tipo = 'decision'
            AND decision->>'aprobado' = 'true'
        """, project_id, empresa_id, fase)
        
        approved_agents = {row["agente_id"] for row in rows}
        missing_agents = set(required_agents) - approved_agents
        
        return {
            "all_approved": len(missing_agents) == 0,
            "approved_agents": list(approved_agents),
            "missing_agents": list(missing_agents),
            "approval_count": len(approved_agents),
            "required_count": len(required_agents)
        }
    
    async def get_timeline(
        self,
        project_id: str,
        empresa_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Obtener timeline de deliberaciones para visualización."""
        
        rows = await self.db.fetch("""
            SELECT 
                id, fase, agente_id, tipo, resumen, 
                decision, created_at
            FROM deliberations
            WHERE project_id = $1 AND empresa_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """, project_id, empresa_id, limit)
        
        return [self._row_to_dict(row) for row in rows]
    
    async def get_agent_activity(
        self,
        empresa_id: str,
        agente_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[dict]:
        """Obtener actividad reciente de un agente."""
        
        rows = await self.db.fetch(f"""
            SELECT d.*, p.nombre as project_nombre
            FROM deliberations d
            JOIN projects p ON p.id = d.project_id
            WHERE d.empresa_id = $1 
            AND d.agente_id = $2
            AND d.created_at > NOW() - INTERVAL '{days} days'
            ORDER BY d.created_at DESC
            LIMIT $3
        """, empresa_id, agente_id, limit)
        
        return [self._row_to_dict(row) for row in rows]
    
    async def log_interaction(
        self,
        empresa_id: str,
        agente_id: str,
        user_message: str,
        agent_response: str,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        latency_ms: Optional[int] = None,
        modelo_usado: Optional[str] = None,
        rag_chunks_used: Optional[List[dict]] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Registrar interacción con agente."""
        
        row = await self.db.fetchrow("""
            INSERT INTO agent_interactions (
                project_id, empresa_id, user_id, session_id,
                agente_id, user_message, agent_response,
                tokens_in, tokens_out, latency_ms, modelo_usado,
                rag_chunks_used, metadata
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7,
                $8, $9, $10, $11,
                $12::jsonb, $13::jsonb
            )
            RETURNING *
        """,
            project_id, empresa_id, user_id, session_id,
            agente_id, user_message, agent_response,
            tokens_in, tokens_out, latency_ms, modelo_usado,
            json.dumps(rag_chunks_used or []), json.dumps(metadata or {})
        )
        
        return self._row_to_dict(row)
    
    async def get_chat_history(
        self,
        empresa_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Obtener historial de chat de una sesión."""
        
        rows = await self.db.fetch("""
            SELECT * FROM agent_interactions
            WHERE empresa_id = $1 AND session_id = $2
            ORDER BY created_at ASC
            LIMIT $3
        """, empresa_id, session_id, limit)
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row: asyncpg.Record) -> dict:
        """Convertir row a dict."""
        result = dict(row)
        
        for key in ["id", "project_id"]:
            if key in result and result[key]:
                result[key] = str(result[key])
        
        if "created_at" in result and result["created_at"]:
            result["created_at"] = result["created_at"].isoformat()
        
        return result
