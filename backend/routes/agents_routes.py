"""
Rutas API para el Sistema de Agentes Autónomos
Endpoints para monitoreo, control y reportes del sistema de auto-reparación.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import logging
from jose import jwt, exceptions as jose_exceptions

from agents.orchestrator import orchestrator
from agents.health.monitor import health_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

security = HTTPBearer(auto_error=False)
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    logger.warning("No JWT secret configured - agents admin endpoints will be disabled")


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Solo administradores pueden acceder a estos endpoints"""
    if not SECRET_KEY:
        raise HTTPException(status_code=503, detail="Servicio no configurado")
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role", "").lower()
        if role not in ["admin", "superadmin", "platform_admin"]:
            raise HTTPException(status_code=403, detail="Solo administradores pueden acceder")
        return payload
    except jose_exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jose_exceptions.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/status")
async def get_agents_status():
    """
    Obtener estado del sistema de agentes.
    No requiere autenticación para monitoreo básico.
    """
    return {
        "success": True,
        "orchestrator": orchestrator.get_status(),
        "timestamp": orchestrator._status.last_cycle.isoformat() if orchestrator._status.last_cycle else None
    }


@router.get("/health")
async def get_health_report():
    """
    Ejecutar health check completo y retornar reporte.
    No requiere autenticación para monitoreo de salud.
    """
    try:
        report = await health_monitor.check_all()
        return {
            "success": True,
            "report": report.to_dict()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/quick")
async def quick_health_check():
    """
    Health check rápido - solo estado básico.
    """
    last_report = health_monitor.get_last_report()
    if last_report:
        return {
            "status": last_report.get("status", "unknown"),
            "summary": last_report.get("summary", {}),
            "timestamp": last_report.get("timestamp")
        }
    
    report = await health_monitor.check_all()
    return {
        "status": report.status.value,
        "summary": report.to_dict().get("summary", {}),
        "timestamp": report.timestamp.isoformat()
    }


@router.post("/orchestrator/start", dependencies=[Depends(get_admin_user)])
async def start_orchestrator(
    background_tasks: BackgroundTasks,
    interval_minutes: int = 5
):
    """
    Iniciar el orquestador de agentes.
    Solo administradores.
    """
    if orchestrator._status.is_running:
        return {
            "success": False,
            "message": "El orquestador ya está corriendo",
            "status": orchestrator.get_status()
        }
    
    background_tasks.add_task(orchestrator.start, interval_minutes)
    
    return {
        "success": True,
        "message": f"Orquestador iniciado con ciclo de {interval_minutes} minutos",
        "status": orchestrator.get_status()
    }


@router.post("/orchestrator/stop", dependencies=[Depends(get_admin_user)])
async def stop_orchestrator():
    """
    Detener el orquestador de agentes.
    Solo administradores.
    """
    orchestrator.stop()
    
    return {
        "success": True,
        "message": "Orquestador detenido",
        "status": orchestrator.get_status()
    }


@router.post("/orchestrator/run-cycle", dependencies=[Depends(get_admin_user)])
async def run_single_cycle():
    """
    Ejecutar un ciclo de mantenimiento manualmente.
    Solo administradores.
    """
    try:
        reports = await orchestrator.run_cycle()
        return {
            "success": True,
            "message": f"Ciclo completado con {len(reports)} reportes",
            "reports": [
                {
                    "agent_id": r.agent_id,
                    "status": r.status,
                    "issues_count": len(r.issues)
                }
                for r in reports
            ]
        }
    except Exception as e:
        logger.error(f"Error ejecutando ciclo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/history")
async def get_reports_history(limit: int = 10):
    """
    Obtener historial de reportes de agentes.
    """
    return {
        "success": True,
        "reports": orchestrator.get_reports_history(limit)
    }


@router.get("/dashboard")
async def get_agents_dashboard():
    """
    Dashboard completo del sistema de agentes.
    """
    status = orchestrator.get_status()
    last_report = health_monitor.get_last_report()
    history = orchestrator.get_reports_history(5)
    
    return {
        "success": True,
        "orchestrator": status,
        "last_health_report": last_report,
        "recent_reports": history,
        "agents": [
            {
                "id": "HEALTH_MONITOR",
                "name": "Monitor de Salud",
                "description": "Monitorea la salud del sistema: BD, endpoints, servicios",
                "status": "active" if status.get("is_running") else "inactive"
            },
            {
                "id": "CODE_REPAIRER",
                "name": "Reparador de Código",
                "description": "Detecta y sugiere reparaciones de código",
                "status": "planned"
            },
            {
                "id": "DOCS_KEEPER",
                "name": "Documentador",
                "description": "Mantiene documentación actualizada",
                "status": "planned"
            }
        ]
    }


from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[str] = None
    target_agents: Optional[List[str]] = None
    empresa_id: Optional[str] = None


@router.get("/fiscal/list")
async def list_fiscal_agents():
    """Lista los 10 agentes fiscales especializados."""
    from services.agent_orchestrator import AGENTS_CONFIG
    
    return {
        "agents": [
            {
                "id": agent_id,
                "name": config["name"],
                "role": config["role"],
                "capabilities": config["capabilities"],
            }
            for agent_id, config in AGENTS_CONFIG.items()
        ],
        "total": len(AGENTS_CONFIG),
    }


@router.post("/fiscal/chat")
async def chat_with_fiscal_agents(request: ChatRequest):
    """Envía un mensaje a los agentes fiscales."""
    from services.agent_orchestrator import get_orchestrator
    
    fiscal_orchestrator = get_orchestrator()
    
    result = await fiscal_orchestrator.process_request(
        empresa_id=request.empresa_id or "demo_tenant",
        project_id=request.project_id or "general",
        user_id="demo_user",
        user_message=request.message,
        target_agents=request.target_agents,
    )
    
    return result


@router.get("/fiscal/{agent_id}")
async def get_fiscal_agent_info(agent_id: str):
    """Obtiene información de un agente fiscal específico."""
    from services.agent_orchestrator import AGENTS_CONFIG
    
    if agent_id not in AGENTS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Agente {agent_id} no encontrado")
    
    config = AGENTS_CONFIG[agent_id]
    return {
        "id": agent_id,
        "name": config["name"],
        "role": config["role"],
        "capabilities": config["capabilities"],
    }
