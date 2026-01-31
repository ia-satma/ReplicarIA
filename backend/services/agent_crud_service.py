"""
agent_crud_service.py - Servicio CRUD para Agentes Dinámicos

Este servicio permite que los agentes (y usuarios autorizados) puedan:
- Crear nuevos agentes y subagentes
- Editar configuraciones de agentes existentes
- Eliminar/desactivar agentes
- Gestionar documentos de agentes
- Auditar todos los cambios

Fecha: 2026-01-31
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class AgentCreateRequest:
    """Request para crear un nuevo agente."""
    agent_id: str
    nombre: str
    rol: str
    descripcion: str
    personalidad: Optional[str] = None
    system_prompt: str = ""
    tipo: str = "principal"  # principal, subagente, orquestador, codigo, soporte
    capabilities: List[str] = None
    fases_activas: List[str] = None
    puede_bloquear: bool = False
    fases_bloqueo: List[str] = None
    agente_padre_id: Optional[str] = None
    pcloud_path: Optional[str] = None
    # Permisos
    puede_crear_agentes: bool = False
    puede_editar_agentes: bool = False
    puede_eliminar_agentes: bool = False
    puede_crear_documentos: bool = True
    puede_editar_documentos: bool = True
    puede_eliminar_documentos: bool = False


@dataclass
class AgentUpdateRequest:
    """Request para actualizar un agente."""
    nombre: Optional[str] = None
    rol: Optional[str] = None
    descripcion: Optional[str] = None
    personalidad: Optional[str] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[List[str]] = None
    fases_activas: Optional[List[str]] = None
    puede_bloquear: Optional[bool] = None
    fases_bloqueo: Optional[List[str]] = None
    pcloud_path: Optional[str] = None
    es_activo: Optional[bool] = None
    # Permisos
    puede_crear_agentes: Optional[bool] = None
    puede_editar_agentes: Optional[bool] = None
    puede_eliminar_agentes: Optional[bool] = None
    puede_crear_documentos: Optional[bool] = None
    puede_editar_documentos: Optional[bool] = None
    puede_eliminar_documentos: Optional[bool] = None


@dataclass
class SubagentCreateRequest:
    """Request para crear un subagente."""
    subagent_id: str
    nombre: str
    funcion: str
    descripcion: str
    system_prompt: str
    tipo: str  # tipificacion, materialidad, riesgos, organizacion, clasificacion, trafico
    agente_padre_id: Optional[str] = None
    capabilities: List[str] = None
    input_schema: Optional[Dict] = None
    output_schema: Optional[Dict] = None
    trigger_conditions: List[Dict] = None
    priority: int = 5


@dataclass
class DocumentCreateRequest:
    """Request para crear un documento de agente."""
    agent_id: str
    document_type: str  # metodologia, training, feedback, ejemplo
    title: str
    content: str
    file_type: Optional[str] = "md"
    pcloud_path: Optional[str] = None


class AgentCRUDService:
    """
    Servicio para operaciones CRUD de agentes.
    Valida permisos y registra auditoría de todos los cambios.
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
            logger.error(f"AgentCRUDService initialization error: {e}")
            return False

    async def close(self):
        """Cerrar conexiones."""
        if self._pool:
            await self._pool.close()

    # =========================================================================
    # VERIFICACIÓN DE PERMISOS
    # =========================================================================

    async def check_permission(
        self,
        requesting_agent_id: str,
        action: str,  # create_agent, edit_agent, delete_agent, create_doc, edit_doc, delete_doc
        target_agent_id: str = None
    ) -> bool:
        """
        Verificar si un agente tiene permiso para realizar una acción.

        Args:
            requesting_agent_id: ID del agente que solicita la acción
            action: Tipo de acción
            target_agent_id: ID del agente objetivo (si aplica)

        Returns:
            True si tiene permiso, False si no
        """
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT puede_crear_agentes, puede_editar_agentes, puede_eliminar_agentes,
                           puede_crear_documentos, puede_editar_documentos, puede_eliminar_documentos,
                           tipo
                    FROM agent_configs
                    WHERE agent_id = $1 AND es_activo = TRUE
                """, requesting_agent_id)

                if not row:
                    return False

                # Orquestadores tienen todos los permisos
                if row['tipo'] == 'orquestador':
                    return True

                permission_map = {
                    'create_agent': row['puede_crear_agentes'],
                    'edit_agent': row['puede_editar_agentes'],
                    'delete_agent': row['puede_eliminar_agentes'],
                    'create_doc': row['puede_crear_documentos'],
                    'edit_doc': row['puede_editar_documentos'],
                    'delete_doc': row['puede_eliminar_documentos'],
                }

                return permission_map.get(action, False)

        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False

    # =========================================================================
    # CRUD DE AGENTES
    # =========================================================================

    async def create_agent(
        self,
        request: AgentCreateRequest,
        created_by_agent: str = None,
        created_by_user: UUID = None
    ) -> Optional[Dict]:
        """
        Crear un nuevo agente.

        Args:
            request: Datos del agente a crear
            created_by_agent: ID del agente que crea (si aplica)
            created_by_user: UUID del usuario que crea (si aplica)

        Returns:
            Dict con el agente creado o None si falla
        """
        # Verificar permisos si es creado por otro agente
        if created_by_agent:
            has_permission = await self.check_permission(created_by_agent, 'create_agent')
            if not has_permission:
                logger.warning(f"Agent {created_by_agent} does not have permission to create agents")
                return None

        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                # Verificar que no exista
                exists = await conn.fetchval("""
                    SELECT EXISTS (SELECT 1 FROM agent_configs WHERE agent_id = $1)
                """, request.agent_id)

                if exists:
                    logger.warning(f"Agent {request.agent_id} already exists")
                    return None

                # Obtener UUID del agente padre si se especifica
                padre_uuid = None
                if request.agente_padre_id:
                    padre_uuid = await conn.fetchval("""
                        SELECT id FROM agent_configs WHERE agent_id = $1
                    """, request.agente_padre_id)

                # Crear el agente
                agent_id = await conn.fetchval("""
                    INSERT INTO agent_configs (
                        agent_id, nombre, rol, descripcion, personalidad, system_prompt,
                        tipo, capabilities, fases_activas, puede_bloquear, fases_bloqueo,
                        agente_padre_id, pcloud_path,
                        puede_crear_agentes, puede_editar_agentes, puede_eliminar_agentes,
                        puede_crear_documentos, puede_editar_documentos, puede_eliminar_documentos,
                        created_by
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                        $14, $15, $16, $17, $18, $19, $20
                    )
                    RETURNING id
                """,
                    request.agent_id, request.nombre, request.rol, request.descripcion,
                    request.personalidad, request.system_prompt, request.tipo,
                    json.dumps(request.capabilities or []),
                    json.dumps(request.fases_activas or []),
                    request.puede_bloquear,
                    json.dumps(request.fases_bloqueo or []),
                    padre_uuid, request.pcloud_path,
                    request.puede_crear_agentes, request.puede_editar_agentes,
                    request.puede_eliminar_agentes, request.puede_crear_documentos,
                    request.puede_editar_documentos, request.puede_eliminar_documentos,
                    created_by_user
                )

                # Registrar auditoría
                await self._audit_log(
                    conn, request.agent_id, 'CREATE',
                    new_values={
                        'agent_id': request.agent_id,
                        'nombre': request.nombre,
                        'rol': request.rol,
                        'tipo': request.tipo
                    },
                    changed_by_type='agent' if created_by_agent else 'user',
                    changed_by_id=str(created_by_user) if created_by_user else None,
                    changed_by_agent=created_by_agent
                )

                logger.info(f"Created agent {request.agent_id}")

                return {
                    'id': str(agent_id),
                    'agent_id': request.agent_id,
                    'nombre': request.nombre,
                    'rol': request.rol,
                    'tipo': request.tipo,
                    'created': True
                }

        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None

    async def update_agent(
        self,
        agent_id: str,
        request: AgentUpdateRequest,
        updated_by_agent: str = None,
        updated_by_user: UUID = None,
        reason: str = None
    ) -> Optional[Dict]:
        """
        Actualizar un agente existente.

        Args:
            agent_id: ID del agente a actualizar
            request: Cambios a aplicar
            updated_by_agent: ID del agente que actualiza
            updated_by_user: UUID del usuario que actualiza
            reason: Razón del cambio

        Returns:
            Dict con el agente actualizado o None si falla
        """
        # Verificar permisos
        if updated_by_agent:
            has_permission = await self.check_permission(updated_by_agent, 'edit_agent', agent_id)
            if not has_permission:
                logger.warning(f"Agent {updated_by_agent} does not have permission to edit agents")
                return None

        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                # Obtener valores actuales
                current = await conn.fetchrow("""
                    SELECT * FROM agent_configs WHERE agent_id = $1
                """, agent_id)

                if not current:
                    logger.warning(f"Agent {agent_id} not found")
                    return None

                # Construir UPDATE dinámico
                updates = []
                values = []
                changed_fields = []
                old_values = {}
                new_values = {}
                param_count = 1

                update_fields = [
                    ('nombre', request.nombre),
                    ('rol', request.rol),
                    ('descripcion', request.descripcion),
                    ('personalidad', request.personalidad),
                    ('system_prompt', request.system_prompt),
                    ('es_activo', request.es_activo),
                    ('pcloud_path', request.pcloud_path),
                    ('puede_crear_agentes', request.puede_crear_agentes),
                    ('puede_editar_agentes', request.puede_editar_agentes),
                    ('puede_eliminar_agentes', request.puede_eliminar_agentes),
                    ('puede_crear_documentos', request.puede_crear_documentos),
                    ('puede_editar_documentos', request.puede_editar_documentos),
                    ('puede_eliminar_documentos', request.puede_eliminar_documentos),
                ]

                for field_name, new_value in update_fields:
                    if new_value is not None:
                        updates.append(f"{field_name} = ${param_count}")
                        values.append(new_value)
                        param_count += 1
                        changed_fields.append(field_name)
                        old_values[field_name] = current[field_name]
                        new_values[field_name] = new_value

                # Campos JSON
                if request.capabilities is not None:
                    updates.append(f"capabilities = ${param_count}")
                    values.append(json.dumps(request.capabilities))
                    param_count += 1
                    changed_fields.append('capabilities')

                if request.fases_activas is not None:
                    updates.append(f"fases_activas = ${param_count}")
                    values.append(json.dumps(request.fases_activas))
                    param_count += 1
                    changed_fields.append('fases_activas')

                if request.fases_bloqueo is not None:
                    updates.append(f"fases_bloqueo = ${param_count}")
                    values.append(json.dumps(request.fases_bloqueo))
                    param_count += 1
                    changed_fields.append('fases_bloqueo')

                if request.puede_bloquear is not None:
                    updates.append(f"puede_bloquear = ${param_count}")
                    values.append(request.puede_bloquear)
                    param_count += 1
                    changed_fields.append('puede_bloquear')

                if not updates:
                    return {'agent_id': agent_id, 'updated': False, 'message': 'No changes'}

                # Incrementar versión
                updates.append(f"version = version + 1")

                # Ejecutar UPDATE
                values.append(agent_id)
                query = f"""
                    UPDATE agent_configs
                    SET {', '.join(updates)}
                    WHERE agent_id = ${param_count}
                    RETURNING version
                """

                new_version = await conn.fetchval(query, *values)

                # Registrar auditoría
                await self._audit_log(
                    conn, agent_id, 'UPDATE',
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields,
                    changed_by_type='agent' if updated_by_agent else 'user',
                    changed_by_id=str(updated_by_user) if updated_by_user else None,
                    changed_by_agent=updated_by_agent,
                    reason=reason
                )

                logger.info(f"Updated agent {agent_id} to version {new_version}")

                return {
                    'agent_id': agent_id,
                    'updated': True,
                    'version': new_version,
                    'changed_fields': changed_fields
                }

        except Exception as e:
            logger.error(f"Error updating agent: {e}")
            return None

    async def delete_agent(
        self,
        agent_id: str,
        deleted_by_agent: str = None,
        deleted_by_user: UUID = None,
        hard_delete: bool = False,
        reason: str = None
    ) -> bool:
        """
        Eliminar (desactivar) un agente.

        Args:
            agent_id: ID del agente a eliminar
            deleted_by_agent: ID del agente que elimina
            deleted_by_user: UUID del usuario que elimina
            hard_delete: Si True, elimina permanentemente (peligroso)
            reason: Razón de la eliminación

        Returns:
            True si se eliminó correctamente
        """
        # Verificar permisos
        if deleted_by_agent:
            has_permission = await self.check_permission(deleted_by_agent, 'delete_agent', agent_id)
            if not has_permission:
                logger.warning(f"Agent {deleted_by_agent} does not have permission to delete agents")
                return False

        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                # Obtener info actual para auditoría
                current = await conn.fetchrow("""
                    SELECT agent_id, nombre, rol, tipo FROM agent_configs WHERE agent_id = $1
                """, agent_id)

                if not current:
                    return False

                if hard_delete:
                    # Eliminación permanente (NO RECOMENDADO)
                    await conn.execute("""
                        DELETE FROM agent_configs WHERE agent_id = $1
                    """, agent_id)
                    action = 'DELETE'
                else:
                    # Soft delete (desactivar)
                    await conn.execute("""
                        UPDATE agent_configs SET es_activo = FALSE WHERE agent_id = $1
                    """, agent_id)
                    action = 'DEACTIVATE'

                # Registrar auditoría
                await self._audit_log(
                    conn, agent_id, action,
                    old_values=dict(current),
                    changed_by_type='agent' if deleted_by_agent else 'user',
                    changed_by_id=str(deleted_by_user) if deleted_by_user else None,
                    changed_by_agent=deleted_by_agent,
                    reason=reason
                )

                logger.info(f"{'Deleted' if hard_delete else 'Deactivated'} agent {agent_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False

    # =========================================================================
    # CRUD DE SUBAGENTES
    # =========================================================================

    async def create_subagent(
        self,
        request: SubagentCreateRequest,
        created_by_agent: str = None,
        created_by_user: UUID = None
    ) -> Optional[Dict]:
        """Crear un nuevo subagente."""
        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                # Verificar que no exista
                exists = await conn.fetchval("""
                    SELECT EXISTS (SELECT 1 FROM subagent_configs WHERE subagent_id = $1)
                """, request.subagent_id)

                if exists:
                    logger.warning(f"Subagent {request.subagent_id} already exists")
                    return None

                # Obtener UUID del padre
                padre_uuid = None
                if request.agente_padre_id:
                    padre_uuid = await conn.fetchval("""
                        SELECT id FROM agent_configs WHERE agent_id = $1
                    """, request.agente_padre_id)

                # Crear
                subagent_id = await conn.fetchval("""
                    INSERT INTO subagent_configs (
                        subagent_id, nombre, funcion, descripcion, system_prompt,
                        agente_padre_id, tipo, capabilities, input_schema, output_schema,
                        trigger_conditions, priority
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id
                """,
                    request.subagent_id, request.nombre, request.funcion,
                    request.descripcion, request.system_prompt, padre_uuid,
                    request.tipo, json.dumps(request.capabilities or []),
                    json.dumps(request.input_schema) if request.input_schema else None,
                    json.dumps(request.output_schema) if request.output_schema else None,
                    json.dumps(request.trigger_conditions or []),
                    request.priority
                )

                logger.info(f"Created subagent {request.subagent_id}")

                return {
                    'id': str(subagent_id),
                    'subagent_id': request.subagent_id,
                    'nombre': request.nombre,
                    'tipo': request.tipo,
                    'created': True
                }

        except Exception as e:
            logger.error(f"Error creating subagent: {e}")
            return None

    # =========================================================================
    # CRUD DE DOCUMENTOS
    # =========================================================================

    async def create_document(
        self,
        request: DocumentCreateRequest,
        created_by_agent: str = None,
        created_by_user: UUID = None
    ) -> Optional[Dict]:
        """Crear un documento para un agente."""
        # Verificar permisos
        if created_by_agent:
            has_permission = await self.check_permission(created_by_agent, 'create_doc')
            if not has_permission:
                logger.warning(f"Agent {created_by_agent} does not have permission to create documents")
                return None

        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                # Calcular checksum simple
                import hashlib
                checksum = hashlib.sha256(request.content.encode()).hexdigest()

                doc_id = await conn.fetchval("""
                    INSERT INTO agent_documents (
                        agent_id, document_type, title, content,
                        file_type, pcloud_path, checksum
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    request.agent_id, request.document_type, request.title,
                    request.content, request.file_type, request.pcloud_path, checksum
                )

                logger.info(f"Created document '{request.title}' for agent {request.agent_id}")

                return {
                    'id': str(doc_id),
                    'agent_id': request.agent_id,
                    'title': request.title,
                    'document_type': request.document_type,
                    'created': True
                }

        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return None

    async def update_document(
        self,
        document_id: UUID,
        content: str = None,
        title: str = None,
        updated_by_agent: str = None
    ) -> bool:
        """Actualizar un documento."""
        if updated_by_agent:
            has_permission = await self.check_permission(updated_by_agent, 'edit_doc')
            if not has_permission:
                return False

        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                updates = []
                values = []
                param_count = 1

                if content is not None:
                    import hashlib
                    checksum = hashlib.sha256(content.encode()).hexdigest()
                    updates.append(f"content = ${param_count}")
                    values.append(content)
                    param_count += 1
                    updates.append(f"checksum = ${param_count}")
                    values.append(checksum)
                    param_count += 1

                if title is not None:
                    updates.append(f"title = ${param_count}")
                    values.append(title)
                    param_count += 1

                if not updates:
                    return False

                values.append(document_id)
                await conn.execute(f"""
                    UPDATE agent_documents
                    SET {', '.join(updates)}
                    WHERE id = ${param_count}
                """, *values)

                return True

        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False

    async def delete_document(
        self,
        document_id: UUID,
        deleted_by_agent: str = None,
        hard_delete: bool = False
    ) -> bool:
        """Eliminar un documento."""
        if deleted_by_agent:
            has_permission = await self.check_permission(deleted_by_agent, 'delete_doc')
            if not has_permission:
                return False

        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                if hard_delete:
                    await conn.execute("""
                        DELETE FROM agent_documents WHERE id = $1
                    """, document_id)
                else:
                    await conn.execute("""
                        UPDATE agent_documents SET es_activo = FALSE WHERE id = $1
                    """, document_id)

                return True

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    # =========================================================================
    # AUDITORÍA
    # =========================================================================

    async def _audit_log(
        self,
        conn,
        agent_id: str,
        action: str,
        old_values: Dict = None,
        new_values: Dict = None,
        changed_fields: List[str] = None,
        changed_by_type: str = 'system',
        changed_by_id: str = None,
        changed_by_agent: str = None,
        reason: str = None
    ):
        """Registrar entrada en log de auditoría."""
        try:
            await conn.execute("""
                INSERT INTO agent_audit_log (
                    agent_id, action, old_values, new_values, changed_fields,
                    changed_by_type, changed_by_id, changed_by_agent, reason
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                agent_id, action,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                json.dumps(changed_fields) if changed_fields else None,
                changed_by_type, changed_by_id, changed_by_agent, reason
            )
        except Exception as e:
            logger.error(f"Error recording audit log: {e}")

    async def get_agent_audit_history(
        self,
        agent_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Obtener historial de cambios de un agente."""
        if not self._pool:
            return []

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM agent_audit_log
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, agent_id, limit)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting audit history: {e}")
            return []


# Singleton instance
_crud_instance: Optional[AgentCRUDService] = None


async def get_agent_crud_service() -> AgentCRUDService:
    """Obtener instancia singleton del servicio CRUD."""
    global _crud_instance
    if _crud_instance is None:
        _crud_instance = AgentCRUDService()
        await _crud_instance.initialize()
    return _crud_instance
