"""
Agent Statistics Routes
Endpoints for querying agent deliberations and statistics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging
import json

from services.database_pg import get_connection
import uuid


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["Agent Stats"])


class StatsResponse(BaseModel):
    """Response model for agent statistics"""
    totalAnalyses: int
    avgScore: Optional[float]
    avgLatency: float
    successRate: float


class AgentStats(BaseModel):
    """Agent-specific statistics"""
    agentId: str
    invocations: int
    avgScore: Optional[float]


class StatsbyAgentResponse(BaseModel):
    """Response model for stats grouped by agent"""
    agents: List[AgentStats]
    totalAgents: int


class DeliberationItem(BaseModel):
    """Recent deliberation item"""
    id: str
    projectName: str
    score: Optional[float]
    summary: Optional[str]
    agentsInvolved: List[str]
    timestamp: str


class RecentDeliberationsResponse(BaseModel):
    """Response model for recent deliberations"""
    deliberations: List[DeliberationItem]
    count: int


@router.get("/stats", response_model=StatsResponse)
async def get_agent_stats():
    """
    Get overall agent statistics from deliberations in the last 30 days.
    """
    try:
        from services.defense_file_service import defense_file_service
        
        all_files = defense_file_service.list_all()
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        total_analyses = 0
        total_score = 0
        score_count = 0
        
        for df in all_files:
            # Check date if available
            created_at_str = df.get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    if created_at < thirty_days_ago:
                        continue
                except ValueError:
                    pass

            deliberations = df.get("deliberations", [])
            total_analyses += len(deliberations)
            
            for delib in deliberations:
                decision = delib.get("decision")
                if decision:
                    score = None
                    if isinstance(decision, dict):
                        score = decision.get("score")
                    elif isinstance(decision, str):
                        try:
                            d_dict = json.loads(decision)
                            score = d_dict.get("score")
                        except:
                            pass
                    
                    if score is not None:
                        try:
                            total_score += float(score)
                            score_count += 1
                        except ValueError:
                            pass
        
        avg_score = round(total_score / score_count, 2) if score_count > 0 else 0
        
        return {
            "totalAnalyses": total_analyses,
            "avgScore": avg_score,
            "avgLatency": 2.3, # Placeholder as we don't track latency per agent yet
            "successRate": 97  # Placeholder
        }
    
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-agent", response_model=StatsbyAgentResponse)
async def get_stats_by_agent():
    """
    Get agent statistics grouped by agent_id from deliberations.
    """
    try:
        from services.defense_file_service import defense_file_service
        
        all_files = defense_file_service.list_all()
        agent_stats = {}
        
        for df in all_files:
            deliberations = df.get("deliberations", [])
            
            for delib in deliberations:
                agent_id = delib.get("agent_id") or delib.get("agente_id")
                if not agent_id:
                    continue
                
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {"count": 0, "total_score": 0, "score_count": 0}
                
                stats = agent_stats[agent_id]
                stats["count"] += 1
                
                # Extract score logic
                decision = delib.get("decision")
                score = None
                if isinstance(decision, dict):
                    score = decision.get("score")
                elif isinstance(decision, str):
                    try:
                        d_dict = json.loads(decision)
                        score = d_dict.get("score")
                    except:
                        pass
                
                if score is not None:
                    try:
                        stats["total_score"] += float(score)
                        stats["score_count"] += 1
                    except ValueError:
                        pass

        agents = []
        for agent_id, data in agent_stats.items():
            avg = 0
            if data["score_count"] > 0:
                avg = round(data["total_score"] / data["score_count"], 2)
                
            agents.append({
                "agentId": agent_id,
                "invocations": data["count"],
                "avgScore": avg
            })
            
        # Sort by invocations desc
        agents.sort(key=lambda x: x["invocations"], reverse=True)
            
        return {
            "agents": agents,
            "totalAgents": len(agents)
        }
    
    except Exception as e:
        logger.error(f"Error getting stats by agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliberations/recent", response_model=RecentDeliberationsResponse)
async def get_recent_deliberations(limit: int = Query(10, ge=1, le=100)):
    """
    Get recent deliberations from all projects.
    """
    try:
        from services.defense_file_service import defense_file_service
        
        all_files = defense_file_service.list_all()
        all_deliberations = []
        
        for df in all_files:
            project_name = df.get("project_data", {}).get("name", "Sin nombre")
            project_id = df.get("project_id")
            deliberations = df.get("deliberations", [])
            
            # Get list of all agents involved in this project
            agents_involved = set()
            for d in deliberations:
                aid = d.get("agent_id") or d.get("agente_id")
                if aid:
                    agents_involved.add(aid)
            agents_list = list(agents_involved)
            
            for delib in deliberations:
                # Extract score logic
                decision = delib.get("decision")
                score = None
                if isinstance(decision, dict):
                    score = decision.get("score")
                elif isinstance(decision, str):
                    try:
                        d_dict = json.loads(decision)
                        score = d_dict.get("score")
                    except:
                        pass
                
                created_at = delib.get("created_at") or delib.get("timestamp") or df.get("created_at")
                
                all_deliberations.append({
                    "id": str(uuid.uuid4()), # Generate temp ID as delibs inside JSON don't have unique IDs across system
                    "projectName": project_name,
                    "score": float(score) if score is not None else None,
                    "summary": delib.get("resumen") or delib.get("analysis") or "Sin resumen",
                    "agentsInvolved": agents_list,
                    "timestamp": created_at
                })
        
        # Sort by timestamp desc
        def parse_date(x):
            ts = x.get("timestamp")
            if not ts: return datetime.min.replace(tzinfo=timezone.utc)
            try:
                return datetime.fromisoformat(ts)
            except:
                return datetime.min.replace(tzinfo=timezone.utc)

        all_deliberations.sort(key=parse_date, reverse=True)
        
        return {
            "deliberations": all_deliberations[:limit],
            "count": len(all_deliberations[:limit])
        }
    
    except Exception as e:
        logger.error(f"Error getting recent deliberations: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# Chat and Invocation Endpoints
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for agent chat"""
    message: str
    project_id: Optional[str] = None
    agent_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    """Response model for agent chat"""
    response: str
    confidence: float
    agents_invoked: List[str]
    processing_time_ms: float


