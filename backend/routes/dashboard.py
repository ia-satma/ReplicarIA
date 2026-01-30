"""
Dashboard API Routes for Revisar.ia System
Provides endpoints for the Dashboard Ejecutivo
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from services.database import db_service, project_repository
from services.dreamhost_email_service import DreamHostEmailService
from config.agents_config import AGENT_CONFIGURATIONS, PROJECT_STATUSES
from services.agents import humanizar_reporte, obtener_persona
from middleware.tenant_context import get_current_empresa_id, get_current_user_id, get_current_tenant

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get user info from tenant context or JWT"""
    tenant = get_current_tenant()
    if tenant:
        return {
            "is_admin": tenant.get("is_admin", False),
            "allowed_companies": tenant.get("allowed_companies", []),
            "user_id": tenant.get("user_id"),
            "empresa_id": tenant.get("empresa_id")
        }
    
    result = {"is_admin": False, "allowed_companies": [], "user_id": None}
    
    if not credentials:
        return result
    
    try:
        from jose import jwt
        import os
        SECRET_KEY = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        result["user_id"] = user_id
        
        if user_id:
            from services.user_db import user_service
            user = await user_service.get_user_by_id(user_id)
            if user:
                result["is_admin"] = user.role == "admin"
                if user.allowed_companies:
                    try:
                        companies = json.loads(user.allowed_companies)
                        if isinstance(companies, list):
                            result["allowed_companies"] = [c.lower().strip() for c in companies]
                    except:
                        pass
    except Exception as e:
        logger.debug(f"Error getting user info: {e}")
    
    return result

class TestEmailRequest(BaseModel):
    to_email: str
    subject: Optional[str] = "Test Email desde Revisar.ia"
    body: Optional[str] = "Este es un correo de prueba del sistema Revisar.ia."

