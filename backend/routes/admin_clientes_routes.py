"""
Rutas de administrador para gestión global de Clientes.
Solo accesible por administradores de plataforma.
Permite aprobar, rechazar, modificar clientes y gestionar documentos.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import os
import logging
import asyncpg
from jose import jwt, exceptions as jose_exceptions

from models.cliente import ClienteUpdate, ClienteResponse
from services.cliente_service import cliente_service
from services.documento_versionado_service import documento_versionado_service
from services.cliente_contexto_service import cliente_contexto_service
from services.deep_research_service import deep_research_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/clientes", tags=["admin-clientes"])

security = HTTPBearer(auto_error=False)
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    logger.error("CRITICAL: SECRET_KEY, SESSION_SECRET or JWT_SECRET_KEY must be configured")
    SECRET_KEY = None
ALGORITHM = "HS256"
DATABASE_URL = os.environ.get('DATABASE_URL', '')


class AprobarClienteRequest(BaseModel):
    notas: Optional[str] = None


class RechazarClienteRequest(BaseModel):
    motivo: str


async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar que el usuario sea administrador de plataforma"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    if not SECRET_KEY:
        raise HTTPException(status_code=500, detail="Configuración de seguridad no disponible")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role", "").lower()
        
        if role not in ["admin", "superadmin", "platform_admin"]:
            raise HTTPException(
                status_code=403, 
                detail="Acceso denegado. Se requieren permisos de administrador."
            )
        
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_db_pool() -> asyncpg.Pool:
    """Obtiene pool de conexiones a PostgreSQL"""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL no configurada")
    
    db_url = DATABASE_URL
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    return await asyncpg.create_pool(db_url, min_size=1, max_size=5, command_timeout=30)


@router.get("")
async def admin_list_clientes(
    estado: Optional[str] = Query(None, description="Filtrar por estado (pendiente/aprobado/rechazado/suspendido)"),
    search: Optional[str] = Query(None, description="Buscar por razón social, RFC o nombre comercial"),
    origen: Optional[str] = Query(None, description="Filtrar por origen del cliente"),
    desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=200, description="Registros por página"),
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Listar todos los clientes con filtros avanzados.
    Retorna lista de clientes con totales por estado y métricas.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            where_clauses = ["1=1"]
            params = []
            param_count = 0
            
            if estado:
                param_count += 1
                where_clauses.append(f"c.estado = ${param_count}")
                params.append(estado)
            
            if search:
                param_count += 1
                where_clauses.append(f"""
                    (c.nombre ILIKE ${param_count} OR 
                     c.rfc ILIKE ${param_count} OR 
                     c.razon_social ILIKE ${param_count})
                """)
                params.append(f"%{search}%")
            
            if origen:
                param_count += 1
                where_clauses.append(f"c.origen = ${param_count}")
                params.append(origen)
            
            if desde:
                param_count += 1
                where_clauses.append(f"c.created_at >= ${param_count}")
                params.append(datetime.strptime(desde, '%Y-%m-%d'))
            
            if hasta:
                param_count += 1
                where_clauses.append(f"c.created_at <= ${param_count}")
                params.append(datetime.strptime(hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
            
            where_sql = " AND ".join(where_clauses)
            offset = (page - 1) * limit
            
            clientes_query = f"""
                SELECT 
                    c.*,
                    (SELECT COUNT(*) FROM clientes_documentos d WHERE d.cliente_id = c.id AND d.activo = true) as total_documentos,
                    (SELECT COUNT(*) FROM clientes_interacciones i WHERE i.cliente_id = c.id) as total_interacciones,
                    (SELECT MAX(created_at) FROM clientes_interacciones i WHERE i.cliente_id = c.id) as ultima_interaccion
                FROM clientes c
                WHERE {where_sql}
                ORDER BY c.created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            params.extend([limit, offset])
            
            clientes = await conn.fetch(clientes_query, *params)
            
            total_query = f"SELECT COUNT(*) FROM clientes c WHERE {where_sql}"
            total = await conn.fetchval(total_query, *params[:-2])
            
            totales_query = """
                SELECT 
                    COALESCE(estado, 'pendiente') as estado,
                    COUNT(*) as count
                FROM clientes
                GROUP BY estado
            """
            totales_rows = await conn.fetch(totales_query)
            
            totales = {
                "pendiente": 0,
                "aprobado": 0,
                "rechazado": 0,
                "suspendido": 0
            }
            for row in totales_rows:
                if row['estado'] in totales:
                    totales[row['estado']] = row['count']
        
        await pool.close()
        
        clientes_list = []
        for c in clientes:
            cliente_dict = dict(c)
            for key, value in cliente_dict.items():
                if isinstance(value, datetime):
                    cliente_dict[key] = value.isoformat()
            clientes_list.append(cliente_dict)
        
        return {
            "clientes": clientes_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "totales_por_estado": totales,
            "filtros": {
                "estado": estado,
                "search": search,
                "origen": origen,
                "desde": desde,
                "hasta": hasta
            }
        }
        
    except asyncpg.exceptions.UndefinedTableError:
        return {
            "clientes": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0,
            "totales_por_estado": {"pendiente": 0, "aprobado": 0, "rechazado": 0, "suspendido": 0},
            "message": "Tabla clientes no existe, usando servicio alternativo"
        }
    except Exception as e:
        logger.warning(f"Error consultando PostgreSQL, usando MongoDB: {e}")
        clientes = await cliente_service.list_clientes(
            status=estado,
            search=search,
            skip=(page - 1) * limit,
            limit=limit
        )
        total = await cliente_service.count_clientes(status=estado)
        
        return {
            "clientes": clientes,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit if total else 0,
            "totales_por_estado": {"pendiente": 0, "aprobado": 0, "rechazado": 0, "suspendido": 0}
        }