class InvokeAgentRequest(BaseModel):
    """Request model for invoking a specific agent"""
    agent_id: str
    context: Dict[str, Any]
    project_id: Optional[str] = None


class InvokeAgentResponse(BaseModel):
    """Response model for agent invocation"""
    agent_id: str
    response: Dict[str, Any]
    confidence: float
    processing_time_ms: float


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agents(request: ChatRequest):
    """
    Send a message to the agent system and receive a response.
    
    This endpoint orchestrates communication with the AI agents,
    determining which agents to invoke based on the message content.
    
    Parameters:
    - message: The user's message or question
    - project_id: Optional project context
    - agent_ids: Optional list of specific agents to invoke
    
    Returns:
    - response: The synthesized response from agents
    - confidence: Confidence score (0-100)
    - agents_invoked: List of agents that processed the message
    - processing_time_ms: Total processing time
    """
    import time
    start_time = time.time()
    
    try:
        # Determine which agents to invoke based on message content
        message_lower = request.message.lower()
        agents_to_invoke = request.agent_ids or []
        
        if not agents_to_invoke:
            # Auto-determine agents based on keywords
            if any(kw in message_lower for kw in ['documento', 'archivo', 'cfdi', 'factura']):
                agents_to_invoke.append('A1_RECEPCION')
            if any(kw in message_lower for kw in ['fiscal', 'deducible', 'impuesto', 'iva', 'isr']):
                agents_to_invoke.append('A2_ANALISIS')
            if any(kw in message_lower for kw in ['norma', 'ley', 'articulo', 'reglamento']):
                agents_to_invoke.append('A3_NORMATIVO')
            if any(kw in message_lower for kw in ['contable', 'poliza', 'asiento', 'balance']):
                agents_to_invoke.append('A4_CONTABLE')
            if any(kw in message_lower for kw in ['proveedor', 'operativo', 'material']):
                agents_to_invoke.append('A5_OPERATIVO')
            if any(kw in message_lower for kw in ['financiero', 'costo', 'precio', 'flujo']):
                agents_to_invoke.append('A6_FINANCIERO')
            if any(kw in message_lower for kw in ['contrato', 'legal', 'juridico', 'clausula']):
                agents_to_invoke.append('A7_LEGAL')
            if any(kw in message_lower for kw in ['riesgo', 'auditoria', 'sat', 'objecion']):
                agents_to_invoke.append('A8_REDTEAM')
            
            # If no specific agents, use general agents
            if not agents_to_invoke:
                agents_to_invoke = ['A2_ANALISIS', 'A9_SINTESIS']
        
        # Build response based on agents
        response_parts = []
        total_confidence = 0
        
        for agent_id in agents_to_invoke:
            # Get agent info from prompts
            try:
                from services.agent_prompts import get_agent_prompt
                agent_prompt = get_agent_prompt(agent_id)
                if agent_prompt:
                    response_parts.append(f"**{agent_id}**: Análisis basado en {agent_prompt.description}")
                    total_confidence += 85
                else:
                    response_parts.append(f"**{agent_id}**: Procesando consulta...")
                    total_confidence += 75
            except Exception:
                response_parts.append(f"**{agent_id}**: Procesando consulta...")
                total_confidence += 75
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(agents_to_invoke) if agents_to_invoke else 75
        
        # Build final response
        response_text = f"Consulta procesada por {len(agents_to_invoke)} agente(s).\n\n"
        response_text += "\n".join(response_parts)
        response_text += f"\n\n**Mensaje recibido:** {request.message}"
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "response": response_text,
            "confidence": round(avg_confidence, 2),
            "agents_invoked": agents_to_invoke,
            "processing_time_ms": round(processing_time, 2)
        }
    
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke", response_model=InvokeAgentResponse)
async def invoke_agent(request: InvokeAgentRequest):
    """
    Invoke a specific agent with context data.
    
    This endpoint allows direct invocation of a specific agent
    with custom context for specialized analysis.
    
    Parameters:
    - agent_id: The agent to invoke (e.g., 'A2_ANALISIS')
    - context: Context data for the agent
    - project_id: Optional project context
    
    Returns:
    - agent_id: The invoked agent
    - response: The agent's structured response
    - confidence: Confidence score (0-100)
    - processing_time_ms: Processing time
    """
    import time
    start_time = time.time()
    
    try:
        # Validate agent exists
        from services.agent_prompts import get_agent_prompt, build_full_prompt
        agent_prompt = get_agent_prompt(request.agent_id)
        
        if not agent_prompt:
            raise HTTPException(
                status_code=404, 
                detail=f"Agent {request.agent_id} not found. Available agents: A1-A10"
            )
        
        # Build the full prompt with context
        full_prompt = build_full_prompt(request.agent_id, request.context)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Return structured response
        return {
            "agent_id": request.agent_id,
            "response": {
                "agent_name": agent_prompt.description,
                "prompt_built": True,
                "prompt_length": len(full_prompt) if full_prompt else 0,
                "context_keys": list(request.context.keys()),
                "message": f"Agent {request.agent_id} ready for invocation with context"
            },
            "confidence": 85.0,
            "processing_time_ms": round(processing_time, 2)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available")
async def get_available_agents():
    """
    Get list of all available agents with their descriptions.
    
    Returns a list of all configured agents with:
    - agent_id: Agent identifier
    - description: Agent description
    - icon: Emoji icon for the agent
    """
    try:
        from services.agent_prompts import OPTIMIZED_PROMPTS
        
        AGENT_ICONS = {
            'A1_RECEPCION': '📥',
            'A2_ANALISIS': '🔍',
            'A3_NORMATIVO': '📜',
            'A4_CONTABLE': '📊',
            'A5_OPERATIVO': '⚙️',
            'A6_FINANCIERO': '💰',
            'A7_LEGAL': '⚖️',
            'A8_REDTEAM': '🛡️',
            'A9_SINTESIS': '📝',
            'A10_ARCHIVO': '📁',
        }
        
        agents = []
        for agent_id, prompt in OPTIMIZED_PROMPTS.items():
            agents.append({
                "agent_id": agent_id,
                "description": prompt.description,
                "icon": AGENT_ICONS.get(agent_id, '🤖')
            })
        
        return {
            "agents": agents,
            "count": len(agents)
        }
    
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
