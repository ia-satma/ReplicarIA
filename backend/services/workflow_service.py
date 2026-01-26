import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from services.agent_service import AgentService, AGENT_CONFIGURATIONS
from services.gmail_service import GmailService
from services.file_analysis_service import FileAnalysisService
from models.projects import (
    Project, ProjectPhase, ProjectStatus,
    StrategicInitiativeBrief, ValidationReport, Evidence
)
from models.agents import AgentInteraction

logger = logging.getLogger(__name__)

class WorkflowService:
    """Servicio que maneja el flujo completo de 5 etapas del proyecto"""
    
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.agent_service = AgentService()
        self.file_analysis_service = FileAnalysisService()
        
        # Initialize Gmail service for agent communications (optional)
        self.gmail_service = None
        try:
            gmail_service = GmailService()
            if gmail_service.service:
                self.gmail_service = gmail_service
                logger.info("Gmail service initialized - Agents can send emails")
            else:
                logger.warning("Gmail service not available - Emails will be logged only")
        except Exception as e:
            logger.warning(f"Could not initialize Gmail service: {str(e)} - Continuing without email notifications")
    
    async def stage_1_intake_and_validation(self, sib_data: Dict) -> Dict:
        """
        ETAPA 1: INTAKE Y VALIDACIÓN ESTRATÉGICA (FASE 0)
        
        Flujo:
        1. Recibir SIB del formulario Wufoo
        2. Registrar en PPM y crear Defense File
        3. Validación estratégica (A1-Sponsor)
        4. Validación fiscal (A3-Fiscal)
        5. Consolidación (A2-PMO)
        6. Solicitar aprobación directiva (Humano)
        """
        logger.info(f"Iniciando STAGE 1: Intake para proyecto {sib_data.get('project_name')}")
        
        # 1. Crear SIB
        sib = StrategicInitiativeBrief(
            sib_id=str(uuid.uuid4()),
            project_name=sib_data['project_name'],
            sponsor_name=sib_data['sponsor_name'],
            sponsor_email=sib_data['sponsor_email'],
            department=sib_data.get('department', 'Unknown'),
            description=sib_data['description'],
            strategic_alignment=sib_data.get('strategic_alignment', ''),
            expected_economic_benefit=float(sib_data['expected_economic_benefit']),
            budget_estimate=float(sib_data['budget_estimate']),
            duration_months=int(sib_data.get('duration_months', 12)),
            attachments=sib_data.get('attachments', []),
            form_data=sib_data
        )
        
        # Guardar SIB en DB
        await self.db.strategic_briefs.insert_one(sib.model_dump())
        
        # 2. Crear proyecto en PPM
        project_id = str(uuid.uuid4())
        project = Project(
            project_id=project_id,
            sib_id=sib.sib_id,
            current_phase=ProjectPhase.PHASE_0_INTAKE,
            current_status=ProjectStatus.IN_VALIDATION,
            project_name=sib.project_name,
            sponsor_agent_id="A1_SPONSOR",
            description=sib.description,
            budget=sib.budget_estimate,
            expected_benefit=sib.expected_economic_benefit,
            submitted_at=datetime.now(timezone.utc)
        )
        
        await self.db.projects.insert_one(project.model_dump())
        
        # 2.5 ANALIZAR ARCHIVOS ADJUNTOS si existen
        attachments_analysis = ""
        if sib.attachments and len(sib.attachments) > 0:
            logger.info(f"Analizando {len(sib.attachments)} archivos adjuntos...")
            analysis_result = self.file_analysis_service.analyze_attachments(sib.attachments)
            attachments_analysis = analysis_result['combined_text']
            logger.info(f"Archivos analizados: {analysis_result['total_files']}")
        
        # 3. Validación Estratégica (A1-Sponsor) CON ANÁLISIS DE ARCHIVOS
        logger.info(f"Ejecutando validación estratégica - A1-Sponsor")
        
        # Agregar contenido de archivos al contexto
        sib_data_with_files = sib.model_dump()
        if attachments_analysis:
            sib_data_with_files['attachments_content'] = attachments_analysis
        
        strategic_validation = await self.agent_service.validate_strategic_alignment(
            sib_data_with_files
        )
        
        # Registrar interacción
        await self._log_interaction(
            project_id=project_id,
            phase="phase_0_intake",
            from_agent="SYSTEM",
            to_agent="A1_SPONSOR",
            interaction_type="strategic_validation",
            content=f"Validar alineación estratégica de {sib.project_name}",
            llm_response=strategic_validation['analysis']
        )
        
        # Guardar reporte de validación
        strategic_report = ValidationReport(
            report_id=str(uuid.uuid4()),
            project_id=project_id,
            agent_id="A1_SPONSOR",
            agent_role="sponsor",
            validation_type="strategic",
            is_approved="aprobar" in strategic_validation['analysis'].lower(),
            findings=["Análisis estratégico completado"],
            recommendations=["Ver reporte detallado"],
            risk_level="medium",
            llm_analysis=strategic_validation['analysis']
        )
        await self.db.validation_reports.insert_one(strategic_report.model_dump())
        
        # 4. Validación Fiscal (A3-Fiscal)
        logger.info(f"Ejecutando validación fiscal - A3-Fiscal")
        fiscal_validation = await self.agent_service.validate_fiscal_compliance(
            sib.model_dump()
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_0_intake",
            from_agent="SYSTEM",
            to_agent="A3_FISCAL",
            interaction_type="fiscal_validation",
            content=f"Validar razón de negocios y cumplimiento fiscal",
            llm_response=fiscal_validation['analysis']
        )
        
        fiscal_report = ValidationReport(
            report_id=str(uuid.uuid4()),
            project_id=project_id,
            agent_id="A3_FISCAL",
            agent_role="fiscal",
            validation_type="fiscal",
            is_approved="aprobar" in fiscal_validation['analysis'].lower() or 
                        "cumple" in fiscal_validation['analysis'].lower(),
            findings=["Análisis fiscal completado"],
            recommendations=["Ver reporte detallado"],
            risk_level="low",
            llm_analysis=fiscal_validation['analysis']
        )
        await self.db.validation_reports.insert_one(fiscal_report.model_dump())
        
        # 5. Consolidación PMO (A2-PMO)
        logger.info(f"Consolidando validaciones - A2-PMO")
        consolidation = await self.agent_service.consolidate_validations([
            strategic_validation,
            fiscal_validation
        ])
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_0_intake",
            from_agent="MULTIPLE",
            to_agent="A2_PMO",
            interaction_type="consolidation",
            content="Consolidar validaciones de Sponsor y Fiscal",
            llm_response=consolidation['analysis']
        )
        
        pmo_report = ValidationReport(
            report_id=str(uuid.uuid4()),
            project_id=project_id,
            agent_id="A2_PMO",
            agent_role="pmo",
            validation_type="consolidation",
            is_approved=strategic_report.is_approved and fiscal_report.is_approved,
            findings=["Consolidación de validaciones completada"],
            recommendations=["Ver reporte consolidado"],
            risk_level="medium",
            llm_analysis=consolidation['analysis']
        )
        await self.db.validation_reports.insert_one(pmo_report.model_dump())
        
        # 6. Actualizar estado del proyecto
        if pmo_report.is_approved:
            await self.db.projects.update_one(
                {"project_id": project_id},
                {"$set": {
                    "current_status": ProjectStatus.APPROVED,
                    "approved_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        # 7. ENVIAR EMAIL AL SPONSOR CON RESULTADOS
        await self._send_validation_summary_email(
            project_id=project_id,
            project_name=sib.project_name,
            sponsor_email=sib.sponsor_email,
            sponsor_name=sib.sponsor_name,
            strategic_validation=strategic_validation,
            fiscal_validation=fiscal_validation,
            consolidation=consolidation,
            is_approved=pmo_report.is_approved
        )
        
        logger.info(f"STAGE 1 completado para proyecto {project_id}")
        
        return {
            "stage": "1_intake_validation",
            "project_id": project_id,
            "sib_id": sib.sib_id,
            "status": "approved" if pmo_report.is_approved else "requires_corrections",
            "validations": {
                "strategic": {
                    "approved": strategic_report.is_approved,
                    "analysis": strategic_validation['analysis']
                },
                "fiscal": {
                    "approved": fiscal_report.is_approved,
                    "analysis": fiscal_validation['analysis']
                },
                "consolidation": {
                    "approved": pmo_report.is_approved,
                    "analysis": consolidation['analysis']
                }
            }
        }
    
    async def stage_2_legal_and_financial(self, project_id: str) -> Dict:
        """
        ETAPA 2: FORMALIZACIÓN LEGAL Y FINANCIERA (FASES 1 Y 2)
        
        Flujo:
        1. Proceso de adquisición (selección proveedor)
        2. Verificación presupuestal (A5-Finanzas)
        3. Generación de PO
        4. Generación contractual (A4-Legal - Humano)
        5. Firma y validación de fecha cierta
        """
        logger.info(f"Iniciando STAGE 2: Legal y Financial para proyecto {project_id}")
        
        # Obtener proyecto
        project_data = await self.db.projects.find_one({"project_id": project_id})
        if not project_data:
            raise ValueError(f"Project {project_id} not found")
        
        # 1. Simulación de selección de proveedor
        logger.info("Fase 1: Selección de proveedor")
        provider_selection = {
            "provider_id": "PROVEEDOR_IA",
            "provider_name": "ProveedorIA S.A. de C.V.",
            "selected_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_1_ACQUISITION,
                "metadata.provider": provider_selection
            }}
        )
        
        # 2. Verificación presupuestal (A5-Finanzas)
        logger.info("Verificación presupuestal - A5-Finanzas")
        budget_validation = await self.agent_service.verify_budget(
            project_data,
            {"po_amount": project_data['budget']}
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_1_acquisition",
            from_agent="SYSTEM",
            to_agent="A5_FINANZAS",
            interaction_type="budget_verification",
            content="Verificar disponibilidad presupuestal y generar PO",
            llm_response=budget_validation['analysis']
        )
        
        # 3. Generar PO (Purchase Order)
        po_number = f"PO-{project_id[:8].upper()}"
        po_data = {
            "po_number": po_number,
            "project_id": project_id,
            "provider": provider_selection['provider_name'],
            "amount": project_data['budget'],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "issued"
        }
        
        await self.db.purchase_orders.insert_one(po_data)
        
        # 4. Generación contractual - Marcado para intervención humana (Legal)
        logger.info("Fase 2: Generación contractual - Requiere intervención humana")
        
        contract_draft = {
            "contract_id": f"CTR-{project_id[:8].upper()}",
            "project_id": project_id,
            "po_number": po_number,
            "status": "pending_legal_review",
            "requires_human_review": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Contrato y SOW requieren revisión legal humana (A4-Legal)"
        }
        
        await self.db.contracts.insert_one(contract_draft)
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_2_CONTRACTUAL,
                "current_status": ProjectStatus.CONTRACTED
            }}
        )
        
        logger.info(f"STAGE 2 completado para proyecto {project_id}")
        
        return {
            "stage": "2_legal_financial",
            "project_id": project_id,
            "provider": provider_selection,
            "po_number": po_number,
            "contract_id": contract_draft['contract_id'],
            "budget_validation": budget_validation['analysis'],
            "status": "awaiting_legal_review"
        }
    
    async def stage_3_execution_monitoring(self, project_id: str) -> Dict:
        """
        ETAPA 3: EJECUCIÓN Y MONITOREO DE MATERIALIDAD (FASES 3 Y 4)
        
        Flujo:
        1. Ejecución del servicio (Proveedor)
        2. Monitoreo continuo de materialidad (A3-Fiscal)
        3. Gestión de cronograma (A2-PMO)
        4. Gestión de cambios si aplica
        """
        logger.info(f"Iniciando STAGE 3: Execution Monitoring para proyecto {project_id}")
        
        project_data = await self.db.projects.find_one({"project_id": project_id})
        if not project_data:
            raise ValueError(f"Project {project_id} not found")
        
        # 1. Simular ejecución del proveedor
        logger.info("Fase 3: Ejecución del servicio por proveedor")
        
        execution_log = {
            "execution_id": str(uuid.uuid4()),
            "project_id": project_id,
            "provider": "PROVEEDOR_IA",
            "activities": [
                "Análisis regulatorio con IA",
                "Optimización de procesos Lean",
                "Modelado financiero algorítmico"
            ],
            "evidence_generated": [
                "logs_api_sistema.json",
                "reporte_analisis_regulatorio.pdf",
                "modelo_financiero_optimizado.xlsx"
            ],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress"
        }
        
        await self.db.execution_logs.insert_one(execution_log)
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_3_EXECUTION,
                "current_status": ProjectStatus.IN_EXECUTION,
                "started_at": execution_log['started_at']
            }}
        )
        
        # 2. Monitoreo de materialidad (A3-Fiscal)
        logger.info("Monitoreo de materialidad - A3-Fiscal")
        
        materiality_context = f"""
Proyecto: {project_data['project_name']}
Actividades ejecutadas: {', '.join(execution_log['activities'])}
Evidencia generada: {', '.join(execution_log['evidence_generated'])}
"""
        
        materiality_check = await self.agent_service.agent_analyze(
            "A3_FISCAL",
            materiality_context,
            "Analiza si la evidencia generada es suficiente para demostrar materialidad del servicio conforme a normativa fiscal mexicana."
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_3_execution",
            from_agent="PROVEEDOR_IA",
            to_agent="A3_FISCAL",
            interaction_type="materiality_monitoring",
            content="Verificar materialidad de evidencia generada",
            llm_response=materiality_check
        )
        
        logger.info(f"STAGE 3 completado para proyecto {project_id}")
        
        return {
            "stage": "3_execution_monitoring",
            "project_id": project_id,
            "execution": execution_log,
            "materiality_check": materiality_check,
            "status": "executing"
        }
    
    async def stage_4_delivery_audit(self, project_id: str, deliverables: List[str]) -> Dict:
        """
        ETAPA 4: ENTREGA Y AUDITORÍA DE CUMPLIMIENTO (FASES 5, 6 Y 7)
        
        Flujo:
        1. Recepción de entregables
        2. Validación técnica (A1-Sponsor)
        3. Aceptación formal
        4. Auditoría de cumplimiento (A3-Fiscal + Legal)
        5. Generación de VBC (Visto Bueno de Cumplimiento)
        """
        logger.info(f"Iniciando STAGE 4: Delivery Audit para proyecto {project_id}")
        
        project_data = await self.db.projects.find_one({"project_id": project_id})
        if not project_data:
            raise ValueError(f"Project {project_id} not found")
        
        # 1. Registrar entregables
        logger.info("Fase 5: Recepción de entregables")
        
        delivery_record = {
            "delivery_id": str(uuid.uuid4()),
            "project_id": project_id,
            "deliverables": deliverables,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "status": "received"
        }
        
        await self.db.deliveries.insert_one(delivery_record)
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"current_phase": ProjectPhase.PHASE_5_DELIVERY}}
        )
        
        # 2. Validación técnica (A1-Sponsor)
        logger.info("Fase 6: Validación técnica - A1-Sponsor")
        
        validation_context = f"""
Proyecto: {project_data['project_name']}
Entregables recibidos:
{chr(10).join([f"- {d}" for d in deliverables])}
Requirements originales: {project_data['description']}
"""
        
        technical_validation = await self.agent_service.agent_analyze(
            "A1_SPONSOR",
            validation_context,
            "Valida técnicamente los entregables contra los requisitos del proyecto. ¿Cumplen con lo esperado?"
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_6_validation",
            from_agent="PROVEEDOR_IA",
            to_agent="A1_SPONSOR",
            interaction_type="technical_validation",
            content="Validar entregables técnicamente",
            llm_response=technical_validation
        )
        
        # 3. Auditoría de cumplimiento (A3-Fiscal)
        logger.info("Fase 7: Auditoría de cumplimiento - A3-Fiscal")
        
        audit_context = f"""
Proyecto: {project_data['project_name']}
Monto: ${project_data['budget']:,.2f} MXN
Entregables: {', '.join(deliverables)}
Validación Técnica: {technical_validation[:200]}...
"""
        
        compliance_audit = await self.agent_service.agent_analyze(
            "A3_FISCAL",
            audit_context,
            "Realiza auditoría de cumplimiento fiscal. ¿La evidencia es suficiente? ¿Se puede emitir VBC (Visto Bueno de Cumplimiento)?"
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_7_audit",
            from_agent="A1_SPONSOR",
            to_agent="A3_FISCAL",
            interaction_type="compliance_audit",
            content="Auditoría final de cumplimiento",
            llm_response=compliance_audit
        )
        
        # 4. Generar VBC
        vbc_record = {
            "vbc_id": f"VBC-{project_id[:8].upper()}",
            "project_id": project_id,
            "status": "approved" if "aprobar" in compliance_audit.lower() or "satisfactorio" in compliance_audit.lower() else "pending",
            "technical_validation": technical_validation,
            "compliance_audit": compliance_audit,
            "issued_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.vbc_records.insert_one(vbc_record)
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_7_AUDIT,
                "current_status": ProjectStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"STAGE 4 completado para proyecto {project_id}")
        
        return {
            "stage": "4_delivery_audit",
            "project_id": project_id,
            "deliverables": deliverables,
            "technical_validation": technical_validation,
            "compliance_audit": compliance_audit,
            "vbc_id": vbc_record['vbc_id'],
            "vbc_status": vbc_record['status'],
            "status": "completed"
        }
    
    async def stage_5_closure_impact(self, project_id: str) -> Dict:
        """
        ETAPA 5: CIERRE Y MEDICIÓN DE IMPACTO (FASES 8 Y 9)
        
        Flujo:
        1. Proceso de pago automatizado (3-Way Match - A5-Finanzas)
        2. Cierre administrativo
        3. Medición de impacto (A1-Sponsor + A5-Finanzas)
        4. Trazabilidad posterior (A3-Fiscal)
        """
        logger.info(f"Iniciando STAGE 5: Closure Impact para proyecto {project_id}")
        
        project_data = await self.db.projects.find_one({"project_id": project_id})
        if not project_data:
            raise ValueError(f"Project {project_id} not found")
        
        # 1. 3-Way Match (A5-Finanzas)
        logger.info("Fase 8: 3-Way Match - A5-Finanzas")

        # Obtener PO y VBC con validación de null
        po_data = await self.db.purchase_orders.find_one({"project_id": project_id})
        vbc_data = await self.db.vbc_records.find_one({"project_id": project_id})

        # Validar que existan los registros necesarios
        if not po_data:
            logger.error(f"❌ Stage 5 failed: No Purchase Order found for project {project_id}")
            return {
                "status": "error",
                "error": "No se encontró Orden de Compra (PO) para este proyecto. Verifique que Stage 2 se haya completado correctamente.",
                "stage": 5,
                "project_id": project_id
            }

        if not vbc_data:
            logger.error(f"❌ Stage 5 failed: No VBC record found for project {project_id}")
            return {
                "status": "error",
                "error": "No se encontró registro de Visto Bueno de Cumplimiento (VBC). Verifique que Stage 4 se haya completado correctamente.",
                "stage": 5,
                "project_id": project_id
            }

        match_context = f"""
Proyecto: {project_data['project_name']}
PO: {po_data.get('po_number', 'N/A')} - ${po_data.get('amount', 0):,.2f} MXN
VBC: {vbc_data.get('vbc_id', 'N/A')} - Status: {vbc_data.get('status', 'unknown')}
Acta de Entrega-Recepción: Firmada y archivada
"""
        
        three_way_match = await self.agent_service.agent_analyze(
            "A5_FINANZAS",
            match_context,
            "Ejecuta 3-Way Match validando PO, Acta de Entrega y VBC. ¿Procede liberar el pago?"
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_8_payment",
            from_agent="SYSTEM",
            to_agent="A5_FINANZAS",
            interaction_type="three_way_match",
            content="Ejecutar 3-Way Match y liberar pago",
            llm_response=three_way_match
        )
        
        # 2. Registrar pago
        payment_record = {
            "payment_id": f"PAY-{project_id[:8].upper()}",
            "project_id": project_id,
            "po_number": po_data.get('po_number', 'N/A'),
            "amount": po_data.get('amount', 0),
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "status": "processed" if "aprobar" in three_way_match.lower() or "liberar" in three_way_match.lower() else "pending",
            "three_way_match_result": three_way_match
        }
        
        await self.db.payments.insert_one(payment_record)
        
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_8_PAYMENT,
                "actual_cost": po_data['amount']
            }}
        )
        
        # 3. Medición de impacto (A1-Sponsor + A5-Finanzas)
        logger.info("Fase 9: Medición de impacto")
        
        impact_context = f"""
Proyecto: {project_data['project_name']}
Beneficio Económico Esperado: ${project_data['expected_benefit']:,.2f} MXN
Costo Real: ${project_data.get('actual_cost', 0):,.2f} MXN
Duración Real: [A calcular en producción]
"""
        
        impact_analysis = await self.agent_service.agent_analyze(
            "A1_SPONSOR",
            impact_context,
            "Analiza el impacto real del proyecto comparado con el BEE inicial. ¿Se lograron los objetivos?"
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_9_closure",
            from_agent="SYSTEM",
            to_agent="A1_SPONSOR",
            interaction_type="impact_measurement",
            content="Medir impacto real vs. esperado",
            llm_response=impact_analysis
        )
        
        # 4. Trazabilidad posterior (A3-Fiscal)
        traceability_validation = await self.agent_service.agent_analyze(
            "A3_FISCAL",
            f"Proyecto: {project_data['project_name']}\nEstado: Cerrado\nToda documentación archivada en Defense File",
            "Valida que la trazabilidad posterior está completa para futuras auditorías."
        )
        
        await self._log_interaction(
            project_id=project_id,
            phase="phase_9_closure",
            from_agent="A1_SPONSOR",
            to_agent="A3_FISCAL",
            interaction_type="traceability_validation",
            content="Validar trazabilidad posterior",
            llm_response=traceability_validation
        )
        
        # 5. Cerrar proyecto
        await self.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "current_phase": ProjectPhase.PHASE_9_CLOSURE,
                "current_status": ProjectStatus.CLOSED,
                "closed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"STAGE 5 completado - Proyecto {project_id} CERRADO")
        
        return {
            "stage": "5_closure_impact",
            "project_id": project_id,
            "payment": payment_record,
            "three_way_match": three_way_match,
            "impact_analysis": impact_analysis,
            "traceability_validation": traceability_validation,
            "status": "closed"
        }
    
    async def _log_interaction(self, project_id: str, phase: str, from_agent: str,
                               to_agent: str, interaction_type: str, content: str,
                               llm_response: Optional[str] = None):
        """Registrar interacción entre agentes y enviar email real"""
        interaction = AgentInteraction(
            interaction_id=str(uuid.uuid4()),
            project_id=project_id,
            phase=phase,
            from_agent=from_agent,
            to_agent=to_agent,
            interaction_type=interaction_type,
            content=content,
            llm_response=llm_response,
            timestamp=datetime.now(timezone.utc),
            metadata={}
        )
        
        await self.db.agent_interactions.insert_one(interaction.model_dump())
        logger.info(f"Logged interaction: {from_agent} -> {to_agent} ({interaction_type})")
        
        # ENVIAR EMAIL REAL ENTRE AGENTES
        if self.gmail_service and from_agent != "SYSTEM" and to_agent != "SYSTEM":
            try:
                # Get agent configurations
                from_config = AGENT_CONFIGURATIONS.get(from_agent, {})
                to_config = AGENT_CONFIGURATIONS.get(to_agent, {})
                
                if from_config and to_config:
                    # Compose email
                    from_name = from_config.get('name', from_agent)
                    from_role = from_config.get('role', 'Agent')
                    to_email = to_config.get('email', '')
                    
                    # Get project details
                    project = await self.db.projects.find_one({"project_id": project_id})
                    project_name = project.get('project_name', 'Proyecto') if project else 'Proyecto'
                    
                    subject = f"[Agent Network] {interaction_type.replace('_', ' ').title()} - {project_name}"
                    
                    # Build email body with agent personality
                    body = f"""
Hola equipo,

{from_name} ({from_role}) necesita tu input sobre el proyecto "{project_name}".

**Tipo de interacción:** {interaction_type.replace('_', ' ').title()}
**Fase del proyecto:** {phase}

**Mensaje:**
{content}

"""
                    
                    if llm_response:
                        # Truncate long responses for email
                        response_preview = llm_response[:500] + "..." if len(llm_response) > 500 else llm_response
                        body += f"""
**Análisis/Respuesta:**
{response_preview}

"""
                    
                    body += f"""
**ID del Proyecto:** {project_id}
**ID de Interacción:** {interaction.interaction_id}

---
Enviado automáticamente por Agent Network System
Timestamp: {interaction.timestamp.isoformat()}
"""
                    
                    # Send email to legal agent
                    email_result = await self.gmail_service.send_email(
                        to="legal@revisar-ia.com",
                        subject=subject,
                        body=body
                    )

                    if email_result and email_result.get('success'):
                        logger.info(f"✅ Email sent: {from_name} -> {to_config.get('name', to_agent)} (Message ID: {email_result.get('message_id')})")
                        
                        # Update interaction with email info
                        await self.db.agent_interactions.update_one(
                            {"interaction_id": interaction.interaction_id},
                            {"$set": {
                                "metadata.email_sent": True,
                                "metadata.email_message_id": email_result.get('message_id'),
                                "metadata.email_timestamp": email_result.get('timestamp')
                            }}
                        )
                    else:
                        logger.warning(f"❌ Failed to send email: {email_result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error sending agent email: {str(e)}")
                # Don't fail the workflow if email fails
                pass
    
    async def get_project_status(self, project_id: str) -> Dict:
        """Obtener estado completo del proyecto"""
        project = await self.db.projects.find_one({"project_id": project_id}, {"_id": 0})
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Obtener interacciones
        interactions = await self.db.agent_interactions.find(
            {"project_id": project_id}, {"_id": 0}
        ).sort("timestamp", 1).to_list(100)
        
        # Obtener validaciones
        validations = await self.db.validation_reports.find(
            {"project_id": project_id}, {"_id": 0}
        ).to_list(50)
        
        return {
            "project": project,
            "interactions": interactions,
            "validations": validations,
            "timeline": self._build_timeline(interactions)
        }
    

    async def _send_validation_summary_email(
        self,
        project_id: str,
        project_name: str,
        sponsor_email: str,
        sponsor_name: str,
        strategic_validation: Dict,
        fiscal_validation: Dict,
        consolidation: Dict,
        is_approved: bool
    ):
        """Enviar email al sponsor con resumen de validaciones de Stage 1"""
        if not self.gmail_service:
            logger.warning("Gmail service not available - Cannot send validation summary")
            return
        
        try:
            subject = f"[Agent Network] Validación Completada - {project_name}"
            
            # Determinar decisión
            decision = "✅ PROYECTO APROBADO" if is_approved else "⚠️ PROYECTO REQUIERE CORRECCIONES"
            decision_color = "green" if is_approved else "orange"
            
            body = f"""
Estimado/a {sponsor_name},

{decision}

El proyecto "{project_name}" ha completado la fase de validación inicial (Stage 1) con nuestros agentes de IA especializados.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 VALIDACIÓN ESTRATÉGICA (María Rodríguez - A1 Sponsor)
Modelo: Claude 3.7 Sonnet

{strategic_validation['analysis'][:800]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 VALIDACIÓN FISCAL (Laura Sánchez - A3 Fiscal)
Modelo: Claude 3.7 Sonnet

{fiscal_validation['analysis'][:800]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤝 CONSOLIDACIÓN PMO (Carlos Mendoza - A2 PMO)
Modelo: Claude 3.7 Sonnet

{consolidation['analysis'][:800]}...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRÓXIMOS PASOS:
"""
            
            if is_approved:
                body += """
✅ El proyecto ha sido aprobado para continuar a Stage 2 (Formalización Legal y Financiera)
✅ Recibirás notificaciones adicionales cuando el proceso avance
✅ Puedes ver el estado completo en el dashboard

"""
            else:
                body += """
⚠️ Por favor revisa las observaciones de los agentes
⚠️ Realiza los ajustes necesarios y vuelve a enviar el proyecto
⚠️ Contacta a los agentes para aclaraciones si lo requieres

"""
            
            body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 INFORMACIÓN DEL PROYECTO:
• ID del Proyecto: {project_id}
• Dashboard: https://enterprise-ai-agents-2.preview.emergentagent.com/project/{project_id}
• Fecha de Validación: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Este es un mensaje automático del Agent Network System.
Para consultas, contacta a: legal@revisar-ia.com

---
Revisar.ia - Agent Network System
"""
            
            # Enviar email
            email_result = await self.gmail_service.send_email(
                to=sponsor_email,
                subject=subject,
                body=body
            )

            if email_result and email_result.get('success'):
                logger.info(f"✅ Validation summary email sent to {sponsor_email} (Message ID: {email_result.get('message_id')})")
            else:
                logger.error(f"❌ Failed to send validation summary email: {email_result.get('error') if email_result else 'No result'}")
                
        except Exception as e:
            logger.error(f"Error sending validation summary email: {str(e)}")

    def _build_timeline(self, interactions: List[Dict]) -> List[Dict]:
        """Construir timeline visual del proyecto"""
        timeline = []
        for interaction in interactions:
            timeline.append({
                "timestamp": interaction['timestamp'],
                "phase": interaction['phase'],
                "event": f"{interaction['from_agent']} → {interaction['to_agent']}: {interaction['interaction_type']}",
                "details": interaction['content']
            })
        return timeline
