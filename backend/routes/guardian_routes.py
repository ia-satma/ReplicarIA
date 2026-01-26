"""
Guardian Agent API Routes
Sistema de monitoreo y detección de bugs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import json
import logging
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guardian", tags=["Guardian Agent"])

_guardian_instance = None
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Obtiene o crea el pool de conexiones a PostgreSQL"""
    global _db_pool
    if _db_pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=503, detail="DATABASE_URL no configurado")
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5,
            command_timeout=30
        )
    return _db_pool


class BugUpdateRequest(BaseModel):
    estado: Optional[str] = None
    asignado_a: Optional[str] = None
    notas: Optional[str] = None


class GuardianStartResponse(BaseModel):
    success: bool
    message: str
    running: bool


@router.get("/status")
async def get_guardian_status():
    """
    GET /api/guardian/status
    Estado general del sistema de monitoreo
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_pruebas,
                    COUNT(*) FILTER (WHERE activo = TRUE) as pruebas_activas,
                    COUNT(*) FILTER (WHERE ultimo_resultado = 'ok') as exitosas,
                    COUNT(*) FILTER (WHERE ultimo_resultado = 'error') as con_error,
                    COUNT(*) FILTER (WHERE ultimo_resultado = 'critical') as criticas,
                    COUNT(*) FILTER (WHERE ultimo_resultado = 'warning') as advertencias
                FROM system_health_checks
            """)
            
            bugs_abiertos = await conn.fetchval("""
                SELECT COUNT(*) FROM detected_bugs
                WHERE estado NOT IN ('resuelto', 'cerrado')
            """)
            
            bugs_criticos = await conn.fetchval("""
                SELECT COUNT(*) FROM detected_bugs
                WHERE estado NOT IN ('resuelto', 'cerrado')
                AND severidad = 'critical'
            """)
            
            ultima_ejecucion = await conn.fetchval("""
                SELECT MAX(ultima_ejecucion) FROM system_health_checks
            """)
            
            global _guardian_instance
            guardian_running = _guardian_instance is not None and _guardian_instance.running
            
            total = stats['total_pruebas'] or 0
            exitosas = stats['exitosas'] or 0
            salud = round((exitosas / total * 100) if total > 0 else 100, 1)
            
            return {
                "success": True,
                "guardian_running": guardian_running,
                "salud_sistema": salud,
                "pruebas": {
                    "total": stats['total_pruebas'] or 0,
                    "activas": stats['pruebas_activas'] or 0,
                    "exitosas": stats['exitosas'] or 0,
                    "con_error": stats['con_error'] or 0,
                    "criticas": stats['criticas'] or 0,
                    "advertencias": stats['advertencias'] or 0
                },
                "bugs": {
                    "abiertos": bugs_abiertos or 0,
                    "criticos": bugs_criticos or 0
                },
                "ultima_ejecucion": ultima_ejecucion.isoformat() if ultima_ejecucion else None,
                "timestamp": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del guardian: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-checks")
async def list_health_checks():
    """
    GET /api/guardian/health-checks
    Lista todas las pruebas configuradas
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, categoria, nombre, descripcion, tipo_prueba,
                    configuracion, intervalo_minutos, ultima_ejecucion,
                    ultimo_resultado, ultimo_mensaje, tiempo_respuesta_ms,
                    total_ejecuciones, total_exitosas, total_fallidas,
                    racha_actual, activo, created_at, updated_at
                FROM system_health_checks
                ORDER BY 
                    CASE ultimo_resultado 
                        WHEN 'critical' THEN 1 
                        WHEN 'error' THEN 2 
                        WHEN 'warning' THEN 3
                        ELSE 4 
                    END,
                    categoria, nombre
            """)
            
            health_checks = []
            for row in rows:
                config = {}
                if row['configuracion']:
                    try:
                        config = json.loads(row['configuracion'])
                    except:
                        config = {}
                
                total = row['total_ejecuciones'] or 0
                exitosas = row['total_exitosas'] or 0
                tasa_exito = round((exitosas / total * 100) if total > 0 else 0, 1)
                
                health_checks.append({
                    "id": row['id'],
                    "categoria": row['categoria'],
                    "nombre": row['nombre'],
                    "descripcion": row['descripcion'],
                    "tipo_prueba": row['tipo_prueba'],
                    "configuracion": config,
                    "intervalo_minutos": row['intervalo_minutos'],
                    "ultima_ejecucion": row['ultima_ejecucion'].isoformat() if row['ultima_ejecucion'] else None,
                    "ultimo_resultado": row['ultimo_resultado'],
                    "ultimo_mensaje": row['ultimo_mensaje'],
                    "tiempo_respuesta_ms": row['tiempo_respuesta_ms'],
                    "estadisticas": {
                        "total_ejecuciones": total,
                        "total_exitosas": exitosas,
                        "total_fallidas": row['total_fallidas'] or 0,
                        "tasa_exito": tasa_exito,
                        "racha_actual": row['racha_actual'] or 0
                    },
                    "activo": row['activo'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "success": True,
                "total": len(health_checks),
                "health_checks": health_checks
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-checks/{check_id}/run")
async def run_health_check(check_id: int):
    """
    POST /api/guardian/health-checks/{id}/run
    Ejecutar una prueba manualmente
    """
    try:
        from services.agents.guardian_agent import GuardianAgent, PruebaConfig
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, categoria, nombre, descripcion, tipo_prueba, 
                       configuracion, intervalo_minutos, ultima_ejecucion,
                       ultimo_resultado, activo
                FROM system_health_checks
                WHERE id = $1
            """, check_id)
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Health check {check_id} no encontrado")
            
            config = {}
            if row['configuracion']:
                try:
                    config = json.loads(row['configuracion'])
                except:
                    config = {}
            
            prueba = PruebaConfig(
                id=row['id'],
                categoria=row['categoria'],
                nombre=row['nombre'],
                descripcion=row['descripcion'],
                tipo_prueba=row['tipo_prueba'],
                configuracion=config,
                intervalo_minutos=row['intervalo_minutos'],
                ultima_ejecucion=row['ultima_ejecucion'],
                ultimo_resultado=row['ultimo_resultado'],
                activo=row['activo']
            )
        
        guardian = GuardianAgent()
        await guardian._init_db_pool()
        guardian.http_client = None
        
        import httpx
        guardian.http_client = httpx.AsyncClient(timeout=30.0, verify=False)
        
        try:
            resultado = await guardian.ejecutar_prueba(prueba)
            await guardian.guardar_resultado(prueba, resultado)
            
            if resultado.status in ('error', 'critical'):
                bug_codigo = await guardian.crear_bug_si_nuevo(prueba, resultado)
            else:
                bug_codigo = None
        finally:
            if guardian.http_client:
                await guardian.http_client.aclose()
            await guardian._close_db_pool()
        
        return {
            "success": True,
            "prueba_id": check_id,
            "nombre": prueba.nombre,
            "resultado": {
                "status": resultado.status,
                "message": resultado.message,
                "tiempo_ms": resultado.tiempo_ms,
                "detalles": resultado.detalles
            },
            "bug_creado": bug_codigo,
            "ejecutado_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando health check {check_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs")
async def list_bugs(
    estado: Optional[str] = None,
    severidad: Optional[str] = None,
    categoria: Optional[str] = None,
    limit: int = 50
):
    """
    GET /api/guardian/bugs
    Lista bugs detectados con filtros opcionales
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT 
                    id, codigo, health_check_id, categoria, componente,
                    titulo, descripcion, error_message, severidad, estado,
                    es_regresion, bug_original_id, asignado_a,
                    veces_detectado, detectado_at, verificado_at, 
                    resuelto_at, notas, created_at, updated_at
                FROM detected_bugs
                WHERE 1=1
            """
            params = []
            param_idx = 1
            
            if estado:
                query += f" AND estado = ${param_idx}"
                params.append(estado)
                param_idx += 1
            
            if severidad:
                query += f" AND severidad = ${param_idx}"
                params.append(severidad)
                param_idx += 1
            
            if categoria:
                query += f" AND categoria = ${param_idx}"
                params.append(categoria)
                param_idx += 1
            
            query += f"""
                ORDER BY 
                    CASE severidad 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3
                        ELSE 4 
                    END,
                    detectado_at DESC
                LIMIT ${param_idx}
            """
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            bugs = []
            for row in rows:
                bugs.append({
                    "id": row['id'],
                    "codigo": row['codigo'],
                    "health_check_id": row['health_check_id'],
                    "categoria": row['categoria'],
                    "componente": row['componente'],
                    "titulo": row['titulo'],
                    "descripcion": row['descripcion'],
                    "error_message": row['error_message'],
                    "severidad": row['severidad'],
                    "estado": row['estado'],
                    "es_regresion": row['es_regresion'],
                    "bug_original_id": row['bug_original_id'],
                    "asignado_a": row['asignado_a'],
                    "veces_detectado": row['veces_detectado'] or 1,
                    "detectado_at": row['detectado_at'].isoformat() if row['detectado_at'] else None,
                    "verificado_at": row['verificado_at'].isoformat() if row['verificado_at'] else None,
                    "resuelto_at": row['resuelto_at'].isoformat() if row['resuelto_at'] else None,
                    "notas": row['notas'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            return {
                "success": True,
                "total": len(bugs),
                "filtros": {
                    "estado": estado,
                    "severidad": severidad,
                    "categoria": categoria,
                    "limit": limit
                },
                "bugs": bugs
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando bugs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bugs/{codigo}")
async def get_bug_detail(codigo: str):
    """
    GET /api/guardian/bugs/{codigo}
    Detalle de un bug específico
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            bug = await conn.fetchrow("""
                SELECT 
                    b.id, b.codigo, b.health_check_id, b.categoria, b.componente,
                    b.titulo, b.descripcion, b.error_message, b.severidad, b.estado,
                    b.es_regresion, b.bug_original_id, b.asignado_a,
                    b.veces_detectado, b.detectado_at, b.verificado_at, 
                    b.resuelto_at, b.notas, b.created_at, b.updated_at,
                    h.nombre as health_check_nombre,
                    h.tipo_prueba as health_check_tipo
                FROM detected_bugs b
                LEFT JOIN system_health_checks h ON b.health_check_id = h.id
                WHERE b.codigo = $1
            """, codigo)
            
            if not bug:
                raise HTTPException(status_code=404, detail=f"Bug {codigo} no encontrado")
            
            historial = await conn.fetch("""
                SELECT 
                    ejecutado_at, resultado, mensaje, tiempo_respuesta_ms, detalles
                FROM health_check_history
                WHERE health_check_id = $1
                ORDER BY ejecutado_at DESC
                LIMIT 20
            """, bug['health_check_id'])
            
            historial_list = []
            for h in historial:
                detalles = {}
                if h['detalles']:
                    try:
                        detalles = json.loads(h['detalles'])
                    except:
                        detalles = {}
                
                historial_list.append({
                    "ejecutado_at": h['ejecutado_at'].isoformat() if h['ejecutado_at'] else None,
                    "resultado": h['resultado'],
                    "mensaje": h['mensaje'],
                    "tiempo_respuesta_ms": h['tiempo_respuesta_ms'],
                    "detalles": detalles
                })
            
            bug_original = None
            if bug['bug_original_id']:
                original = await conn.fetchrow("""
                    SELECT codigo, titulo, resuelto_at FROM detected_bugs WHERE id = $1
                """, bug['bug_original_id'])
                if original:
                    bug_original = {
                        "codigo": original['codigo'],
                        "titulo": original['titulo'],
                        "resuelto_at": original['resuelto_at'].isoformat() if original['resuelto_at'] else None
                    }
            
            return {
                "success": True,
                "bug": {
                    "id": bug['id'],
                    "codigo": bug['codigo'],
                    "health_check_id": bug['health_check_id'],
                    "health_check_nombre": bug['health_check_nombre'],
                    "health_check_tipo": bug['health_check_tipo'],
                    "categoria": bug['categoria'],
                    "componente": bug['componente'],
                    "titulo": bug['titulo'],
                    "descripcion": bug['descripcion'],
                    "error_message": bug['error_message'],
                    "severidad": bug['severidad'],
                    "estado": bug['estado'],
                    "es_regresion": bug['es_regresion'],
                    "bug_original": bug_original,
                    "asignado_a": bug['asignado_a'],
                    "veces_detectado": bug['veces_detectado'] or 1,
                    "detectado_at": bug['detectado_at'].isoformat() if bug['detectado_at'] else None,
                    "verificado_at": bug['verificado_at'].isoformat() if bug['verificado_at'] else None,
                    "resuelto_at": bug['resuelto_at'].isoformat() if bug['resuelto_at'] else None,
                    "notas": bug['notas'],
                    "created_at": bug['created_at'].isoformat() if bug['created_at'] else None,
                    "updated_at": bug['updated_at'].isoformat() if bug['updated_at'] else None
                },
                "historial_pruebas": historial_list
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo bug {codigo}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/bugs/{codigo}")
async def update_bug(codigo: str, update: BugUpdateRequest):
    """
    PATCH /api/guardian/bugs/{codigo}
    Actualizar estado de bug
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchval(
                "SELECT id FROM detected_bugs WHERE codigo = $1", codigo
            )
            if not existing:
                raise HTTPException(status_code=404, detail=f"Bug {codigo} no encontrado")
            
            updates = []
            params = []
            param_idx = 1
            
            if update.estado is not None:
                valid_estados = ['detectado', 'en_revision', 'en_progreso', 'verificando', 'resuelto', 'cerrado']
                if update.estado not in valid_estados:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Estado inválido. Válidos: {', '.join(valid_estados)}"
                    )
                updates.append(f"estado = ${param_idx}")
                params.append(update.estado)
                param_idx += 1
                
                if update.estado == 'resuelto':
                    updates.append(f"resuelto_at = NOW()")
                elif update.estado == 'verificando':
                    updates.append(f"verificado_at = NOW()")
            
            if update.asignado_a is not None:
                updates.append(f"asignado_a = ${param_idx}")
                params.append(update.asignado_a)
                param_idx += 1
            
            if update.notas is not None:
                updates.append(f"notas = ${param_idx}")
                params.append(update.notas)
                param_idx += 1
            
            if not updates:
                raise HTTPException(status_code=400, detail="No hay campos para actualizar")
            
            updates.append("updated_at = NOW()")
            params.append(codigo)
            
            query = f"""
                UPDATE detected_bugs
                SET {', '.join(updates)}
                WHERE codigo = ${param_idx}
                RETURNING id, codigo, estado, asignado_a, notas, updated_at
            """
            
            result = await conn.fetchrow(query, *params)
            
            return {
                "success": True,
                "message": f"Bug {codigo} actualizado",
                "bug": {
                    "id": result['id'],
                    "codigo": result['codigo'],
                    "estado": result['estado'],
                    "asignado_a": result['asignado_a'],
                    "notas": result['notas'],
                    "updated_at": result['updated_at'].isoformat() if result['updated_at'] else None
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando bug {codigo}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """
    GET /api/guardian/metrics
    Métricas generales del sistema
    """
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            pruebas_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    SUM(total_ejecuciones) as total_ejecuciones,
                    SUM(total_exitosas) as total_exitosas,
                    SUM(total_fallidas) as total_fallidas,
                    AVG(tiempo_respuesta_ms) as avg_tiempo_ms,
                    MAX(tiempo_respuesta_ms) as max_tiempo_ms
                FROM system_health_checks
                WHERE activo = TRUE
            """)
            
            bugs_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_bugs,
                    COUNT(*) FILTER (WHERE estado NOT IN ('resuelto', 'cerrado')) as abiertos,
                    COUNT(*) FILTER (WHERE estado = 'resuelto') as resueltos,
                    COUNT(*) FILTER (WHERE estado = 'cerrado') as cerrados,
                    COUNT(*) FILTER (WHERE severidad = 'critical') as criticos,
                    COUNT(*) FILTER (WHERE severidad = 'high') as altos,
                    COUNT(*) FILTER (WHERE es_regresion = TRUE) as regresiones
                FROM detected_bugs
            """)
            
            bugs_por_categoria = await conn.fetch("""
                SELECT categoria, COUNT(*) as count
                FROM detected_bugs
                WHERE estado NOT IN ('resuelto', 'cerrado')
                GROUP BY categoria
                ORDER BY count DESC
            """)
            
            ultimas_ejecuciones = await conn.fetch("""
                SELECT 
                    h.nombre,
                    h.ultimo_resultado,
                    h.tiempo_respuesta_ms,
                    h.ultima_ejecucion
                FROM system_health_checks h
                WHERE h.ultima_ejecucion IS NOT NULL
                ORDER BY h.ultima_ejecucion DESC
                LIMIT 10
            """)
            
            total_ejecuciones = pruebas_stats['total_ejecuciones'] or 0
            total_exitosas = pruebas_stats['total_exitosas'] or 0
            uptime = round((total_exitosas / total_ejecuciones * 100) if total_ejecuciones > 0 else 100, 2)
            
            mttr = await conn.fetchval("""
                SELECT AVG(EXTRACT(EPOCH FROM (resuelto_at - detectado_at)) / 3600)
                FROM detected_bugs
                WHERE resuelto_at IS NOT NULL
            """)
            
            return {
                "success": True,
                "metricas": {
                    "uptime_porcentaje": uptime,
                    "mttr_horas": round(mttr, 2) if mttr else None,
                    "pruebas": {
                        "total_configuradas": pruebas_stats['total'] or 0,
                        "total_ejecuciones": total_ejecuciones,
                        "total_exitosas": total_exitosas,
                        "total_fallidas": pruebas_stats['total_fallidas'] or 0,
                        "tiempo_promedio_ms": round(pruebas_stats['avg_tiempo_ms'] or 0, 2),
                        "tiempo_maximo_ms": pruebas_stats['max_tiempo_ms'] or 0
                    },
                    "bugs": {
                        "total": bugs_stats['total_bugs'] or 0,
                        "abiertos": bugs_stats['abiertos'] or 0,
                        "resueltos": bugs_stats['resueltos'] or 0,
                        "cerrados": bugs_stats['cerrados'] or 0,
                        "criticos": bugs_stats['criticos'] or 0,
                        "altos": bugs_stats['altos'] or 0,
                        "regresiones": bugs_stats['regresiones'] or 0
                    },
                    "bugs_por_categoria": [
                        {"categoria": row['categoria'], "count": row['count']}
                        for row in bugs_por_categoria
                    ]
                },
                "ultimas_ejecuciones": [
                    {
                        "nombre": row['nombre'],
                        "resultado": row['ultimo_resultado'],
                        "tiempo_ms": row['tiempo_respuesta_ms'],
                        "ejecutado_at": row['ultima_ejecucion'].isoformat() if row['ultima_ejecucion'] else None
                    }
                    for row in ultimas_ejecuciones
                ],
                "timestamp": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=GuardianStartResponse)
async def start_guardian():
    """
    POST /api/guardian/start
    Iniciar el agente guardian
    """
    global _guardian_instance
    
    try:
        from services.agents.guardian_agent import GuardianAgent
        
        if _guardian_instance is not None and _guardian_instance.running:
            return GuardianStartResponse(
                success=True,
                message="Guardian ya está corriendo",
                running=True
            )
        
        _guardian_instance = GuardianAgent()
        await _guardian_instance.iniciar()
        
        logger.info("🛡️ Guardian Agent iniciado via API")
        
        return GuardianStartResponse(
            success=True,
            message="Guardian Agent iniciado exitosamente",
            running=True
        )
    except Exception as e:
        logger.error(f"Error iniciando Guardian: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=GuardianStartResponse)
async def stop_guardian():
    """
    POST /api/guardian/stop
    Detener el agente guardian
    """
    global _guardian_instance
    
    try:
        if _guardian_instance is None or not _guardian_instance.running:
            return GuardianStartResponse(
                success=True,
                message="Guardian no está corriendo",
                running=False
            )
        
        await _guardian_instance.detener()
        _guardian_instance = None
        
        logger.info("🛡️ Guardian Agent detenido via API")
        
        return GuardianStartResponse(
            success=True,
            message="Guardian Agent detenido exitosamente",
            running=False
        )
    except Exception as e:
        logger.error(f"Error deteniendo Guardian: {e}")
        raise HTTPException(status_code=500, detail=str(e))
