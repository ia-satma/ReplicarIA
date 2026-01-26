from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import os
from datetime import datetime

from services.workflow_service import WorkflowService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET_KEY', 'your-webhook-secret-key-here')

class WufooWebhookData(BaseModel):
    """Modelo para datos del webhook de Wufoo"""
    HandshakeKey: Optional[str] = None
    EntryId: str
    FormId: str
    DateCreated: Optional[str] = None

@router.get("/wufoo")
async def wufoo_webhook_verify():
    """
    Endpoint GET para verificación de Wufoo.
    Wufoo usa GET para verificar que el webhook existe antes de enviar datos.
    """
    return {
        "status": "ok",
        "message": "Wufoo webhook endpoint is ready",
        "webhook_url": "/api/webhooks/wufoo",
        "method": "POST",
        "note": "Este endpoint acepta POST con datos de formularios Wufoo"
    }

@router.post("/wufoo")
async def wufoo_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Webhook para recibir formularios de Wufoo y iniciar el flujo automáticamente.
    
    Wufoo envía los datos del formulario cuando se completa un SIB (Strategic Initiative Brief).
    Este endpoint:
    1. Valida el HandshakeKey de seguridad
    2. Extrae los datos del formulario
    3. Descarga los attachments si existen
    4. Inicia automáticamente el Stage 1 (Intake y Validación)
    """
    
    # LOG TODO LO QUE LLEGA
    logger.info("=" * 80)
    logger.info("WUFOO WEBHOOK RECIBIDO")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info("=" * 80)
    
    # Obtener datos del formulario
    form_data = await request.form()
    
    # Validar HandshakeKey
    handshake_key = form_data.get("HandshakeKey")
    if handshake_key != WEBHOOK_SECRET:
        logger.warning(f"Invalid HandshakeKey received from Wufoo webhook")
        raise HTTPException(status_code=401, detail="Invalid HandshakeKey")
    
    # Extraer datos básicos del webhook
    entry_id = form_data.get("EntryId")
    form_id = form_data.get("FormId")
    date_created = form_data.get("DateCreated")
    
    logger.info(f"Wufoo webhook received - EntryId: {entry_id}, FormId: {form_id}")
    
    # Mapear campos del formulario Wufoo según API Information
    # Field IDs específicos de tu formulario "desarrollo-de-proyectos-ir"
    
    # Obtener departamento seleccionado (checkboxes Field2-9)
    departments = []
    if form_data.get("Field2"): departments.append("Operaciones")
    if form_data.get("Field3"): departments.append("Legal")
    if form_data.get("Field4"): departments.append("Recursos Humanos")
    if form_data.get("Field5"): departments.append("Marketing")
    if form_data.get("Field6"): departments.append("Finanzas")
    if form_data.get("Field7"): departments.append("Compras")
    if form_data.get("Field8"): departments.append("Calidad")
    if form_data.get("Field9"): departments.append("Proyectos y Arquitectura")
    department_str = ", ".join(departments) if departments else "No especificado"
    
    # Extraer presupuesto (puede venir con formato de moneda)
    budget_raw = form_data.get("Field106", "0")
    budget_value = float(''.join(filter(str.isdigit, str(budget_raw)))) if budget_raw else 0.0
    
    project_data = {
        "project_name": form_data.get("Field215", "Proyecto sin nombre"),  # Información del proyecto
        "sponsor_name": form_data.get("Field103", ""),  # Nombre del solicitante
        "sponsor_email": form_data.get("Field218", ""),  # Correo electrónico
        "department": department_str,  # Departamentos (Field2-9)
        "description": form_data.get("Field107", ""),  # Expectativas del proyecto
        "strategic_alignment": form_data.get("Field215", ""),  # Usa la info del proyecto como alineación
        "expected_economic_benefit": budget_value * 2.5,  # Estimación: 2.5x el presupuesto
        "budget_estimate": budget_value,  # Presupuesto asignado (Field106)
        "duration_months": 12,  # Por defecto 12 meses
        "attachments": [],
        "wufoo_entry_id": entry_id,
        "wufoo_form_id": form_id,
        "wufoo_date": date_created,
        # Campos adicionales específicos de Wufoo
        "company_name": form_data.get("Field213", ""),  # Razón social
        "request_date": form_data.get("Field102", ""),  # Fecha de solicitud
        "urgency_level": form_data.get("Field104", "Normal"),  # Nivel de urgencia
        "requires_human": form_data.get("Field108", "No"),  # ¿Humano requerido?
        "process_completed": form_data.get("Field219", "No")  # ¿Proceso culminado?
    }
    
    # Procesar attachments (archivos adjuntos)
    # Field1 = Constancia de situación fiscal
    # Field216 = Constitutiva
    # Field215 = Información del proyecto (puede incluir archivos)
    attachment_fields = []
    
    # Verificar Field1 (Constancia fiscal)
    fiscal_doc = form_data.get("Field1", "")
    if fiscal_doc and isinstance(fiscal_doc, str) and fiscal_doc.startswith("http"):
        attachment_fields.append({"field": "Field1", "name": "Constancia Fiscal", "url": fiscal_doc})
        project_data["attachments"].append(fiscal_doc)
    
    # Verificar Field216 (Constitutiva)
    constitutiva = form_data.get("Field216", "")
    if constitutiva and isinstance(constitutiva, str) and constitutiva.startswith("http"):
        attachment_fields.append({"field": "Field216", "name": "Constitutiva", "url": constitutiva})
        project_data["attachments"].append(constitutiva)
    
    # Verificar otros campos que puedan contener URLs de archivos
    for key, value in form_data.items():
        if key not in ["Field1", "Field216"] and isinstance(value, str):
            # Si el valor es una URL de archivo de Wufoo
            if value.startswith("http") and ("wufoo.com" in value or "storage" in value or "amazonaws" in value):
                attachment_fields.append({"field": key, "name": f"Archivo {key}", "url": value})
                if value not in project_data["attachments"]:
                    project_data["attachments"].append(value)
    
    logger.info(f"Extracted project data: {project_data['project_name']}")
    logger.info(f"Company: {project_data.get('company_name', 'N/A')}")
    logger.info(f"Departments: {project_data['department']}")
    logger.info(f"Budget: ${project_data['budget_estimate']:,.2f} MXN")
    logger.info(f"Attachments found: {len(attachment_fields)}")
    
    # Iniciar Stage 1 en background para no bloquear la respuesta del webhook
    from server import db
    workflow_service = WorkflowService(db)
    
    background_tasks.add_task(
        process_wufoo_submission,
        workflow_service,
        project_data
    )
    
    # Respuesta inmediata a Wufoo
    return {
        "success": True,
        "message": "Formulario recibido. Iniciando flujo de validación...",
        "entry_id": entry_id,
        "project_name": project_data["project_name"]
    }

async def process_wufoo_submission(workflow_service: WorkflowService, project_data: Dict):
    """
    Procesar la submisión de Wufoo e iniciar el flujo completo.
    Se ejecuta en background para no bloquear el webhook.
    """
    try:
        logger.info(f"Starting Stage 1 for Wufoo submission: {project_data['project_name']}")
        
        # Ejecutar Stage 1: Intake y Validación Estratégica
        result = await workflow_service.stage_1_intake_and_validation(project_data)
        
        logger.info(f"Stage 1 completed for project {result['project_id']}")
        logger.info(f"Status: {result['status']}")
        
        # Aquí podrías enviar notificaciones por email a los agentes involucrados
        # usando el Gmail API (cuando lo integres)
        
    except Exception as e:
        logger.error(f"Error processing Wufoo submission: {str(e)}", exc_info=True)

@router.get("/wufoo/test")
async def test_wufoo_connection():
    """
    Endpoint de prueba para verificar que el webhook está accesible.
    """
    return {
        "status": "ok",
        "message": "Wufoo webhook endpoint is ready",
        "webhook_url": "/api/webhooks/wufoo",
        "note": "Configure este URL en Wufoo Notifications → WebHooks"
    }

@router.post("/wufoo/simulate")
async def simulate_wufoo_submission(
    background_tasks: BackgroundTasks,
    project_name: str = "Proyecto de Prueba desde Wufoo",
    sponsor_name: str = "Juan Pérez",
    sponsor_email: str = "juan.perez@empresa.com"
):
    """
    Endpoint para simular una submisión de Wufoo (útil para pruebas).
    """
    
    # Simular datos de Wufoo
    project_data = {
        "project_name": project_name,
        "sponsor_name": sponsor_name,
        "sponsor_email": sponsor_email,
        "department": "Dirección Estratégica",
        "description": "Proyecto de prueba simulando formulario Wufoo",
        "strategic_alignment": "Alineado con transformación digital 2025",
        "expected_economic_benefit": 3000000.0,
        "budget_estimate": 1000000.0,
        "duration_months": 12,
        "attachments": [],
        "wufoo_entry_id": "SIMULATED-001",
        "wufoo_form_id": "TEST-FORM",
        "wufoo_date": datetime.now().isoformat()
    }
    
    from server import db
    workflow_service = WorkflowService(db)
    
    background_tasks.add_task(
        process_wufoo_submission,
        workflow_service,
        project_data
    )
    
    return {
        "success": True,
        "message": "Simulación de Wufoo iniciada. El flujo comenzará en background.",
        "project_data": project_data
    }
