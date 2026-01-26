"""
Documentation API Routes for Revisar.IA Platform.

Provides endpoints to access agent inventory, phases, pillars, and documentation snapshots.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from documentation import (
    AgentInventoryItem,
    PhaseModel,
    PillarModel,
    DocumentationSnapshot
)
from documentation.doc_agent import doc_agent_service

router = APIRouter(prefix="/docs", tags=["Documentation"])


class SnapshotCreateRequest(BaseModel):
    changelog: Optional[str] = None


class SnapshotSummary(BaseModel):
    snapshot_id: str
    version: str
    created_at: str
    created_by: str
    agent_count: int
    phase_count: int
    pillar_count: int


class InventoryResponse(BaseModel):
    total_agents: int
    principal_agents: int
    subagents: int
    blocking_agents: int
    agents: List[AgentInventoryItem]


class SystemOverview(BaseModel):
    total_agents: int
    total_phases: int
    total_pillars: int
    hard_locks: List[str]
    blocking_agents: List[str]
    version: str


@router.get("/overview", response_model=SystemOverview)
async def get_system_overview():
    """Get a high-level overview of the Revisar.IA system."""
    agents = await doc_agent_service.get_agent_inventory()
    phases = await doc_agent_service.get_phases_documentation()
    pillars = await doc_agent_service.get_pillars_documentation()
    
    hard_locks = [p.phase_id for p in phases if p.is_hard_lock]
    blocking_agents = [a.agent_id for a in agents if a.can_block]
    
    return SystemOverview(
        total_agents=len(agents),
        total_phases=len(phases),
        total_pillars=len(pillars),
        hard_locks=hard_locks,
        blocking_agents=blocking_agents,
        version="4.0.0"
    )


@router.get("/inventory", response_model=InventoryResponse)
async def get_full_inventory():
    """Get full agent inventory including all agents and subagents."""
    agents = await doc_agent_service.get_agent_inventory()
    
    principal_count = sum(1 for a in agents if a.type.value == "principal")
    subagent_count = sum(1 for a in agents if a.type.value == "subagent")
    blocking_count = sum(1 for a in agents if a.can_block)
    
    return InventoryResponse(
        total_agents=len(agents),
        principal_agents=principal_count,
        subagents=subagent_count,
        blocking_agents=blocking_count,
        agents=agents
    )


@router.get("/agents/{agent_id}", response_model=AgentInventoryItem)
async def get_agent_details(agent_id: str):
    """Get detailed information about a specific agent."""
    agent = await doc_agent_service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent


@router.get("/agents/{agent_id}/markdown")
async def get_agent_markdown(agent_id: str):
    """Get markdown documentation for a specific agent."""
    agent = await doc_agent_service.get_agent_by_id(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    markdown = doc_agent_service.generate_agent_markdown(agent)
    
    return {"agent_id": agent_id, "markdown": markdown}


@router.get("/phases", response_model=List[PhaseModel])
async def get_phases_documentation():
    """Get all phases documentation."""
    return await doc_agent_service.get_phases_documentation()


@router.get("/phases/{phase_id}", response_model=PhaseModel)
async def get_phase_details(phase_id: str):
    """Get details about a specific phase."""
    phases = await doc_agent_service.get_phases_documentation()
    
    for phase in phases:
        if phase.phase_id == phase_id:
            return phase
    
    raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found")


@router.get("/pillars", response_model=List[PillarModel])
async def get_pillars_documentation():
    """Get all pillars documentation."""
    return await doc_agent_service.get_pillars_documentation()


@router.get("/pillars/{pillar_id}", response_model=PillarModel)
async def get_pillar_details(pillar_id: str):
    """Get details about a specific pillar."""
    pillars = await doc_agent_service.get_pillars_documentation()
    
    for pillar in pillars:
        if pillar.pillar_id == pillar_id:
            return pillar
    
    raise HTTPException(status_code=404, detail=f"Pillar {pillar_id} not found")


@router.post("/snapshot", response_model=DocumentationSnapshot)
async def create_documentation_snapshot(request: SnapshotCreateRequest = None):
    """Create a new documentation snapshot."""
    snapshot = await doc_agent_service.generate_full_documentation()
    
    if request and request.changelog:
        snapshot.changelog = request.changelog
    
    return snapshot


@router.get("/snapshots", response_model=List[SnapshotSummary])
async def list_snapshots():
    """List all documentation snapshots."""
    snapshots = doc_agent_service.get_snapshots()
    
    summaries = []
    for snapshot in snapshots:
        summaries.append(SnapshotSummary(
            snapshot_id=snapshot.snapshot_id,
            version=snapshot.version,
            created_at=snapshot.created_at.isoformat(),
            created_by=snapshot.created_by,
            agent_count=len(snapshot.agents),
            phase_count=len(snapshot.phases),
            pillar_count=len(snapshot.pillars)
        ))
    
    return summaries


@router.get("/snapshots/{snapshot_id}", response_model=DocumentationSnapshot)
async def get_snapshot(snapshot_id: str):
    """Get a specific documentation snapshot."""
    snapshots = doc_agent_service.get_snapshots()
    
    for snapshot in snapshots:
        if snapshot.snapshot_id == snapshot_id:
            return snapshot
    
    raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")


@router.get("/hard-locks")
async def get_hard_locks():
    """Get information about all hard lock phases."""
    phases = await doc_agent_service.get_phases_documentation()
    
    hard_locks = []
    for phase in phases:
        if phase.is_hard_lock:
            hard_locks.append({
                "phase_id": phase.phase_id,
                "name": phase.name,
                "lock_condition": phase.lock_condition,
                "required_agents": phase.required_agents
            })
    
    return {
        "total_hard_locks": len(hard_locks),
        "hard_locks": hard_locks
    }


@router.get("/blocking-agents")
async def get_blocking_agents():
    """Get list of agents that can block project advancement."""
    agents = await doc_agent_service.get_agent_inventory()
    
    blocking = []
    for agent in agents:
        if agent.can_block:
            blocking_capabilities = [
                {"id": c.id, "name": c.name, "description": c.description}
                for c in agent.capabilities if c.can_block
            ]
            blocking.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "phases": agent.phases,
                "blocking_capabilities": blocking_capabilities,
                "controls": [{"id": c.id, "name": c.name, "phase": c.phase, "condition": c.condition} for c in agent.controls]
            })
    
    return {
        "total_blocking_agents": len(blocking),
        "agents": blocking
    }