router = APIRouter(prefix="/api", tags=["Dashboard"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
async def api_root():
    return {
        "message": "Revisar.ia Multi-Agent System API",
        "version": "4.0.0",
        "description": "Sistema de Trazabilidad - Revisar.ia",
        "demo_mode": db_service.demo_mode,
        "endpoints": {
            "projects": "/api/projects",
            "agents": "/api/agents",
            "stats": "/api/stats",
            "docs": "/docs"
        }
    }

async def _get_dashboard_stats(empresa_id: Optional[str] = None) -> Dict[str, Any]:
    """Core stats logic shared by both /api/stats and /dashboard/stats"""
    try:
        from services.defense_file_service import defense_file_service
        from services.project_serializer import get_project_amount
        
        defense_files = defense_file_service.list_all()
        
        approved = 0
        rejected = 0
        in_review = 0
        total_amount = 0.0
        total_projects = 0
        
        for df in defense_files:
            project_data = df.get("project_data", {})
            df_empresa = project_data.get("empresa_id") or df.get("empresa_id")
            
            if empresa_id and df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
                continue
            
            total_projects += 1
            
            full_df = defense_file_service.get_defense_file(df["project_id"])
            if full_df:
                total_amount += get_project_amount(full_df)
                
                decision = (df.get("final_decision") or "").lower()
                if decision == "approve":
                    approved += 1
                elif decision == "reject":
                    rejected += 1
                else:
                    in_review += 1
        
        agent_status = []
        for agent_id, config in AGENT_CONFIGURATIONS.items():
            agent_status.append({
                "agent_id": agent_id,
                "name": config.get('name', agent_id),
                "status": "active",
                "department": config.get('department', ''),
                "role": config.get('role', '')
            })
        
        return {
            "approved": approved,
            "rejected": rejected,
            "in_review": in_review,
            "total": approved + rejected + in_review,
            "total_projects": total_projects,
            "total_amount": total_amount,
            "empresa_id": empresa_id,
            "agents": agent_status,
            "agent_count": len(agent_status)
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        # 503 for service unavailable (database issues)
        raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible. Intente nuevamente.")


@router.get("/stats")
async def get_stats():
    """Get stats filtered by current empresa"""
    empresa_id = get_current_empresa_id()
    return await _get_dashboard_stats(empresa_id)


@dashboard_router.get("/stats")
async def get_dashboard_stats(request: Request):
    """Get dashboard stats - accessible via /dashboard/stats"""
    empresa_id = request.headers.get("X-Empresa-ID")
    return await _get_dashboard_stats(empresa_id)

@router.get("/projects/empresa/{empresa_id}")
async def get_projects_by_empresa(
    empresa_id: str,
    status: Optional[str] = None
):
    """Get all projects for a specific company (multi-tenant with authorization)."""
    current_empresa = get_current_empresa_id()
    
    if current_empresa and current_empresa.lower().strip() != empresa_id.lower().strip():
        raise HTTPException(
            status_code=403, 
            detail="No tienes permiso para acceder a los proyectos de esta empresa"
        )
    
    try:
        projects = await project_repository.get_projects_by_empresa(
            empresa_id=empresa_id,
            status=status
        )
        return {"projects": projects, "total": len(projects), "empresa_id": empresa_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting projects for empresa {empresa_id}: {e}")
        # 503 for service unavailable
        raise HTTPException(status_code=503, detail="Error retrieving projects. Service temporarily unavailable.")

class CreateProjectRequest(BaseModel):
    empresa_id: str
    project_name: str
    description: Optional[str] = ""
    budget_estimate: Optional[float] = 0
    status: Optional[str] = "IN_REVIEW"
    created_by: Optional[str] = None

@router.post("/projects")
async def create_project(
    project_data: CreateProjectRequest,
    user_info: dict = Depends(get_current_user_info)
):
    """Create a new project with mandatory empresa_id."""
    try:
        data = project_data.model_dump()
        empresa_id = data.pop("empresa_id")
        created_by = data.pop("created_by", None) or user_info.get("user_id")
        
        project_id = await project_repository.create_project(
            project_data=data,
            empresa_id=empresa_id,
            created_by=created_by
        )
        
        project = await project_repository.get_project(project_id)
        return {"success": True, "project": project}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class HumanizeReportRequest(BaseModel):
    tipo_agente: str
    datos: Dict[str, Any]
    contexto: Optional[Dict[str, Any]] = None
    formato: str = 'markdown'


@router.get("/agents")
async def get_agents():
    agents = []
    for agent_id, config in AGENT_CONFIGURATIONS.items():
        agents.append({
            "agent_id": agent_id,
            "name": config['name'],
            "role": config['role'],
            "email": config['email'],
            "department": config['department'],
            "llm_model": config['llm_model'],
            "pcloud_folder": config.get('pcloud_folder', ''),
            "pcloud_link": config.get('pcloud_link', '')
        })
    return {"agents": agents}


@router.post("/agents/humanize-report", summary="Humanize agent report")
async def humanize_report_endpoint(request: HumanizeReportRequest):
    """
    Convierte datos crudos de un agente en reporte narrativo humanizado.
    
    tipo_agente: 'ocr_validation', 'red_team', 'risk_scoring', 'a1'-'a8'
    datos: Diccionario con resultados del agente
    contexto: Información del proyecto
    formato: 'markdown', 'html', o 'dict'
    """
    try:
        reporte = humanizar_reporte(
            tipo_agente=request.tipo_agente,
            datos_crudos=request.datos,
            contexto=request.contexto,
            formato=request.formato
        )
        
        return {
            'success': True,
            'reporte': reporte
        }
    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors only
        logger.exception(f"Unexpected error humanizing report: {e}")
        raise HTTPException(status_code=500, detail="Error processing report. Please try again.")


@router.get("/agents/persona-profiles", summary="List all agent personas")
async def list_personas():
    """Lista todas las personas profesionales disponibles."""
    personas_ids = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 
                    'ocr_validation', 'red_team', 'risk_analyzer', 'defense']
    
    personas = []
    for pid in personas_ids:
        try:
            p = obtener_persona(pid)
            personas.append({
                'id': pid,
                'nombre': p.nombre,
                'titulo': p.titulo,
                'especialidad': p.especialidad,
                'años_experiencia': p.años_experiencia,
                'tono': p.tono.value
            })
        except:
            pass
    
    return {
        'success': True,
        'count': len(personas),
        'personas': personas
    }


@router.get("/agents/persona-profiles/{persona_id}", summary="Get persona details")
async def get_persona_details(persona_id: str):
    """Obtiene detalles de una persona específica."""
    try:
        p = obtener_persona(persona_id)
        return {
            'success': True,
            'persona': {
                'nombre': p.nombre,
                'titulo': p.titulo,
                'especialidad': p.especialidad,
                'años_experiencia': p.años_experiencia,
                'tono': p.tono.value,
                'firma': p.firma,
                'saludo_formal': p.saludo_formal,
                'cierre_formal': p.cierre_formal,
                'frases_caracteristicas': p.frases_caracteristicas
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found")


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in AGENT_CONFIGURATIONS:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    config = AGENT_CONFIGURATIONS[agent_id]
    return {
        "agent_id": agent_id,
        **config
    }


@router.get("/interactions")
async def get_interactions(project_id: Optional[str] = None):
    try:
        interactions = await db_service.get_interactions(project_id)
        return {"interactions": interactions}
    except Exception as e:
        logger.error(f"Error getting interactions: {e}")
        # 503 for database/service issues
        raise HTTPException(status_code=503, detail="Unable to retrieve interactions. Service temporarily unavailable.")

def _get_month_name_spanish(month: int) -> str:
    """Convert month number to Spanish month name"""
    months = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    return months.get(month, "Desconocido")

@router.get("/defense-files")
async def get_defense_files():
    """
    Get defense files organized by Company → Month → Projects
    Uses real defense file data from defense_file_service.
    Filtered by current empresa via tenant context.
    """
    empresa_id = get_current_empresa_id()
    
    try:
        from services.defense_file_service import defense_file_service
        
        stored_defense_files = defense_file_service.list_all()
        
        companies = {}
        
        for df in stored_defense_files:
            project_id = df.get('project_id', '')
            project_data = df.get('project_data', {})
            
            df_empresa = project_data.get("empresa_id") or df.get("empresa_id")
            if empresa_id and df_empresa and df_empresa.lower().strip() != empresa_id.lower().strip():
                continue
            
            company_name = (
                project_data.get('client_name') or 
                project_data.get('company_name') or 
                project_data.get('sponsor_name') or 
                "Sin Empresa"
            )
            
            created_at_str = df.get('created_at', '') or project_data.get('submitted_at', '')
            if isinstance(created_at_str, str) and created_at_str:
                try:
                    created_date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    created_date = datetime.now()
            elif isinstance(created_at_str, datetime):
                created_date = created_at_str
            else:
                created_date = datetime.now()
            
            month_key = f"{_get_month_name_spanish(created_date.month)} {created_date.year}"
            
            if company_name not in companies:
                companies[company_name] = {
                    "company_name": company_name,
                    "months": {},
                    "total_projects": 0,
                    "total_budget": 0
                }
            
            if month_key not in companies[company_name]["months"]:
                companies[company_name]["months"][month_key] = {
                    "month": month_key,
                    "month_number": created_date.month,
                    "year": created_date.year,
                    "projects": [],
                    "project_count": 0,
                    "total_budget": 0
                }
            
            deliberations = df.get("deliberations", [])
            pcloud_documents = df.get("pcloud_documents", [])
            documents = df.get("documents", [])
            final_decision = df.get("final_decision")
            pcloud_links = df.get("pcloud_links", {})
            bitacora_link = df.get("bitacora_link")
            compliance_score = df.get("compliance_score", 100)
            emails = df.get("emails", [])
            
            budget = project_data.get('amount', 0) or project_data.get('budget_estimate', 0) or 0
            
            project_entry = {
                "project_id": project_id,
                "project_name": project_data.get('name', '') or project_data.get('project_name', ''),
                "budget": budget,
                "sponsor_name": project_data.get('sponsor_name', ''),
                "sponsor_email": project_data.get('sponsor_email', ''),
                "deliberations": deliberations,
                "deliberation_count": len(deliberations),
                "pcloud_documents": pcloud_documents,
                "documents": documents,
                "emails": emails,
                "final_decision": final_decision,
                "status": 'approved' if final_decision == 'approved' else ('rejected' if final_decision == 'rejected' else 'in_review'),
                "workflow_state": df.get('workflow_state', 'E4_LEGAL'),
                "compliance_score": compliance_score,
                "created_at": created_at_str,
                "pcloud_links": pcloud_links,
                "bitacora_link": bitacora_link
            }
            
            companies[company_name]["months"][month_key]["projects"].append(project_entry)
            companies[company_name]["months"][month_key]["project_count"] += 1
            companies[company_name]["months"][month_key]["total_budget"] += budget
            companies[company_name]["total_projects"] += 1
            companies[company_name]["total_budget"] += budget
        
        result = []
        for company_name, company_data in sorted(companies.items()):
            months_list = []
            for month_key, month_data in sorted(
                company_data["months"].items(),
                key=lambda x: (x[1]["year"], x[1]["month_number"]),
                reverse=True
            ):
                months_list.append({
                    "month": month_data["month"],
                    "projects": month_data["projects"],
                    "project_count": month_data["project_count"],
                    "total_budget": month_data["total_budget"]
                })
            
            result.append({
                "company_name": company_name,
                "months": months_list,
                "total_projects": company_data["total_projects"],
                "total_budget": company_data["total_budget"]
            })
        
        return {
            "defense_files": result,
            "total_companies": len(result),
            "total_projects": sum(c["total_projects"] for c in result)
        }
        
    except Exception as e:
        logger.error(f"Error getting defense files: {e}")
        import traceback
        traceback.print_exc()
        return {
            "defense_files": [],
            "total_companies": 0,
            "total_projects": 0,
            "error": str(e)
        }

@router.post("/test-email")
async def test_external_email(request: TestEmailRequest):
    """
    Test endpoint to verify external email delivery via DreamHost SMTP.
    This helps diagnose if emails to external providers (like Santiago) are being sent.
    """
    try:
        email_service = DreamHostEmailService()
        
        if not email_service.initialized:
            return {
                "success": False,
                "error": "DreamHost email service not initialized - check DREAMHOST_EMAIL_PASSWORD secret",
                "initialized": False
            }
        
        result = email_service.send_email(
            from_agent_id="A2_PMO",
            to_email=request.to_email,
            subject=request.subject,
            body=f"""
{request.body}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este correo fue enviado desde Revisar.ia
como prueba de conectividad SMTP.

Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sistema: Revisar.ia Multi-Agent System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Carlos Mendoza
Gerente de PMO
Revisar.ia
📧 pmo@revisar.ia
"""
        )
        
        logger.info(f"[TEST-EMAIL] Result: {result}")
        
        return {
            "success": result.get("success", False),
            "message_id": result.get("message_id"),
            "to_email": request.to_email,
            "error": result.get("error"),
            "initialized": True,
            "smtp_host": email_service.smtp_host,
            "smtp_port": email_service.smtp_port
        }
        
    except Exception as e:
        logger.error(f"[TEST-EMAIL] Error: {e}")
        return {
            "success": False,
            "error": str(e),
            "initialized": False
        }

@router.get("/email-status")
async def get_email_status():
    """Check email service configuration status"""
    try:
        email_service = DreamHostEmailService()
        
        return {
            "initialized": email_service.initialized,
            "smtp_host": email_service.smtp_host,
            "smtp_port": email_service.smtp_port,
            "imap_host": email_service.imap_host,
            "agents_configured": list(AGENT_CONFIGURATIONS.keys()),
            "password_configured": bool(email_service.agent_passwords.get("A2_PMO"))
        }
    except Exception as e:
        return {
            "error": str(e),
            "initialized": False
        }

class PCloudLinkRequest(BaseModel):
    file_id: int

@router.post("/pcloud/get-link")
async def get_pcloud_link(request: PCloudLinkRequest):
    """
    Get a fresh permanent public link for a pCloud file.
    Use this endpoint to refresh expired download links.
    Returns a non-expiring public share link.
    """
    try:
        from services.pcloud_service import PCloudService
        
        pcloud = PCloudService()
        login_result = pcloud.login()
        
        if not login_result.get("success"):
            return {
                "success": False,
                "error": "Failed to connect to pCloud. Check credentials.",
                "details": login_result.get("error")
            }
        
        link_result = pcloud.get_or_create_public_link(request.file_id)
        
        if link_result.get("success"):
            return {
                "success": True,
                "public_link": link_result.get("public_link"),
                "download_link": link_result.get("download_link"),
                "code": link_result.get("code"),
                "expires": None,
                "message": "Permanent public link generated successfully"
            }
        else:
            return {
                "success": False,
                "error": link_result.get("error"),
                "message": "Failed to generate public link"
            }
            
    except Exception as e:
        logger.error(f"Error getting pCloud link: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/pcloud/agent-folder/{agent_id}")
async def get_agent_folder_link(agent_id: str):
    """
    Get a permanent public link for an agent's pCloud folder.
    This allows viewing all documents for a specific agent.
    """
    try:
        from services.pcloud_service import PCloudService, AGENT_FOLDER_IDS
        
        folder_id = AGENT_FOLDER_IDS.get(agent_id)
        if not folder_id:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_id}",
                "valid_agents": list(AGENT_FOLDER_IDS.keys())
            }
        
        pcloud = PCloudService()
        login_result = pcloud.login()
        
        if not login_result.get("success"):
            return {
                "success": False,
                "error": "Failed to connect to pCloud"
            }
        
        link_result = pcloud.get_folder_public_link(folder_id)
        
        return {
            "success": link_result.get("success", False),
            "agent_id": agent_id,
            "folder_id": folder_id,
            "public_link": link_result.get("public_link"),
            "error": link_result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error getting agent folder link: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/pcloud/status")
async def get_pcloud_status():
    """Check pCloud service connection status and list available folders"""
    try:
        from services.pcloud_service import PCloudService, AGENT_FOLDER_IDS
        
        pcloud = PCloudService()
        login_result = pcloud.login()
        
        if not login_result.get("success"):
            return {
                "connected": False,
                "error": login_result.get("error"),
                "credentials_configured": bool(pcloud.username and pcloud.password)
            }
        
        folders_result = pcloud.find_agent_folders()
        
        return {
            "connected": True,
            "email": login_result.get("email"),
            "server": login_result.get("server"),
            "quota_used": login_result.get("usedquota"),
            "quota_total": login_result.get("quota"),
            "agent_folders": pcloud.agent_folders,
            "predefined_folders": AGENT_FOLDER_IDS
        }
        
    except Exception as e:
        logger.error(f"Error checking pCloud status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }
