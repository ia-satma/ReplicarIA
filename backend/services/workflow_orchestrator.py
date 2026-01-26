import os
import logging
import glob as glob_module
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

from services.agent_service import AgentService, AGENT_CONFIGURATIONS
from services.gmail_service import GmailService
from services.file_analysis_service import FileAnalysisService
from services.report_generator import ReportGeneratorService
from services.agent_email_service import AgentEmailService
from services.agent_discussion_service import AgentDiscussionService
from services.dreamhost_email_service import DreamHostEmailService
from services.state_machine import ProjectStateMachine, ProjectState, AgentDecision
from models.projects import Project, ProjectPhase, ProjectStatus, StrategicInitiativeBrief, ValidationReport

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """
    Orquestador de workflow con State Machine y Revisión Iterativa.
    A2-PMO actúa como hub central de coordinación.
    """
    
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.agent_service = AgentService()
        self.file_analysis = FileAnalysisService()
        self.report_generator = ReportGeneratorService()
        self.agent_email_service = AgentEmailService()
        self.discussion_service = AgentDiscussionService(db)
        self.state_machine = ProjectStateMachine()
        
        self.dreamhost_email = DreamHostEmailService()
        
        ROOT_DIR = Path(__file__).parent.parent
        self.reports_dir = ROOT_DIR / "reports"
        self.po_dir = ROOT_DIR / "purchase_orders"
        
        try:
            gmail = GmailService()
            self.gmail_service = gmail if gmail.service else None
        except:
            self.gmail_service = None
            logger.warning("Gmail not available - emails will be logged only")
    
    def _get_provider_email(self, sib: StrategicInitiativeBrief) -> str:
        """
        Gets the provider/vendor email from SIB form data.
        Priority: provider_email > vendor_email > sponsor_email
        """
        form_data = sib.form_data or {}
        
        provider_email = form_data.get('provider_email') or form_data.get('vendor_email')
        if provider_email:
            return provider_email
        
        return sib.sponsor_email
    
    def _collect_project_pdfs(self, project_id: str) -> List[str]:
        """
        Collects all PDF paths for a project (agent reports, consolidated reports, POs).
        Returns list of absolute file paths.
        
        Uses the same naming convention as ReportGeneratorService:
        - Files are named: ID{project_id[:8]}_{agent_id}_Reporte_*.pdf
        - Example: IDPROJ-314_A1_SPONSOR_Reporte_estrategia_V1.pdf
        """
        pdf_paths = []
        
        if not project_id:
            logger.warning("_collect_project_pdfs called with empty project_id")
            return pdf_paths
        
        safe_id = str(project_id)[:8]
        file_prefix = f"ID{safe_id}"
        
        if self.reports_dir.exists():
            patterns = [
                f"{file_prefix}_A1_SPONSOR_*.pdf",
                f"{file_prefix}_A3_FISCAL_*.pdf",
                f"{file_prefix}_A5_FINANZAS_*.pdf",
                f"{file_prefix}_LEGAL_*.pdf",
                f"{file_prefix}_A2_*.pdf",
                f"{file_prefix}_SYSTEM_*.pdf",
                f"{file_prefix}_BITACORA_*.pdf",
            ]
            
            for pattern in patterns:
                try:
                    matches = list(self.reports_dir.glob(pattern))
                    for match in matches:
                        if match.exists() and match.is_file() and str(match) not in pdf_paths:
                            pdf_paths.append(str(match))
                except Exception as e:
                    logger.warning(f"Error searching for pattern {pattern}: {e}")
        else:
            logger.warning(f"Reports directory does not exist: {self.reports_dir}")
        
        if self.po_dir and self.po_dir.exists():
            try:
                po_patterns = [
                    f"{file_prefix}*.pdf",
                    f"*{safe_id}*.pdf",
                ]
                for po_pattern in po_patterns:
                    po_matches = list(self.po_dir.glob(po_pattern))
                    for match in po_matches:
                        if match.exists() and match.is_file() and str(match) not in pdf_paths:
                            pdf_paths.append(str(match))
            except Exception as e:
                logger.warning(f"Error searching for PO files: {e}")
        
        logger.info(f"Collected {len(pdf_paths)} PDFs for project {file_prefix}: {[os.path.basename(p) for p in pdf_paths]}")
        return pdf_paths
    
    async def _send_provider_notification(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        final_state: ProjectState,
        decisions: Dict[str, str],
        conflicts: List[str],
        consolidation_analysis: str,
        po_path: Optional[str] = None
    ) -> Dict:
        """
        Sends email notification to the vendor/provider with all deliberation PDFs attached.
        Uses DreamHost email service for external communication.
        """
        provider_email = self._get_provider_email(sib)
        provider_name = sib.form_data.get('provider_name') or sib.sponsor_name
        
        is_approved = final_state == ProjectState.APROBADO_F0
        decision_text = "APROBADO" if is_approved else "RECHAZADO/REQUIERE AJUSTES"
        
        pdf_attachments = self._collect_project_pdfs(project_id)
        
        if po_path:
            if os.path.exists(po_path) and os.path.isfile(po_path):
                if po_path not in pdf_attachments:
                    pdf_attachments.append(po_path)
                    logger.info(f"PO attachment added: {os.path.basename(po_path)}")
            else:
                logger.warning(f"PO attachment not found or not a file: {po_path}")
        
        if not pdf_attachments:
            logger.warning(f"No PDF attachments found for project {project_id}")
        
        subject = f"[Revisar.ia] Resultado de Evaluación: {sib.project_name[:40]} - {decision_text}"
        
        if is_approved:
            body = f"""Estimado/a {provider_name},

Soy Carlos Mendoza, Gerente de PMO de Revisar.ia.

Me complace informarle que su propuesta de proyecto ha sido APROBADA por nuestro equipo de evaluación.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMEN DE DECISIÓN

Proyecto: {sib.project_name}
ID de Proyecto: {project_id}
Monto Aprobado: ${sib.budget_estimate:,.2f} MXN
Duración: {sib.duration_months} meses
Decisión Final: ✅ APROBADO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗳️ EVALUACIONES DEL EQUIPO:

• María Rodríguez (Estrategia): {decisions.get('A1_SPONSOR', 'N/A')}
• Laura Sánchez (Fiscal): {decisions.get('A3_FISCAL', 'N/A')}
• Roberto Torres (Finanzas): {decisions.get('A5_FINANZAS', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 DOCUMENTOS ADJUNTOS:

Se incluyen {len(pdf_attachments)} documentos PDF con los análisis detallados de cada área:
- Análisis Estratégico (A1-Sponsor)
- Análisis Fiscal (A3-Fiscal)
- Análisis Financiero (A5-Finanzas)
- Reporte Consolidado PMO
- Orden de Compra (si aplica)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PRÓXIMOS PASOS:

1. Nuestro departamento Legal (legal@revisar-ia.com) le contactará para la elaboración del contrato
2. Una vez firmado el contrato, procederemos con la formalización
3. Se le notificará la fecha de inicio del proyecto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANÁLISIS CONSOLIDADO:

{consolidation_analysis[:800]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quedamos a su disposición para cualquier consulta.

Saludos cordiales,

Carlos Mendoza
Gerente de PMO
Revisar.ia

📧 pmo@revisar-ia.com
"""
        else:
            conflict_text = '\n'.join(['• ' + c for c in conflicts]) if conflicts else 'No se registraron conflictos específicos.'
            
            body = f"""Estimado/a {provider_name},

Soy Carlos Mendoza, Gerente de PMO de Revisar.ia.

Le informo que su propuesta de proyecto requiere ajustes antes de poder ser aprobada, o ha sido rechazada por nuestro equipo de evaluación.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMEN DE DECISIÓN

Proyecto: {sib.project_name}
ID de Proyecto: {project_id}
Monto Propuesto: ${sib.budget_estimate:,.2f} MXN
Decisión Final: ❌ {decision_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗳️ EVALUACIONES DEL EQUIPO:

• María Rodríguez (Estrategia): {decisions.get('A1_SPONSOR', 'N/A')}
• Laura Sánchez (Fiscal): {decisions.get('A3_FISCAL', 'N/A')}
• Roberto Torres (Finanzas): {decisions.get('A5_FINANZAS', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ OBSERVACIONES Y AJUSTES REQUERIDOS:

{conflict_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 DOCUMENTOS ADJUNTOS:

Se incluyen {len(pdf_attachments)} documentos PDF con los análisis detallados que fundamentan esta decisión.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANÁLISIS CONSOLIDADO:

{consolidation_analysis[:800]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 OPCIONES DISPONIBLES:

1. Revisar las observaciones y presentar una propuesta ajustada
2. Solicitar una reunión para aclarar los puntos señalados
3. Contactar a nuestro equipo para mayor información

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quedamos a su disposición para cualquier consulta o aclaración.

Saludos cordiales,

Carlos Mendoza
Gerente de PMO
Revisar.ia

📧 pmo@revisar-ia.com
"""
        
        result = self.dreamhost_email.send_email_with_attachments(
            from_agent_id="A2_PMO",
            to_email=provider_email,
            subject=subject,
            body=body,
            attachments=pdf_attachments,
            cc_emails=None
        )
        
        if result.get('success'):
            logger.info(f"✅ Email enviado al proveedor {provider_email} con {len(pdf_attachments)} adjuntos")
        else:
            logger.error(f"❌ Error enviando email al proveedor: {result.get('error')}")
        
        return result
    
    async def _send_legal_contract_request(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        consolidation_analysis: str,
        po_path: Optional[str] = None
    ) -> Dict:
        """
        Sends contract preparation request to legal@revisar-ia.com for approved projects.
        Includes all relevant project documentation.
        """
        legal_email = "legal@revisar-ia.com"
        provider_email = self._get_provider_email(sib)
        provider_name = sib.form_data.get('provider_name') or sib.sponsor_name
        
        pdf_attachments = self._collect_project_pdfs(project_id)
        
        if po_path:
            if os.path.exists(po_path) and os.path.isfile(po_path):
                if po_path not in pdf_attachments:
                    pdf_attachments.append(po_path)
                    logger.info(f"PO attachment added for legal request: {os.path.basename(po_path)}")
            else:
                logger.warning(f"PO attachment not found for legal request: {po_path}")
        
        if not pdf_attachments:
            logger.warning(f"No PDF attachments found for legal contract request - project {project_id}")
        
        subject = f"[PMO → Legal] Solicitud de Contrato - Proyecto: {sib.project_name[:40]}"
        
        body = f"""Hola Equipo Legal,

Soy Carlos Mendoza, Gerente de PMO.

El proyecto "{sib.project_name}" ha sido APROBADO por el equipo ejecutivo. Solicito la elaboración del contrato de prestación de servicios.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 INFORMACIÓN DEL PROYECTO:

• Proyecto: {sib.project_name}
• ID Proyecto: {project_id}
• Monto Aprobado: ${sib.budget_estimate:,.2f} MXN
• Duración: {sib.duration_months} meses
• Departamento: {sib.department}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 DATOS DEL PROVEEDOR/CONTRATISTA:

• Nombre/Razón Social: {provider_name}
• Email de Contacto: {provider_email}
• Descripción del Servicio: {sib.description[:300]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 DOCUMENTOS ADJUNTOS ({len(pdf_attachments)} archivos):

Se incluyen todos los análisis de deliberación:
- Análisis Estratégico (María Rodríguez - A1)
- Análisis Fiscal (Laura Sánchez - A3)
- Análisis Financiero (Roberto Torres - A5)
- Reporte Consolidado PMO
- Orden de Compra (si aplica)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 SOLICITUD DE CONTRATO:

Por favor elaborar el Contrato de Prestación de Servicios que incluya:

✓ Alcance detallado del servicio
✓ Entregables específicos y verificables
✓ Criterios de aceptación claros
✓ Timeline y milestones
✓ Forma de pago (hitos, porcentajes)
✓ Cláusulas de cumplimiento fiscal
✓ Evidencia de materialidad requerida (Art. 69-B CFF)
✓ Fecha Cierta para efectos fiscales

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ANÁLISIS CONSOLIDADO DEL EQUIPO:

{consolidation_analysis[:600]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📨 PRÓXIMOS PASOS ESPERADOS:

1. Elaborar borrador de contrato
2. Enviar a revisión del equipo (María, Laura, Roberto)
3. Una vez aprobado, enviar al proveedor para firma
4. Archivar contrato firmado en Defense File

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cualquier duda, estoy disponible.

Saludos,

Carlos Mendoza
Gerente de PMO
Revisar.ia

📧 pmo@revisar-ia.com
"""
        
        result = self.dreamhost_email.send_email_with_attachments(
            from_agent_id="A2_PMO",
            to_email=legal_email,
            subject=subject,
            body=body,
            attachments=pdf_attachments,
            cc_emails=[provider_email]
        )
        
        if result.get('success'):
            logger.info(f"✅ Solicitud de contrato enviada a Legal ({legal_email}) con CC a proveedor")
        else:
            logger.error(f"❌ Error enviando solicitud a Legal: {result.get('error')}")
        
        return result
    
    async def process_phase_0_intake(self, sib_data: Dict) -> Dict:
        """
        FASE 0: INTAKE Y VALIDACIÓN con State Machine y Revisión Iterativa.
        
        Flujo:
        1. INTAKE → A2 registra proyecto
        2. VALIDACION_PARALELA → A1, A3, A5 analizan y generan PDFs
        3. CONSOLIDACION → A2 evalúa consenso
        4. Si conflicto → REVISION_ITERATIVA (ciclo con PDFs consolidados)
        5. APROBADO_F0 / RECHAZADO_F0 / ESCALADO_HUMANO
        """
        
        # ===== PASO 1: INTAKE (A2-PMO) =====
        logger.info(f"[STATE MACHINE] INTAKE: Registrando proyecto {sib_data.get('project_name')}")
        
        # Crear SIB
        sib = StrategicInitiativeBrief(**{
            "sib_id": str(uuid.uuid4()),
            **sib_data
        })
        await self.db.strategic_briefs.insert_one(sib.model_dump())
        
        # Crear proyecto con state machine
        project_id = str(uuid.uuid4())
        project = Project(
            project_id=project_id,
            sib_id=sib.sib_id,
            current_phase=ProjectPhase.PHASE_0_INTAKE,
            current_status=ProjectStatus.IN_VALIDATION,
            workflow_state=ProjectState.INTAKE,
            revision_cycle=0,
            project_name=sib.project_name,
            sponsor_agent_id="A1_SPONSOR",
            description=sib.description,
            budget=sib.budget_estimate,
            expected_benefit=sib.expected_economic_benefit,
            submitted_at=datetime.now(timezone.utc)
        )
        await self.db.projects.insert_one(project.model_dump())
        
        # Analizar archivos adjuntos
        attachments_content = ""
        if sib.attachments:
            logger.info(f"Analizando {len(sib.attachments)} archivos adjuntos...")
            analysis = self.file_analysis.analyze_attachments(sib.attachments)
            attachments_content = analysis['combined_text']
        
        # Transición: INTAKE → VALIDACION_PARALELA
        await self._transition_state(project_id, ProjectState.VALIDACION_PARALELA, "A2-PMO inicia validaciones paralelas")
        
        # ===== PASO 2: VALIDACIÓN PARALELA (A1, A3, A5) =====
        # IMPORTANTE: Agentes NO envían emails individuales al sponsor
        # Solo generan análisis y PDFs para la discusión interna
        
        logger.info(f"[STATE MACHINE] VALIDACION_PARALELA: Generando análisis (SIN enviar al sponsor)")
        
        sib_with_files = sib.model_dump()
        if attachments_content:
            sib_with_files['attachments_content'] = attachments_content
        
        # A1-Sponsor: Validación estratégica (solo análisis, SIN email al sponsor)
        strategic_val = await self.agent_service.validate_strategic_alignment(sib_with_files)
        strategic_decision = self._extract_decision(strategic_val['analysis'])
        strategic_pdf = self.report_generator.generate_agent_report(
            project_id=project_id,
            agent_id="A1_SPONSOR",
            agent_name="María Rodríguez",
            agent_role="sponsor",
            report_type="Estrategico",
            version=1,
            project_data=sib_with_files,
            analysis=strategic_val['analysis'],
            decision=strategic_decision,
            findings=["Análisis estratégico completado"],
            recommendations=[]
        )
        
        # A3-Fiscal: Validación fiscal (solo análisis, SIN email al sponsor)
        fiscal_val = await self.agent_service.validate_fiscal_compliance(sib_with_files)
        fiscal_decision = self._extract_decision(fiscal_val['analysis'])
        fiscal_pdf = self.report_generator.generate_agent_report(
            project_id=project_id,
            agent_id="A3_FISCAL",
            agent_name="Laura Sánchez",
            agent_role="fiscal",
            report_type="Fiscal",
            version=1,
            project_data=sib_with_files,
            analysis=fiscal_val['analysis'],
            decision=fiscal_decision,
            findings=["Análisis fiscal completado"],
            recommendations=[]
        )
        
        # A5-Finanzas: Validación financiera (solo análisis, SIN email al sponsor)
        financial_val = await self.agent_service.verify_budget(sib_with_files, {"po_amount": sib.budget_estimate})
        financial_decision = self._extract_decision(financial_val['analysis'])
        financial_pdf = self.report_generator.generate_agent_report(
            project_id=project_id,
            agent_id="A5_FINANZAS",
            agent_name="Roberto Torres",
            agent_role="finanzas",
            report_type="Financiero",
            version=1,
            project_data=sib_with_files,
            analysis=financial_val['analysis'],
            decision=financial_decision,
            findings=["Análisis financiero completado"],
            recommendations=[]
        )
        
        # ===== PASO 3: DISCUSIÓN ENTRE AGENTES (3-5 RONDAS) =====
        # Los agentes NO envían emails individuales al sponsor todavía
        # Primero discuten ENTRE ELLOS
        
        logger.info(f"[STATE MACHINE] Iniciando discusión entre agentes (3-5 rondas)")
        
        # Preparar análisis iniciales con PDFs
        initial_analyses = {
            "A1_SPONSOR": {
                "analysis": strategic_val['analysis'],
                "decision": strategic_decision,
                "pdf_path": f"/app/backend{strategic_pdf}" if strategic_pdf else None
            },
            "A3_FISCAL": {
                "analysis": fiscal_val['analysis'],
                "decision": fiscal_decision,
                "pdf_path": f"/app/backend{fiscal_pdf}" if fiscal_pdf else None
            },
            "A5_FINANZAS": {
                "analysis": financial_val['analysis'],
                "decision": financial_decision,
                "pdf_path": f"/app/backend{financial_pdf}" if financial_pdf else None
            }
        }
        
        # Iniciar sistema de discusión iterativa
        discussion_result = await self.discussion_service.initiate_discussion(
            project_id=project_id,
            project_data=sib.model_dump(),
            initial_analyses=initial_analyses
        )
        
        logger.info(f"[STATE MACHINE] Discusión completada: {discussion_result.get('status')}")
        
        return {
            "project_id": project_id,
            "stage_1_status": discussion_result.get('status'),
            "rounds_completed": discussion_result.get('rounds_completed', 0),
            "next_stage": discussion_result.get('next_stage', 'PENDING')
        }
    
    async def _handle_revision_cycle(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        cycle: int,
        decisions: Dict[str, str],
        validations: Dict[str, Dict],
        pdfs: Dict[str, str]
    ):
        """Maneja un ciclo de revisión iterativa"""
        
        if self.state_machine.should_escalate_to_human(cycle):
            logger.warning(f"[STATE MACHINE] Límite de ciclos alcanzado ({cycle}). Escalando a humano.")
            await self._transition_state(project_id, ProjectState.ESCALADO_HUMANO, f"No se alcanzó consenso después de {cycle} ciclos")
            await self._send_escalation_email(project_id, sib, decisions, validations)
            return
        
        await self._transition_state(project_id, ProjectState.REVISION_ITERATIVA, f"Iniciando ciclo de revisión {cycle}")
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"revision_cycle": cycle}}
        )
        
        logger.info(f"[STATE MACHINE] A2-PMO genera reporte consolidado C{cycle}")
        
        agent_decisions_data = {
            agent_id: {
                "agent_name": AGENT_CONFIGURATIONS[agent_id]["name"],
                "decision": dec,
                "summary": validations[agent_id]['analysis'][:300]
            }
            for agent_id, dec in decisions.items()
        }
        
        conflicts = self._identify_conflicts(decisions)
        
        consolidation = await self.agent_service.consolidate_validations([
            validations["A1_SPONSOR"],
            validations["A3_FISCAL"],
            validations["A5_FINANZAS"]
        ])
        
        consolidated_pdf = self.report_generator.generate_consolidated_report(
            project_id=project_id,
            cycle=cycle,
            project_data=sib.model_dump(),
            agent_decisions=agent_decisions_data,
            conflicts=conflicts,
            pmo_analysis=consolidation['analysis']
        )
        
        await self._send_revision_request_email(
            project_id=project_id,
            sib=sib,
            cycle=cycle,
            consolidated_pdf=consolidated_pdf,
            consolidation_analysis=consolidation['analysis']
        )
        
        logger.info(f"[STATE MACHINE] Ciclo {cycle} completado. Tomando decisión por mayoría de votos.")
        
        approvals = sum(1 for d in decisions.values() if d == AgentDecision.APROBADO)
        rejections = sum(1 for d in decisions.values() if d == AgentDecision.RECHAZADO)
        
        if approvals >= 2:
            final_state = ProjectState.APROBADO_F0
            logger.info(f"[STATE MACHINE] Decisión por mayoría: APROBADO ({approvals}/3 votos)")
        else:
            final_state = ProjectState.RECHAZADO_F0
            logger.info(f"[STATE MACHINE] Decisión por mayoría: RECHAZADO ({rejections}/3 votos)")
        
        await self._transition_state(project_id, final_state, f"Decisión por mayoría después de ciclo {cycle}")
        
        logger.info(f"📧 Carlos Mendoza (A2-PMO) enviando resumen ejecutivo final...")
        await self._send_pmo_final_summary(
            project_id=project_id,
            sib=sib,
            final_state=final_state,
            decisions=decisions,
            conflicts=conflicts,
            consolidation_analysis=consolidation['analysis']
        )
        

    async def _send_pmo_final_summary(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        final_state: ProjectState,
        decisions: Dict[str, str],
        conflicts: List[str],
        consolidation_analysis: str,
        po_path: Optional[str] = None
    ):
        """
        A2-PMO envía resumen ejecutivo final.
        
        This method:
        1. Sends internal summary email via Gmail (if available)
        2. Sends provider notification via DreamHost with all PDF attachments
        3. For approved projects, sends contract request to legal@revisar.ia
        """
        is_approved = final_state == ProjectState.APROBADO_F0
        decision_text = "APROBADO" if is_approved else "RECHAZADO"
        
        if self.gmail_service:
            subject = f"[A2-PMO] Resumen Ejecutivo: {sib.project_name[:40]} - {decision_text}"
            
            body = f"""Hola {sib.sponsor_name},

Soy Carlos Mendoza, Gerente de PMO de Revisar.ia.

Como orquestador del proceso de validación, te comparto mi consolidación ejecutiva.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 RESUMEN EJECUTIVO

Proyecto: {sib.project_name}
ID: {project_id}
Decisión Final: {decision_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗳️ VOTOS DE LOS AGENTES:
• María Rodríguez (Estrategia): {decisions.get('A1_SPONSOR', 'N/A')}
• Laura Sánchez (Fiscal): {decisions.get('A3_FISCAL', 'N/A')}
• Roberto Torres (Finanzas): {decisions.get('A5_FINANZAS', 'N/A')}

"""
            
            if conflicts:
                conflict_text = '\n'.join(['• ' + c for c in conflicts])
                body += f"""⚠️ CONFLICTOS DETECTADOS:
{conflict_text}

"""
            
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MI CONSOLIDACIÓN:

