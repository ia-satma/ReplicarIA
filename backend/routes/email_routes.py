"""
Email API Routes for Revisar.ia Multi-Agent System
Handles agent email communication endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import logging

from services.dreamhost_email_service import email_service, AGENT_EMAILS, AGENT_NAMES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])


class SendEmailRequest(BaseModel):
    from_agent_id: str
    to_email: str
    subject: str
    body: str
    cc_emails: Optional[List[str]] = None
    html_body: Optional[str] = None


class AgentToAgentRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    subject: str
    body: str
    cc_agent_ids: Optional[List[str]] = None
    project_id: Optional[str] = None


class ProviderEmailRequest(BaseModel):
    from_agent_id: str
    provider_email: str
    subject: str
    body: str
    project_id: Optional[str] = None
    cc_pmo: bool = True


@router.get("/status")
async def get_email_status():
    """Check email service status"""
    return {
        "initialized": email_service.initialized,
        "smtp_host": email_service.smtp_host,
        "smtp_port": email_service.smtp_port,
        "agents": list(AGENT_EMAILS.keys())
    }


@router.get("/test/{agent_id}")
async def test_agent_connection(agent_id: str):
    """Test email connection for a specific agent"""
    if agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    result = email_service.test_connection(agent_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Connection test failed"))
    
    return result


@router.post("/send")
async def send_email(request: SendEmailRequest):
    """Send email from an agent"""
    if request.from_agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Agent {request.from_agent_id} not found")
    
    result = email_service.send_email(
        from_agent_id=request.from_agent_id,
        to_email=request.to_email,
        subject=request.subject,
        body=request.body,
        cc_emails=request.cc_emails,
        html_body=request.html_body
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))
    
    return result


@router.post("/agent-to-agent")
async def send_agent_to_agent(request: AgentToAgentRequest):
    """Send email between agents for deliberation"""
    if request.from_agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Sender agent {request.from_agent_id} not found")
    
    if request.to_agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Recipient agent {request.to_agent_id} not found")
    
    result = email_service.send_agent_to_agent(
        from_agent_id=request.from_agent_id,
        to_agent_id=request.to_agent_id,
        subject=request.subject,
        body=request.body,
        cc_agent_ids=request.cc_agent_ids,
        project_id=request.project_id
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))
    
    return result


@router.post("/to-provider")
async def send_to_provider(request: ProviderEmailRequest):
    """Send email to external provider (request adjustments)"""
    if request.from_agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Agent {request.from_agent_id} not found")
    
    result = email_service.send_to_provider(
        from_agent_id=request.from_agent_id,
        provider_email=request.provider_email,
        subject=request.subject,
        body=request.body,
        project_id=request.project_id,
        cc_pmo=request.cc_pmo
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send email"))
    
    return result


@router.get("/inbox/{agent_id}")
async def read_agent_inbox(agent_id: str, limit: int = 10, unread_only: bool = True):
    """Read emails from an agent's inbox"""
    if agent_id not in AGENT_EMAILS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    emails = email_service.read_inbox(
        agent_id=agent_id,
        limit=limit,
        unread_only=unread_only
    )
    
    return {
        "agent_id": agent_id,
        "email": AGENT_EMAILS[agent_id],
        "count": len(emails),
        "emails": emails
    }


@router.get("/agents")
async def list_agent_emails():
    """List all agent email addresses"""
    agents = []
    for agent_id, email_addr in AGENT_EMAILS.items():
        agents.append({
            "agent_id": agent_id,
            "name": AGENT_NAMES.get(agent_id, agent_id),
            "email": email_addr
        })
    return {"agents": agents}
