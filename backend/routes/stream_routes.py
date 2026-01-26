"""
SSE Stream Routes for Revisar.IA Multi-Agent Deliberation
Real-time event streaming for analysis progress updates
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from jose import jwt, exceptions as jose_exceptions

from services.event_stream import event_emitter

router = APIRouter(prefix="/analysis", tags=["Analysis Stream"])
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def verify_stream_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token for stream access - allows unauthenticated access for same-origin requests"""
    if not credentials:
        return None
    
    SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jose_exceptions.ExpiredSignatureError, jose_exceptions.JWTError):
        return None

KEEPALIVE_INTERVAL = 15


async def event_generator(
    project_id: str,
    request: Request
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for a project's analysis.
    Includes keepalive pings every 15 seconds.
    """
    queue = event_emitter.subscribe(project_id)
    logger.info(f"Cliente conectado al stream del proyecto {project_id}")
    
    try:
        initial_event = {
            "agent_id": "SYSTEM",
            "agent_name": "Sistema Revisar.IA",
            "status": "connected",
            "message": "Conexión establecida. Esperando eventos de análisis...",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id
        }
        yield f"event: connected\ndata: {json.dumps(initial_event, ensure_ascii=False)}\n\n"
        
        while True:
            if await request.is_disconnected():
                logger.info(f"Cliente desconectado del proyecto {project_id}")
                break
            
            try:
                event = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL)
                
                event_type = event.get("status", "message")
                event_data = json.dumps(event, ensure_ascii=False)
                
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                
                if event.get("status") in ["complete", "error"]:
                    if event.get("data", {}).get("final", False):
                        logger.info(f"Stream finalizado para proyecto {project_id}")
                        break
                        
            except asyncio.TimeoutError:
                ping_data = {
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                yield f"event: ping\ndata: {json.dumps(ping_data)}\n\n"
                
    except asyncio.CancelledError:
        logger.info(f"Stream cancelado para proyecto {project_id}")
    except Exception as e:
        logger.error(f"Error en stream para proyecto {project_id}: {e}")
        error_event = {
            "agent_id": "SYSTEM",
            "agent_name": "Sistema",
            "status": "error",
            "message": f"Error en la conexión: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    finally:
        event_emitter.unsubscribe(project_id, queue)
        logger.info(f"Suscripción removida para proyecto {project_id}")


@router.get("/stream/{project_id}")
async def stream_analysis_events(project_id: str, request: Request):
    """
    SSE endpoint that streams real-time analysis events for a project.
    
    Events include:
    - thinking: Agent is processing
    - rag_search: Agent is querying knowledge base
    - analyzing: Agent is analyzing project data
    - sending: Agent is sending analysis to next agent
    - auditing: Agent is generating audit trail
    - complete: Agent completed analysis
    - error: An error occurred
    - ping: Keepalive signal (every 15 seconds)
    
    Example event:
    ```
    event: analyzing
    data: {"agent_id": "A1_SPONSOR", "agent_name": "María Rodríguez", "status": "analyzing", "message": "Analizando razón de negocios...", "timestamp": "2025-12-01T03:10:00Z", "progress": 25}
    ```
    """
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    
    return StreamingResponse(
        event_generator(project_id, request),
        media_type="text/event-stream",
        headers=headers
    )


@router.get("/stream/{project_id}/status")
async def get_stream_status(project_id: str):
    """
    Get the current status of a project's event stream.
    Returns subscriber count and session information.
    """
    session_info = event_emitter.get_session_info(project_id)
    
    if session_info:
        return {
            "success": True,
            "active": True,
            **session_info
        }
    
    return {
        "success": True,
        "active": False,
        "project_id": project_id,
        "subscriber_count": 0,
        "message": "No hay sesión activa para este proyecto"
    }


@router.get("/streams")
async def get_active_streams():
    """
    Get information about all active streaming sessions.
    Useful for monitoring and debugging.
    """
    sessions = event_emitter.get_active_sessions()
    
    return {
        "success": True,
        "active_count": len(sessions),
        "sessions": sessions
    }


@router.post("/stream/{project_id}/test")
async def send_test_event(project_id: str):
    """
    Send a test event to verify streaming is working.
    Only for development/debugging purposes.
    """
    success = await event_emitter.emit(
        project_id=project_id,
        agent_id="SYSTEM",
        status="thinking",
        message="Evento de prueba - El streaming está funcionando correctamente",
        progress=50
    )
    
    if success:
        return {
            "success": True,
            "message": "Evento de prueba enviado",
            "project_id": project_id
        }
    
    return {
        "success": False,
        "message": "No hay suscriptores activos para este proyecto",
        "project_id": project_id
    }


@router.delete("/stream/{project_id}")
async def cleanup_stream(project_id: str):
    """
    Force cleanup of a project's streaming session.
    Disconnects all subscribers.
    """
    cleaned = event_emitter.cleanup_session(project_id)
    
    return {
        "success": cleaned,
        "project_id": project_id,
        "message": "Sesión limpiada" if cleaned else "No se encontró sesión activa"
    }
