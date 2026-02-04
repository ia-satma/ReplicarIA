"""
Servicio de Proyectos - PostgreSQL.
Reemplaza el uso de MongoDB para proyectos.
"""

import asyncpg
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import os


class ProjectService:
    """Gestión de proyectos usando PostgreSQL."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool
    
    async def create_project(
        self,
        empresa_id: str,
        nombre: str,
        descripcion: Optional[str] = None,
        tipo: Optional[str] = None,
        proveedor_rfc: Optional[str] = None,
        proveedor_nombre: Optional[str] = None,
        monto_total: Optional[float] = None,
        datos_sib: Optional[dict] = None,
        created_by: Optional[str] = None
    ) -> dict:
        """Crear nuevo proyecto."""
        
        row = await self.db.fetchrow("""
            INSERT INTO projects (
                empresa_id, nombre, descripcion, tipo,
                proveedor_rfc, proveedor_nombre, monto_total,
                datos_sib, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
            RETURNING *
        """,
            empresa_id,
            nombre,
            descripcion,
            tipo,
            proveedor_rfc,
            proveedor_nombre,
            monto_total,
            json.dumps(datos_sib or {}),
            created_by
        )
        
        await self._initialize_phases(str(row["id"]), empresa_id)
        
        return self._row_to_dict(row)
    
    async def get_project(
        self,
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[dict]:
        """Obtener proyecto por ID. Si empresa_id=None, admin puede ver cualquier proyecto."""

        if empresa_id:
            row = await self.db.fetchrow("""
                SELECT * FROM projects
                WHERE id = $1 AND empresa_id = $2
            """, project_id, empresa_id)
        else:
            # Admin: puede ver cualquier proyecto
            row = await self.db.fetchrow("""
                SELECT * FROM projects
                WHERE id = $1
            """, project_id)

        if not row:
            return None

        return self._row_to_dict(row)
    
    async def list_projects(
        self,
        empresa_id: Optional[str] = None,
        estado: Optional[str] = None,
        fase: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> List[dict]:
        """Listar proyectos con filtros. Si empresa_id=None, retorna TODOS los proyectos (admin)."""

        conditions: List[str] = []
        params: List[Any] = []
        param_count = 0

        # Si empresa_id está presente, filtrar por empresa; si es None, admin ve todos
        if empresa_id:
            param_count += 1
            conditions.append(f"empresa_id = ${param_count}")
            params.append(empresa_id)

        if estado:
            param_count += 1
            conditions.append(f"estado = ${param_count}")
            params.append(estado)

        if fase is not None:
            param_count += 1
            conditions.append(f"fase_actual = ${param_count}")
            params.append(fase)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        valid_columns = ["created_at", "updated_at", "nombre", "fase_actual", "risk_score"]
        if order_by not in valid_columns:
            order_by = "created_at"

        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"

        query = f"""
            SELECT * FROM projects
            WHERE {where_clause}
            ORDER BY {order_by} {order_dir}
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])

        rows = await self.db.fetch(query, *params)
        return [self._row_to_dict(row) for row in rows]
    
    async def update_project(
        self,
        project_id: str,
        empresa_id: str,
        updates: dict
    ) -> Optional[dict]:
        """Actualizar proyecto."""
        
        allowed_fields = [
            "nombre", "descripcion", "tipo", "estado", "fase_actual",
            "proveedor_rfc", "proveedor_nombre", "monto_total",
            "risk_score", "compliance_score"
        ]
        
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return await self.get_project(project_id, empresa_id)
        
        set_parts = []
        params = []
        param_count = 0
        
        for field, value in filtered_updates.items():
            param_count += 1
            set_parts.append(f"{field} = ${param_count}")
            params.append(value)
        
        set_clause = ", ".join(set_parts)
        params.extend([project_id, empresa_id])
        
        row = await self.db.fetchrow(f"""
            UPDATE projects
            SET {set_clause}, updated_at = NOW()
            WHERE id = ${param_count + 1} AND empresa_id = ${param_count + 2}
            RETURNING *
        """, *params)
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def update_project_metadata(
        self,
        project_id: str,
        empresa_id: str,
        metadata_updates: dict
    ) -> bool:
        """Actualizar metadata JSONB (merge)."""
        
        result = await self.db.execute("""
            UPDATE projects
            SET metadata = metadata || $1::jsonb,
                updated_at = NOW()
            WHERE id = $2 AND empresa_id = $3
        """, json.dumps(metadata_updates), project_id, empresa_id)
        
        return "UPDATE 1" in result
    
    async def delete_project(
        self,
        project_id: str,
        empresa_id: str
    ) -> bool:
        """Eliminar proyecto (y cascada a fases, deliberaciones)."""
        
        result = await self.db.execute("""
            DELETE FROM projects
            WHERE id = $1 AND empresa_id = $2
        """, project_id, empresa_id)
        
        return "DELETE 1" in result
    
    async def _initialize_phases(self, project_id: str, empresa_id: str):
        """Inicializar las 10 fases del proyecto."""
        
        fases = [
            (0, "Intake"),
            (1, "PO"),
            (2, "Contrato"),
            (3, "Ejecución"),
            (4, "Auditoría"),
            (5, "Entregables"),
            (6, "Cierre"),
            (7, "Defense File"),
            (8, "Pago"),
            (9, "Archivo"),
        ]
        
        for fase_num, nombre in fases:
            await self.db.execute("""
                INSERT INTO project_phases (project_id, empresa_id, fase, nombre, estado)
                VALUES ($1, $2, $3, $4, 'pendiente')
                ON CONFLICT (project_id, fase) DO NOTHING
            """, project_id, empresa_id, fase_num, nombre)
    
    async def get_phase_status(
        self,
        project_id: str,
        empresa_id: str
    ) -> List[dict]:
        """Obtener estado de todas las fases."""
        
        rows = await self.db.fetch("""
            SELECT * FROM project_phases
            WHERE project_id = $1 AND empresa_id = $2
            ORDER BY fase
        """, project_id, empresa_id)
        
        return [dict(row) for row in rows]
    
    async def update_phase_status(
        self,
        project_id: str,
        empresa_id: str,
        fase: int,
        estado: str,
        aprobado_por: Optional[dict] = None
    ) -> bool:
        """Actualizar estado de una fase."""
        
        if aprobado_por:
            await self.db.execute("""
                UPDATE project_phases
                SET estado = $1,
                    aprobado_por = aprobado_por || $2::jsonb,
                    fecha_completado = CASE WHEN $1 = 'aprobado' THEN NOW() ELSE fecha_completado END,
                    updated_at = NOW()
                WHERE project_id = $3 AND empresa_id = $4 AND fase = $5
            """, estado, json.dumps([aprobado_por]), project_id, empresa_id, fase)
        else:
            await self.db.execute("""
                UPDATE project_phases
                SET estado = $1, updated_at = NOW()
                WHERE project_id = $2 AND empresa_id = $3 AND fase = $4
            """, estado, project_id, empresa_id, fase)
        
        if estado == "aprobado":
            await self.db.execute("""
                UPDATE projects
                SET fase_actual = GREATEST(fase_actual, $1 + 1),
                    updated_at = NOW()
                WHERE id = $2 AND empresa_id = $3
            """, fase, project_id, empresa_id)
        
        return True
    
    async def add_deliberation(
        self,
        project_id: str,
        empresa_id: str,
        fase: int,
        agente_id: str,
        tipo: str,
        contenido: str,
        decision: Optional[dict] = None,
        resumen: Optional[str] = None,
        tokens_usados: Optional[int] = None
    ) -> dict:
        """Agregar deliberación de un agente."""
        
        row = await self.db.fetchrow("""
            INSERT INTO deliberations (
                project_id, empresa_id, fase, agente_id,
                tipo, contenido, resumen, decision, tokens_usados
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9)
            RETURNING *
        """,
            project_id, empresa_id, fase, agente_id,
            tipo, contenido, resumen, 
            json.dumps(decision) if decision else None,
            tokens_usados
        )
        
        return dict(row)
    
    async def get_deliberations(
        self,
        project_id: str,
        empresa_id: str,
        fase: Optional[int] = None,
        agente_id: Optional[str] = None
    ) -> List[dict]:
        """Obtener deliberaciones de un proyecto."""
        
        conditions: List[str] = ["project_id = $1", "empresa_id = $2"]
        params: List[Any] = [project_id, empresa_id]
        param_count = 2
        
        if fase is not None:
            param_count += 1
            conditions.append(f"fase = ${param_count}")
            params.append(fase)
        
        if agente_id:
            param_count += 1
            conditions.append(f"agente_id = ${param_count}")
            params.append(agente_id)
        
        query = f"""
            SELECT * FROM deliberations
            WHERE {' AND '.join(conditions)}
            ORDER BY fase, created_at
        """
        
        rows = await self.db.fetch(query, *params)
        return [dict(row) for row in rows]
    
    async def get_latest_deliberation(
        self,
        project_id: str,
        empresa_id: str,
        agente_id: Optional[str] = None
    ) -> Optional[dict]:
        """Obtener última deliberación."""
        
        if agente_id:
            row = await self.db.fetchrow("""
                SELECT * FROM deliberations
                WHERE project_id = $1 AND empresa_id = $2 AND agente_id = $3
                ORDER BY created_at DESC
                LIMIT 1
            """, project_id, empresa_id, agente_id)
        else:
            row = await self.db.fetchrow("""
                SELECT * FROM deliberations
                WHERE project_id = $1 AND empresa_id = $2
                ORDER BY created_at DESC
                LIMIT 1
            """, project_id, empresa_id)
        
        return dict(row) if row else None
    
    async def search_projects(
        self,
        empresa_id: str,
        query: str,
        limit: int = 20
    ) -> List[dict]:
        """Buscar proyectos por nombre, proveedor o RFC."""
        
        rows = await self.db.fetch("""
            SELECT * FROM projects
            WHERE empresa_id = $1
            AND (
                nombre ILIKE $2
                OR proveedor_nombre ILIKE $2
                OR proveedor_rfc ILIKE $2
            )
            ORDER BY updated_at DESC
            LIMIT $3
        """, empresa_id, f"%{query}%", limit)
        
        return [self._row_to_dict(row) for row in rows]
    
    async def get_project_stats(self, empresa_id: Optional[str] = None) -> dict:
        """Estadísticas de proyectos. Si empresa_id=None, retorna estadísticas globales (admin)."""

        if empresa_id:
            row = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE estado = 'activo') as activos,
                    COUNT(*) FILTER (WHERE estado = 'completado') as completados,
                    AVG(risk_score) FILTER (WHERE risk_score IS NOT NULL) as avg_risk_score,
                    SUM(monto_total) FILTER (WHERE estado = 'activo') as monto_activo
                FROM projects
                WHERE empresa_id = $1
            """, empresa_id)
        else:
            # Admin: estadísticas globales de TODOS los proyectos
            row = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE estado = 'activo') as activos,
                    COUNT(*) FILTER (WHERE estado = 'completado') as completados,
                    AVG(risk_score) FILTER (WHERE risk_score IS NOT NULL) as avg_risk_score,
                    SUM(monto_total) FILTER (WHERE estado = 'activo') as monto_activo
                FROM projects
            """)

        return {
            "total": row["total"],
            "activos": row["activos"],
            "completados": row["completados"],
            "avg_risk_score": float(row["avg_risk_score"]) if row["avg_risk_score"] else None,
            "monto_activo": float(row["monto_activo"]) if row["monto_activo"] else 0
        }
    
    def _row_to_dict(self, row: asyncpg.Record) -> dict:
        """Convertir row de asyncpg a dict."""
        result = dict(row)
        
        for key in ["id", "proveedor_id"]:
            if key in result and result[key]:
                result[key] = str(result[key])
        
        for key in ["created_at", "updated_at", "fecha_inicio", "fecha_fin_estimada"]:
            if key in result and result[key]:
                result[key] = result[key].isoformat()
        
        return result


async def get_project_service() -> ProjectService:
    """Factory function para obtener ProjectService."""
    import asyncpg
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")
    
    pool = await asyncpg.create_pool(database_url)
    return ProjectService(pool)
