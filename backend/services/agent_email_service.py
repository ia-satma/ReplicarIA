import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from services.multi_agent_gmail import MultiAgentGmailService
from services.drive_organization_service import DriveOrganizationService
from services.agent_service import AGENT_CONFIGURATIONS

logger = logging.getLogger(__name__)

class AgentEmailService:
    """Servicio para que cada agente envíe emails individuales con su personalidad"""
    
    def __init__(self):
        # Usar servicio multi-agente que maneja todas las cuentas
        self.multi_gmail = MultiAgentGmailService()
        self.drive_org_service = DriveOrganizationService()
    
    async def send_agent_individual_analysis(
        self,
        agent_id: str,
        project_id: str,
        project_data: Dict,
        analysis: str,
        decision: str,
        sponsor_email: str,
        sponsor_name: str
    ) -> Dict:
        """
        Cada agente envía SU PROPIO email desde su cuenta real.
        Incluye CC a otros agentes para comunicación cruzada.
        """
        
        # Obtener configuración del agente
        agent_config = AGENT_CONFIGURATIONS.get(agent_id)
        if not agent_config:
            return {"success": False, "reason": f"Agente {agent_id} no encontrado"}
        
        agent_name = agent_config['name']
        agent_role = agent_config['role']
        agent_dept = agent_config['department']
        agent_email_addr = agent_config['email']
        folder_id = agent_config['drive_folder_id']
        token_file = agent_config.get('token_file', '')
        
        # Crear contenido del documento
        doc_content = f"""ANÁLISIS Y DICTAMEN
Agente: {agent_name}
ID Agente: {agent_id}
Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROYECTO: {project_data.get('project_name', 'Proyecto')}
ID: {project_id}

DECISIÓN: {decision}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANÁLISIS DETALLADO:

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este documento fue generado automáticamente por {agent_name}.
Agent Network System - Revisar.ia
"""
        
        # Guardar documento en Drive del agente (organizado por mes)
        logger.info(f"📄 {agent_name} guardando análisis en SU Drive (carpeta del mes)...")
        
        drive_doc = self.drive_org_service.save_document_to_drive(
            agent_id=agent_id,
            token_file=token_file,
            parent_folder_id=folder_id,
            project_id=project_id,
            project_name=project_data.get('project_name', 'Proyecto'),
            document_content=doc_content,
            document_type="Análisis"
        )
        
        if drive_doc:
            drive_link = drive_doc['web_view_link']
            pdf_attachment_path = drive_doc.get('pdf_path')
            logger.info(f"✅ {agent_name} guardó documento en Drive exitosamente")
        else:
            drive_link = "Documento no disponible"
            pdf_attachment_path = None
            logger.warning(f"⚠️ {agent_name} NO pudo guardar en Drive")
        
        # Construir email con personalidad del agente
        subject, body = self._compose_personalized_email(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_role=agent_role,
            agent_dept=agent_dept,
            agent_email=agent_email_addr,
            project_id=project_id,
            project_name=project_data.get('project_name'),
            sponsor_name=sponsor_name,
            analysis=analysis,
            decision=decision,
            drive_link=drive_link
        )
        
        # Lista de CC - OTROS AGENTES
        cc_list = []
        for other_id, other_config in AGENT_CONFIGURATIONS.items():
            if other_id != agent_id and other_id != 'PROVEEDOR_IA':
                cc_list.append(other_config['email'])
        
        # Enviar email desde la cuenta del agente con PDF ADJUNTO
        result = self.multi_gmail.send_email_as_agent(
            agent_id=agent_id,
            to=sponsor_email,
            subject=subject,
            body=body,
            cc=cc_list,
            attachment_path=pdf_attachment_path  # ← PDF ADJUNTO
        )
        
        if result.get('success'):
            logger.info(f"✅ {agent_name} envió email desde {agent_email_addr}: {result.get('message_id')}")
            logger.info(f"   CC a: {', '.join(cc_list)}")
            return {
                "success": True,
                "message_id": result.get('message_id'),
                "drive_document": drive_doc,
                "agent": agent_name,
                "from_email": agent_email_addr,
                "cc": cc_list
            }
        else:
            logger.error(f"❌ {agent_name} no pudo enviar email: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error'),
                "agent": agent_name
            }
    
    def _compose_personalized_email(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        agent_dept: str,
        agent_email: str,
        project_id: str,
        project_name: str,
        sponsor_name: str,
        analysis: str,
        decision: str,
        drive_link: str
    ) -> tuple[str, str]:
        """Compone email con la personalidad única de cada agente - TONO HUMANO"""
        
        # Subject más natural
        subjects = {
            "A1_SPONSOR": f"Re: {project_name} - Mi análisis estratégico",
            "A3_FISCAL": f"Re: {project_name} - Revisión fiscal",
            "A5_FINANZAS": f"Re: {project_name} - Análisis financiero",
            "A2_PMO": f"Re: {project_name} - Consolidación del equipo"
        }
        
        subject = subjects.get(agent_id, f"Re: {project_name}")
        
        # Saludo más humano
        greetings = {
            "A1_SPONSOR": f"Hola {sponsor_name},",
            "A3_FISCAL": f"Hola {sponsor_name},",
            "A5_FINANZAS": f"Hola {sponsor_name},",
            "A2_PMO": f"Hola {sponsor_name},"
        }
        
        # Intro personalizada
        intros = {
            "A1_SPONSOR": "Soy María, de Estrategia. Acabo de revisar tu propuesta.",
            "A3_FISCAL": "Soy Laura, del equipo Fiscal. Revisé el proyecto con atención.",
            "A5_FINANZAS": "Soy Roberto, de Finanzas. Analicé los números de tu proyecto.",
            "A2_PMO": "Soy Carlos, de PMO. Ya consolidé los análisis del equipo."
        }
        
        # Firma más humana
        signatures = {
            "A1_SPONSOR": "Cualquier duda sobre estrategia, escríbeme.\n\nSaludos,\nMaría",
            "A3_FISCAL": "Si necesitas aclarar algo del tema fiscal, con gusto.\n\nSaludos,\nLaura",
            "A5_FINANZAS": "Para dudas sobre presupuesto o ROI, aquí estoy.\n\nSaludos,\nRoberto",
            "A2_PMO": "Cualquier cosa, me avisas.\n\nSaludos,\nCarlos"
        }
        
        greeting = greetings.get(agent_id, f'Hola {sponsor_name},')
        intro = intros.get(agent_id, "Revisé tu proyecto.")
        signature = signatures.get(agent_id, '\nSaludos')
        
        # Body más conversacional
        body = f"""{greeting}

{intro}

{analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 ADJUNTO: Mi análisis completo en PDF
También disponible en Drive: {drive_link}

{signature}

--
{agent_name}
{agent_email}
{agent_dept}
"""
        
        return subject, body
