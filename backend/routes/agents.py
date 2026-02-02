from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from services.agent_service import AgentService, AGENT_CONFIGURATIONS
from services.drive_service import DriveService

router = APIRouter(prefix="/agents", tags=["agents"])
agent_service = AgentService()
drive_service = DriveService()

class AnalysisRequest(BaseModel):
    context: str
    query: str


@router.get("/", summary="List all agents")
async def list_agents():
    """
    Listar todos los agentes configurados en el sistema con sus personalidades.
    """
    agents = agent_service.list_agents()
    return {
        "success": True,
        "count": len(agents),
        "agents": agents
    }


@router.get("/{agent_id}", summary="Get agent info")
async def get_agent_info(agent_id: str):
    """
    Obtener información detallada de un agente específico.
    """
    info = agent_service.get_agent_info(agent_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "success": True,
        "agent_id": agent_id,
        "info": info
    }

@router.post("/{agent_id}/analyze", summary="Request analysis from specific agent")
async def analyze_with_agent(agent_id: str, request: AnalysisRequest):
    """
    Solicitar un análisis específico a un agente.
    
    Cada agente tiene su propia personalidad y modelo LLM:
    - A1_SPONSOR: GPT-5 para análisis estratégico
    - A2_PMO: Claude Sonnet para consolidación
    - A3_FISCAL: Claude Sonnet para análisis fiscal
    - A5_FINANZAS: GPT-5 para análisis financiero
    - PROVEEDOR_IA: GPT-5 para consultoría tecnológica
    """
    try:
        analysis = await agent_service.agent_analyze(
            agent_id, request.context, request.query
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "analysis": analysis
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactions/recent", summary="Get recent agent interactions")
async def get_recent_interactions():
    """
    Obtener las interacciones recientes entre agentes.
    """
    from services.database import db

    try:
        interactions = await db.agent_interactions.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(50).to_list(50)
        
        return {
            "success": True,
            "count": len(interactions),
            "interactions": interactions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/knowledge", summary="Get agent's knowledge base summary")
async def get_agent_knowledge(agent_id: str):
    """
    Obtiene un resumen del conocimiento disponible en Google Drive para un agente.
    
    Muestra:
    - Cantidad de archivos en su carpeta
    - Tipos de documentos
    - Lista de archivos disponibles
    - Enlaces a los documentos
    """
    try:
        # Verificar que el agente existe
        agent_info = agent_service.get_agent_info(agent_id)
        if not agent_info:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # Obtener folder_id
        folder_id = agent_info.get("drive_folder_id")
        if not folder_id:
            return {
                "success": False,
                "message": "Agent does not have a Drive folder configured",
                "agent": agent_info["name"]
            }
        
        # Obtener resumen de conocimiento
        knowledge_summary = await drive_service.get_agent_knowledge_summary(folder_id)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent_info["name"],
            "agent_role": agent_info["role"],
            "knowledge": knowledge_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
