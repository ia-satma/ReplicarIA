from fastapi import APIRouter, Body, HTTPException
from services.orchestrator import analyze as analyze_fn

router = APIRouter(prefix="/agent", tags=["Agent Analyze"])

@router.post('/analyze')
async def analyze_endpoint(payload: dict = Body(...)):
    agent_id = (payload or {}).get('agent_id') or (payload or {}).get('agentId')
    text = (payload or {}).get('text') or (payload or {}).get('query')
    
    if not agent_id or not text:
        raise HTTPException(status_code=400, detail='Faltan agent_id y text')
    
    result = await analyze_fn(agent_id=agent_id, user_text=text)
    
    return {
        "success": True,
        **result
    }