@router.get("/{cliente_id}")
async def admin_get_cliente_complete(
    cliente_id: int,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Obtener información completa de un cliente.
    Incluye: datos del cliente, documentos actuales, historial (50), interacciones (20), contexto.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                "SELECT * FROM clientes WHERE id = $1",
                cliente_id
            )
            
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
            documentos = await conn.fetch(
                """
                SELECT * FROM clientes_documentos 
                WHERE cliente_id = $1 AND activo = true AND es_version_actual = true
                ORDER BY created_at DESC
                """,
                cliente_id
            )
            
            historial = await conn.fetch(
                """
                SELECT * FROM clientes_historial 
                WHERE cliente_id = $1 
                ORDER BY created_at DESC 
                LIMIT 50
                """,
                cliente_id
            )
            
            interacciones = await conn.fetch(
                """
                SELECT * FROM clientes_interacciones 
                WHERE cliente_id = $1 
                ORDER BY created_at DESC 
                LIMIT 20
                """,
                cliente_id
            )
            
            contexto = await conn.fetchrow(
                "SELECT * FROM clientes_contexto WHERE cliente_id = $1",
                cliente_id
            )
        
        await pool.close()
        
        def serialize_row(row):
            if not row:
                return None
            d = dict(row)
            for key, value in d.items():
                if isinstance(value, datetime):
                    d[key] = value.isoformat()
            return d
        
        return {
            "cliente": serialize_row(cliente),
            "documentos": [serialize_row(d) for d in documentos],
            "historial": [serialize_row(h) for h in historial],
            "interacciones": [serialize_row(i) for i in interacciones],
            "contexto": serialize_row(contexto)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo cliente {cliente_id}: {e}")
        cliente = await cliente_service.get_cliente(str(cliente_id))
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return {
            "cliente": cliente,
            "documentos": [],
            "historial": [],
            "interacciones": [],
            "contexto": None
        }


@router.post("/{cliente_id}/aprobar")
async def admin_aprobar_cliente(
    cliente_id: int,
    request: AprobarClienteRequest,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Aprobar un cliente.
    Actualiza estado='aprobado', aprobado_por, fecha_aprobacion.
    Registra en historial.
    """
    admin_id = admin.get("user_id") or admin.get("sub")
    now = datetime.utcnow()
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                "SELECT id, estado, nombre FROM clientes WHERE id = $1",
                cliente_id
            )
            
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
            estado_anterior = cliente['estado']
            
            notas_text = f"[APROBACIÓN] {request.notas}" if request.notas else None
            await conn.execute(
                """
                UPDATE clientes SET 
                    estado = 'aprobado',
                    aprobado_por = $1,
                    fecha_aprobacion = $2,
                    notas_internas = COALESCE(notas_internas || E'\n', '') || COALESCE($3, ''),
                    updated_at = $2
                WHERE id = $4
                """,
                admin_id,
                now,
                notas_text,
                cliente_id
            )
            
            await conn.execute(
                """
                INSERT INTO clientes_historial (
                    cliente_id, tipo_cambio, campo_modificado,
                    valor_anterior, valor_nuevo, descripcion,
                    origen, agente_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                cliente_id,
                "aprobacion",
                "estado",
                estado_anterior,
                "aprobado",
                f"Cliente aprobado por administrador. {request.notas or ''}".strip(),
                "admin_panel",
                admin_id,
                now
            )
        
        await pool.close()
        
        return {
            "success": True,
            "message": "Cliente aprobado exitosamente",
            "cliente_id": cliente_id,
            "estado": "aprobado",
            "aprobado_por": admin_id,
            "fecha_aprobacion": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aprobando cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al aprobar cliente: {str(e)}")


@router.post("/{cliente_id}/rechazar")
async def admin_rechazar_cliente(
    cliente_id: int,
    request: RechazarClienteRequest,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Rechazar un cliente.
    Requiere motivo de rechazo.
    Actualiza estado='rechazado', motivo_rechazo.
    Registra en historial.
    """
    if not request.motivo or len(request.motivo.strip()) < 5:
        raise HTTPException(status_code=400, detail="El motivo de rechazo es requerido (mínimo 5 caracteres)")
    
    admin_id = admin.get("user_id") or admin.get("sub")
    now = datetime.utcnow()
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                "SELECT id, estado, nombre FROM clientes WHERE id = $1",
                cliente_id
            )
            
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
            estado_anterior = cliente['estado']
            
            await conn.execute(
                """
                UPDATE clientes SET 
                    estado = 'rechazado',
                    motivo_rechazo = $1,
                    rechazado_por = $2,
                    fecha_rechazo = $3,
                    updated_at = $3
                WHERE id = $4
                """,
                request.motivo,
                admin_id,
                now,
                cliente_id
            )
            
            await conn.execute(
                """
                INSERT INTO clientes_historial (
                    cliente_id, tipo_cambio, campo_modificado,
                    valor_anterior, valor_nuevo, descripcion,
                    origen, agente_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                cliente_id,
                "rechazo",
                "estado",
                estado_anterior,
                "rechazado",
                f"Cliente rechazado. Motivo: {request.motivo}",
                "admin_panel",
                admin_id,
                now
            )
        
        await pool.close()
        
        return {
            "success": True,
            "message": "Cliente rechazado",
            "cliente_id": cliente_id,
            "estado": "rechazado",
            "motivo_rechazo": request.motivo,
            "rechazado_por": admin_id,
            "fecha_rechazo": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rechazando cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al rechazar cliente: {str(e)}")


@router.put("/{cliente_id}")
async def admin_update_cliente(
    cliente_id: int,
    update_data: ClienteUpdate,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Modificar campos de un cliente.
    Guarda snapshot en clientes_historial antes de modificar.
    """
    admin_id = admin.get("user_id") or admin.get("sub")
    now = datetime.utcnow()
    
    update_dict = update_data.dict(exclude_none=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            cliente_actual = await conn.fetchrow(
                "SELECT * FROM clientes WHERE id = $1",
                cliente_id
            )
            
            if not cliente_actual:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
            import json
            snapshot = {}
            for key, value in dict(cliente_actual).items():
                if isinstance(value, datetime):
                    snapshot[key] = value.isoformat()
                else:
                    snapshot[key] = value
            
            await conn.execute(
                """
                INSERT INTO clientes_historial (
                    cliente_id, tipo_cambio, campo_modificado,
                    valor_anterior, valor_nuevo, descripcion,
                    origen, agente_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                cliente_id,
                "modificacion",
                "multiple",
                json.dumps(snapshot),
                json.dumps(update_dict),
                f"Modificación por administrador. Campos: {', '.join(update_dict.keys())}",
                "admin_panel",
                admin_id,
                now
            )
            
            set_clauses = []
            params = []
            param_idx = 1
            
            for key, value in update_dict.items():
                set_clauses.append(f"{key} = ${param_idx}")
                params.append(value)
                param_idx += 1
            
            set_clauses.append(f"updated_at = ${param_idx}")
            params.append(now)
            param_idx += 1
            
            params.append(cliente_id)
            
            update_sql = f"""
                UPDATE clientes 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx}
                RETURNING *
            """
            
            updated = await conn.fetchrow(update_sql, *params)
        
        await pool.close()
        
        result = dict(updated) if updated else {}
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        
        return {
            "success": True,
            "message": "Cliente actualizado",
            "cliente": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando cliente {cliente_id}: {e}")
        cliente = await cliente_service.update_cliente(
            cliente_id=str(cliente_id),
            update_data=update_dict,
            empresa_id=None
        )
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return {"success": True, "cliente": cliente}


@router.get("/{cliente_id}/documentos/{doc_uuid}/versiones")
async def admin_get_document_versions(
    cliente_id: int,
    doc_uuid: str,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Obtener todas las versiones de un documento específico.
    """
    try:
        versiones = await documento_versionado_service.get_versiones(
            cliente_id=cliente_id,
            documento_uuid=doc_uuid
        )
        
        return {
            "documento_uuid": doc_uuid,
            "cliente_id": cliente_id,
            "total_versiones": len(versiones),
            "versiones": versiones
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo versiones del documento {doc_uuid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo versiones: {str(e)}")


@router.post("/{cliente_id}/documentos")
async def admin_upload_document(
    cliente_id: int,
    file: UploadFile = File(...),
    tipo_documento: Optional[str] = Form(None),
    categoria: Optional[str] = Form(None),
    subcategoria: Optional[str] = Form(None),
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Subir un documento a un cliente.
    Usa el servicio de documentos versionados.
    """
    admin_id = admin.get("user_id") or admin.get("sub")
    
    try:
        contenido = await file.read()
        
        resultado = await documento_versionado_service.subir_documento(
            cliente_id=cliente_id,
            nombre_archivo=file.filename,
            contenido=contenido,
            tipo_documento=tipo_documento,
            categoria=categoria,
            subcategoria=subcategoria,
            usuario=admin_id
        )
        
        return {
            "success": True,
            "message": resultado.get("mensaje", "Documento subido"),
            "documento": resultado
        }
        
    except Exception as e:
        logger.error(f"Error subiendo documento para cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir documento: {str(e)}")


@router.get("/{cliente_id}/contexto/actualizar")
async def admin_actualizar_contexto(
    cliente_id: int,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Trigger actualización del contexto evolutivo del cliente.
    Usa IA para analizar todos los datos y generar contexto actualizado.
    """
    try:
        await cliente_contexto_service.actualizar_contexto_evolutivo(cliente_id)
        
        return {
            "success": True,
            "message": f"Contexto evolutivo actualizado para cliente {cliente_id}",
            "cliente_id": cliente_id
        }
        
    except Exception as e:
        logger.error(f"Error actualizando contexto del cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando contexto: {str(e)}")


@router.get("/stats/general")
async def admin_clientes_stats(
    admin: dict = Depends(verify_admin)
):
    """[ADMIN] Estadísticas globales de clientes"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE estado = 'pendiente') as pendiente,
                    COUNT(*) FILTER (WHERE estado = 'aprobado') as aprobado,
                    COUNT(*) FILTER (WHERE estado = 'rechazado') as rechazado,
                    COUNT(*) FILTER (WHERE estado = 'suspendido') as suspendido
                FROM clientes
                """
            )
        
        await pool.close()
        
        return {
            "total": stats['total'] or 0,
            "pendiente": stats['pendiente'] or 0,
            "aprobado": stats['aprobado'] or 0,
            "rechazado": stats['rechazado'] or 0,
            "suspendido": stats['suspendido'] or 0
        }
        
    except Exception as e:
        logger.warning(f"Error obteniendo stats: {e}")
        total = await cliente_service.count_clientes()
        return {
            "total": total,
            "pendiente": 0,
            "aprobado": 0,
            "rechazado": 0,
            "suspendido": 0
        }


class DeepResearchClienteRequest(BaseModel):
    nombre: Optional[str] = None
    rfc: Optional[str] = None
    sitio_web: Optional[str] = None
    documento_texto: Optional[str] = None


@router.post("/deep-research")
async def admin_deep_research_cliente(
    request: DeepResearchClienteRequest,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Deep Research: Auto-completar perfil de cliente usando IA.
    
    Acepta uno o más de:
    - nombre: Nombre o razón social
    - rfc: RFC del cliente
    - sitio_web: URL del sitio web
    - documento_texto: Texto extraído de documento (CSF, acta, etc)
    
    Retorna datos auto-completados con niveles de confianza.
    """
    if not request.nombre and not request.rfc and not request.sitio_web and not request.documento_texto:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un dato: nombre, rfc, sitio_web o documento_texto"
        )
    
    logger.info(f"[ADMIN] Deep Research cliente: nombre={request.nombre}, rfc={request.rfc}")
    
    try:
        if request.sitio_web or (request.nombre and not request.documento_texto):
            resultado = await deep_research_service.investigar_empresa(
                sitio_web=request.sitio_web,
                rfc=request.rfc,
                nombre=request.nombre
            )
        else:
            resultado = await deep_research_service.investigar_empresa(
                nombre=request.nombre,
                rfc=request.rfc,
                documento_texto=request.documento_texto
            )
        
        return {
            "success": resultado.get("success", False),
            "data": resultado.get("datos_empresa") or resultado.get("data", {}),
            "confianza": resultado.get("confianza", {}),
            "fuentes": resultado.get("fuentes_consultadas", []),
            "tokens_usados": resultado.get("tokens_used", 0)
        }
        
    except Exception as e:
        logger.error(f"Error en Deep Research cliente: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la investigación: {str(e)}"
        )


@router.post("/{cliente_id}/autofill-ia")
async def admin_autofill_cliente(
    cliente_id: int,
    admin: dict = Depends(verify_admin)
):
    """
    [ADMIN] Auto-completar datos de cliente existente con IA.
    Usa los datos actuales del cliente para investigar y completar campos faltantes.
    """
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            cliente = await conn.fetchrow(
                "SELECT * FROM clientes WHERE id = $1",
                cliente_id
            )
            
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            
            cliente_dict = dict(cliente)
        
        await pool.close()
        
        resultado = await deep_research_service.investigar_empresa(
            nombre=cliente_dict.get("nombre") or cliente_dict.get("razon_social"),
            rfc=cliente_dict.get("rfc"),
            sitio_web=cliente_dict.get("sitio_web")
        )
        
        if resultado.get("success") and resultado.get("datos_empresa"):
            datos_nuevos = resultado.get("datos_empresa", {})
            
            campos_actualizados = {}
            campos_mapeados = {
                "razon_social": "razon_social",
                "direccion_fiscal": "direccion",
                "codigo_postal": "codigo_postal",
                "ciudad": "ciudad",
                "estado": "estado",
                "telefono": "telefono",
                "email": "email",
                "sitio_web": "sitio_web",
                "regimen_fiscal": "regimen_fiscal",
                "representante_legal": "representante_legal",
                "actividad_economica": "giro",
                "objeto_social": "objeto_social"
            }
            
            for campo_ia, campo_db in campos_mapeados.items():
                if datos_nuevos.get(campo_ia) and not cliente_dict.get(campo_db):
                    campos_actualizados[campo_db] = datos_nuevos[campo_ia]
            
            if campos_actualizados:
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    set_clauses = []
                    params = []
                    for idx, (campo, valor) in enumerate(campos_actualizados.items(), 1):
                        set_clauses.append(f"{campo} = ${idx}")
                        params.append(valor)
                    
                    params.append(cliente_id)
                    update_sql = f"""
                        UPDATE clientes 
                        SET {', '.join(set_clauses)}, updated_at = NOW()
                        WHERE id = ${len(params)}
                    """
                    await conn.execute(update_sql, *params)
                await pool.close()
            
            return {
                "success": True,
                "campos_actualizados": list(campos_actualizados.keys()),
                "datos_encontrados": datos_nuevos,
                "confianza": resultado.get("confianza", {})
            }
        
        return {
            "success": False,
            "message": "No se encontraron datos adicionales",
            "error": resultado.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en autofill cliente {cliente_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