{consolidation_analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ya recibiste emails individuales de cada agente con sus análisis detallados y documentos en Drive.
Este es mi resumen ejecutivo como PMO.

Dashboard: https://enterprise-ai-agents-2.preview.emergentagent.com/project/{project_id}

Saludos,
Carlos Mendoza
Gerente de PMO
Revisar.ia

---
📧 pmo@revisar-ia.com
🏢 PMO - Revisar.ia
"""
            
            result = await self.gmail_service.send_email(to=sib.sponsor_email, subject=subject, body=body)

            if result and result.get('success'):
                logger.info(f"✅ Carlos Mendoza (A2-PMO) envió resumen ejecutivo interno: {result.get('message_id')}")
        
        logger.info(f"📧 Enviando notificación al proveedor/vendor vía DreamHost...")
        provider_result = await self._send_provider_notification(
            project_id=project_id,
            sib=sib,
            final_state=final_state,
            decisions=decisions,
            conflicts=conflicts,
            consolidation_analysis=consolidation_analysis,
            po_path=po_path
        )
        
        if is_approved:
            logger.info(f"📧 Proyecto APROBADO - Enviando solicitud de contrato a Legal...")
            legal_result = await self._send_legal_contract_request(
                project_id=project_id,
                sib=sib,
                consolidation_analysis=consolidation_analysis,
                po_path=po_path
            )
            
            if legal_result.get('success'):
                logger.info(f"✅ Solicitud de contrato enviada a legal@revisar-ia.com")
            else:
                logger.error(f"❌ Error enviando solicitud a Legal: {legal_result.get('error')}")
    
    def _extract_decision(self, analysis: str) -> str:
        """Extrae la decisión del análisis del agente"""
        analysis_lower = analysis.lower()
        
        if "aprobar" in analysis_lower or "aprobado" in analysis_lower or "recomiend" in analysis_lower and "aprobar" in analysis_lower:
            return AgentDecision.APROBADO
        elif "rechaz" in analysis_lower or "no aprobar" in analysis_lower or "no recomiend" in analysis_lower:
            return AgentDecision.RECHAZADO
        elif "condicion" in analysis_lower or "ajuste" in analysis_lower:
            return AgentDecision.CONDICIONAL
        else:
            return AgentDecision.PENDIENTE
    
    def _identify_conflicts(self, decisions: Dict[str, str]) -> List[str]:
        """Identifica conflictos entre las decisiones de los agentes"""
        conflicts = []
        
        decisions_list = list(decisions.values())
        unique_decisions = set(decisions_list)
        
        if len(unique_decisions) > 1:
            for agent_id, decision in decisions.items():
                agent_name = AGENT_CONFIGURATIONS[agent_id]["name"]
                if decisions_list.count(decision) == 1:  # Decisión única
                    conflicts.append(f"{agent_name} tiene postura diferente: {decision}")
        
        return conflicts
    
    async def _transition_state(self, project_id: str, new_state: ProjectState, reason: str):
        """Transiciona el proyecto a un nuevo estado"""
        # Obtener estado actual
        project = await self.db.projects.find_one({"project_id": project_id})
        current_state = project.get('workflow_state', 'INTAKE') if project else 'INTAKE'
        
        # Validar transición
        if not self.state_machine.can_transition(ProjectState(current_state), new_state):
            logger.warning(f"⚠️ Transición inválida: {current_state} → {new_state}")
        
        # Actualizar estado
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"workflow_state": new_state}}
        )
        
        # Log de transición
        transition_log = self.state_machine.create_state_transition_log(
            project_id, ProjectState(current_state), new_state, reason
        )
        await self.db.state_transitions.insert_one(transition_log)
        
        logger.info(f"[STATE MACHINE] {current_state} → {new_state}: {reason}")
    
    async def _finalize_phase_0(
        self,
        project_id: str,
        final_state: ProjectState,
        sib: StrategicInitiativeBrief,
        strategic_val: Dict,
        fiscal_val: Dict,
        financial_val: Dict
    ):
        """Finaliza Phase 0 y envía email al sponsor"""
        
        is_approved = final_state == ProjectState.APROBADO_F0
        
        # Actualizar status del proyecto
        if is_approved:
            await self.db.projects.update_one(
                {"project_id": project_id},
                {"$set": {
                    "current_status": ProjectStatus.APPROVED,
                    "approved_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            await self.db.projects.update_one(
                {"project_id": project_id},
                {"$set": {"current_status": ProjectStatus.REJECTED}}
            )
        
        # Enviar email al sponsor con resultados
        await self._send_final_decision_email(
            project_id=project_id,
            project_name=sib.project_name,
            sponsor_email=sib.sponsor_email,
            sponsor_name=sib.sponsor_name,
            is_approved=is_approved,
            strategic_val=strategic_val,
            fiscal_val=fiscal_val,
            financial_val=financial_val
        )
        
        logger.info(f"[STATE MACHINE] FASE 0 finalizada: {final_state}")
    
    async def _send_revision_request_email(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        cycle: int,
        consolidated_pdf: str,
        consolidation_analysis: str
    ):
        """A2-PMO envía email solicitando revisión cruzada"""
        if not self.gmail_service:
            logger.warning("Gmail no disponible - no se puede enviar solicitud de revisión")
            return
        
        subject = self.state_machine.format_email_subject(
            phase="0",
            state=ProjectState.REVISION_ITERATIVA,
            project_id=project_id,
            action=f"Solicitud de Revisión Cruzada - Ciclo {cycle}"
        )
        
        body = f"""
Estimados agentes,

Soy Carlos Mendoza (A2-PMO), orquestador de este proyecto.

**CONFLICTO DETECTADO EN VALIDACIONES**

Proyecto: {sib.project_name}
ID: {project_id}
Ciclo de Revisión: {cycle}

He consolidado las validaciones iniciales y detecté conflictos entre las posturas de los agentes.
Adjunto el Reporte Consolidado C{cycle} que incluye las opiniones de todos los agentes.

**INSTRUCCIONES:**
1. Revisen el reporte consolidado adjunto
2. Analicen los argumentos de los otros agentes
3. Emitan un nuevo dictamen V{cycle + 1}
4. Pueden mantener su postura o modificarla

**Análisis Consolidado:**
{consolidation_analysis[:500]}...

**PDF Consolidado:** {consolidated_pdf}

---
Carlos Mendoza - A2 PMO
Revisar.ia
"""
        
        # Enviar a legal@revisar-ia.com (cuenta compartida)
        result = await self.gmail_service.send_email(
            to=sib.sponsor_email,  # En producción, iría a cada agente
            subject=subject,
            body=body
        )

        if result and result.get('success'):
            logger.info(f"✅ Email de revisión C{cycle} enviado: {result.get('message_id')}")
    
    async def _send_final_decision_email(
        self,
        project_id: str,
        project_name: str,
        sponsor_email: str,
        sponsor_name: str,
        is_approved: bool,
        strategic_val: Dict,
        fiscal_val: Dict,
        financial_val: Dict
    ):
        """Envía email final con decisión al sponsor"""
        if not self.gmail_service:
            logger.warning("Gmail no disponible")
            return
        
        subject = self.state_machine.format_email_subject(
            phase="0",
            state=ProjectState.APROBADO_F0 if is_approved else ProjectState.RECHAZADO_F0,
            project_id=project_id,
            action="Decisión Final"
        )
        
        decision = "✅ PROYECTO APROBADO" if is_approved else "❌ PROYECTO RECHAZADO"
        
        body = f"""
Estimado/a {sponsor_name},

{decision}

**Proyecto:** {project_name}
**ID:** {project_id}
**Decisión:** {"APROBADO - Procede a Stage 2" if is_approved else "RECHAZADO - Requiere ajustes"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **VALIDACIÓN ESTRATÉGICA** (María Rodríguez - A1 Sponsor)
{strategic_val['analysis'][:700]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **VALIDACIÓN FISCAL** (Laura Sánchez - A3 Fiscal)
{fiscal_val['analysis'][:700]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 **VALIDACIÓN FINANCIERA** (Roberto Torres - A5 Finanzas)
{financial_val['analysis'][:700]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Próximos Pasos:**
{"✅ El proyecto avanzará a Stage 2: Formalización Legal y Financiera" if is_approved else "⚠️ Revisa las observaciones y realiza ajustes según las recomendaciones"}

Dashboard: https://enterprise-ai-agents-2.preview.emergentagent.com/project/{project_id}

---
Agent Network System - Revisar.ia
"""
        
        result = await self.gmail_service.send_email(to=sponsor_email, subject=subject, body=body)

        if result and result.get('success'):
            logger.info(f"✅ Email de decisión final enviado: {result.get('message_id')}")
    
    async def _send_escalation_email(
        self,
        project_id: str,
        sib: StrategicInitiativeBrief,
        decisions: Dict[str, str],
        validations: Dict[str, Dict]
    ):
        """Envía email al director cuando se escala por falta de consenso"""
        if not self.gmail_service:
            return
        
        subject = self.state_machine.format_email_subject(
            phase="0",
            state=ProjectState.ESCALADO_HUMANO,
            project_id=project_id,
            action="REQUIERE DECISIÓN EJECUTIVA"
        )
        
        body = f"""
**ESCALAMIENTO A DECISIÓN HUMANA REQUERIDO**

Proyecto: {sib.project_name}
ID: {project_id}

Los agentes IA no alcanzaron consenso después de múltiples ciclos de revisión.
Se requiere decisión ejecutiva del Director.

**Posiciones de los Agentes:**
- A1-Sponsor: {decisions.get('A1_SPONSOR', 'N/A')}
- A3-Fiscal: {decisions.get('A3_FISCAL', 'N/A')}
- A5-Finanzas: {decisions.get('A5_FINANZAS', 'N/A')}

Favor de revisar los reportes adjuntos y tomar una decisión final.

---
Carlos Mendoza - A2 PMO
"""

        await self.gmail_service.send_email(to=sib.sponsor_email, subject=subject, body=body)
