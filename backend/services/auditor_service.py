"""
A8_AUDITOR - Documentation Auditor Agent Service
Verifies document compliance, audits pCloud uploads, and communicates adjustments to providers
"""
import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from services.pcloud_service import PCloudService, AGENT_FOLDER_IDS
from services.dreamhost_email_service import DreamHostEmailService
from services.defense_file_service import defense_file_service

logger = logging.getLogger(__name__)

REQUIRED_DEFENSE_FILE_STRUCTURE = [
    "proyecto_info.json",
    "deliberaciones/",
    "comunicaciones/",
    "documentos_generados/",
    "rag_contexts/",
    "decision_final.json"
]

DOCUMENTO_CHECKLIST = {
    "documentos_proveedor": {
        "nombre": "Documentos del Proveedor",
        "descripcion": "Documentación legal y fiscal del proveedor de servicios",
        "requeridos": [
            {
                "id": "acta_constitutiva",
                "nombre": "Acta Constitutiva",
                "descripcion": "Acta constitutiva de la empresa proveedora con objeto social que incluya el servicio contratado",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Debe incluir objeto social compatible con el servicio"]
            },
            {
                "id": "opinion_cumplimiento_sat",
                "nombre": "Opinión de Cumplimiento SAT",
                "descripcion": "Opinión de cumplimiento de obligaciones fiscales vigente (32-D)",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["No mayor a 30 días", "Debe estar en positivo"]
            },
            {
                "id": "constancia_situacion_fiscal",
                "nombre": "Constancia de Situación Fiscal",
                "descripcion": "Constancia de situación fiscal del proveedor (CIF)",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Vigente", "RFC debe coincidir"]
            },
            {
                "id": "poder_representante",
                "nombre": "Poder del Representante Legal",
                "descripcion": "Poder notarial del representante legal para celebrar contratos",
                "obligatorio": False,
                "formatos": ["PDF"],
                "validaciones": ["Vigente", "Facultades suficientes"]
            }
        ]
    },
    "documentos_operacion": {
        "nombre": "Documentos de la Operación",
        "descripcion": "Documentación de soporte para la operación específica",
        "requeridos": [
            {
                "id": "orden_compra",
                "nombre": "Orden de Compra / Solicitud de Servicio",
                "descripcion": "Documento interno que autoriza la contratación del servicio",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Firmada por autorizador", "Monto debe coincidir"]
            },
            {
                "id": "contrato_servicios",
                "nombre": "Contrato de Prestación de Servicios",
                "descripcion": "Contrato firmado entre las partes con alcance, entregables y condiciones",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Firmado por ambas partes", "Incluye alcance detallado"]
            },
            {
                "id": "cotizacion_propuesta",
                "nombre": "Cotización / Propuesta Técnica",
                "descripcion": "Propuesta técnica y económica del proveedor",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Descripción detallada del servicio", "Precio desglosado"]
            },
            {
                "id": "factura_cfdi",
                "nombre": "Factura CFDI",
                "descripcion": "Comprobante Fiscal Digital por Internet emitido por el proveedor",
                "obligatorio": True,
                "formatos": ["PDF", "XML"],
                "validaciones": ["CFDI válido", "Monto y concepto correctos", "Timbre fiscal vigente"]
            },
            {
                "id": "comprobante_pago",
                "nombre": "Comprobante de Pago",
                "descripcion": "Comprobante de transferencia o pago realizado",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Monto coincide con factura", "Cuenta destino correcta"]
            }
        ]
    },
    "evidencia_materialidad": {
        "nombre": "Evidencia de Materialidad",
        "descripcion": "Documentación que demuestra que el servicio fue efectivamente prestado",
        "requeridos": [
            {
                "id": "entregables",
                "nombre": "Entregables del Servicio",
                "descripcion": "Documentos, reportes o productos resultado del servicio contratado",
                "obligatorio": True,
                "formatos": ["PDF", "DOCX", "XLSX", "PPT"],
                "validaciones": ["Fecha de entrega", "Contenido sustancial"]
            },
            {
                "id": "evidencia_reuniones",
                "nombre": "Evidencia de Reuniones / Comunicaciones",
                "descripcion": "Minutas de reuniones, correos electrónicos o comunicaciones del proyecto",
                "obligatorio": False,
                "formatos": ["PDF", "MSG", "EML"],
                "validaciones": ["Fechas durante vigencia del contrato"]
            },
            {
                "id": "carta_aceptacion",
                "nombre": "Carta de Aceptación / Conformidad",
                "descripcion": "Documento que confirma la recepción satisfactoria del servicio",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Firmada por receptor autorizado", "Descripción del servicio recibido"]
            }
        ]
    },
    "documentos_sistema": {
        "nombre": "Documentos Generados por el Sistema",
        "descripcion": "Reportes y análisis generados por los agentes de Revisar.ia",
        "requeridos": [
            {
                "id": "reporte_estrategia",
                "nombre": "Reporte de Análisis Estratégico",
                "descripcion": "Análisis del A1_SPONSOR sobre razón de negocios",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Generado automáticamente"]
            },
            {
                "id": "reporte_fiscal",
                "nombre": "Reporte de Análisis Fiscal",
                "descripcion": "Análisis del A3_FISCAL sobre cumplimiento tributario",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Generado automáticamente"]
            },
            {
                "id": "reporte_finanzas",
                "nombre": "Reporte de Análisis Financiero",
                "descripcion": "Análisis del A5_FINANZAS sobre viabilidad económica",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Generado automáticamente"]
            },
            {
                "id": "reporte_legal",
                "nombre": "Reporte de Análisis Legal",
                "descripcion": "Análisis del equipo legal sobre cumplimiento normativo",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Generado automáticamente"]
            },
            {
                "id": "consolidacion_pmo",
                "nombre": "Consolidación PMO",
                "descripcion": "Reporte consolidado del A2_PMO con recomendaciones finales",
                "obligatorio": True,
                "formatos": ["PDF"],
                "validaciones": ["Generado automáticamente"]
            },
            {
                "id": "bitacora_proyecto",
                "nombre": "Bitácora del Proyecto",
                "descripcion": "Registro completo de todas las acciones y decisiones del proyecto",
                "obligatorio": True,
                "formatos": ["PDF", "JSON"],
                "validaciones": ["Trazabilidad completa"]
            }
        ]
    }
}


class AuditorService:
    """
    A8_AUDITOR - Documentation Auditor Agent
    Responsible for:
    - Verifying PDF uploads to pCloud per stage/agent
    - Auditing Defense File ZIP structure
    - Sending adjustment emails to providers
    - Parsing adjustment requirements from deliberations
    """
    
    def __init__(self):
        self.pcloud = PCloudService()
        self.email_service = DreamHostEmailService()
        self.agent_id = "A8_AUDITOR"
        self.agent_name = "Auditor de Documentación"
        self.agent_email = "auditoria@revisar-ia.com"
        
    def _log_audit_action(self, action: str, project_id: str, details: Dict[str, Any]):
        """Log audit actions for traceability"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.agent_id,
            "action": action,
            "project_id": project_id,
            "details": details
        }
        logger.info(f"[AUDIT] {action} | Project: {project_id} | Details: {details}")
        return log_entry
    
    def audit_stage_upload(self, project_id: str, stage: str, agent_id: str) -> Dict[str, Any]:
        """
        Verify that a PDF was uploaded to pCloud for a specific stage/agent
        
        Args:
            project_id: The project identifier
            stage: The workflow stage (e.g., 'fiscal_review', 'finance_review')
            agent_id: The agent ID that should have uploaded (e.g., 'A3_FISCAL')
            
        Returns:
            Dict with audit results including success status and found documents
        """
        self._log_audit_action("audit_stage_upload_start", project_id, {
            "stage": stage,
            "agent_id": agent_id
        })
        
        try:
            login_result = self.pcloud.login()
            if not login_result.get("success"):
                return {
                    "success": False,
                    "audit_passed": False,
                    "error": "Failed to connect to pCloud",
                    "details": login_result
                }
            
            folder_id = AGENT_FOLDER_IDS.get(agent_id)
            if not folder_id:
                folder_id = AGENT_FOLDER_IDS.get(agent_id.upper())
            
            if not folder_id:
                return {
                    "success": False,
                    "audit_passed": False,
                    "error": f"No pCloud folder configured for agent {agent_id}",
                    "available_agents": list(AGENT_FOLDER_IDS.keys())
                }
            
            folder_contents = self.pcloud.list_folder(folder_id=folder_id)
            if not folder_contents.get("success"):
                return {
                    "success": False,
                    "audit_passed": False,
                    "error": "Failed to list pCloud folder",
                    "details": folder_contents
                }
            
            project_prefix = project_id[:8] if len(project_id) > 8 else project_id
            matching_files = []
            
            for item in folder_contents.get("items", []):
                if item.get("is_folder"):
                    continue
                filename = item.get("name", "")
                if project_prefix.lower() in filename.lower() and filename.lower().endswith(".pdf"):
                    matching_files.append({
                        "name": filename,
                        "id": item.get("id"),
                        "size": item.get("size"),
                        "modified": item.get("modified")
                    })
            
            audit_passed = len(matching_files) > 0
            
            result = {
                "success": True,
                "audit_passed": audit_passed,
                "project_id": project_id,
                "stage": stage,
                "agent_id": agent_id,
                "folder_id": folder_id,
                "files_found": len(matching_files),
                "matching_files": matching_files,
                "audited_at": datetime.now(timezone.utc).isoformat()
            }
            
            self._log_audit_action("audit_stage_upload_complete", project_id, {
                "audit_passed": audit_passed,
                "files_found": len(matching_files)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"[AUDIT] Error auditing stage upload: {str(e)}")
            return {
                "success": False,
                "audit_passed": False,
                "error": str(e),
                "project_id": project_id,
                "stage": stage,
                "agent_id": agent_id
            }
    
    def audit_defense_zip(self, project_id: str) -> Dict[str, Any]:
        """
        Verify that the Defense File ZIP has the correct structure
        
        Args:
            project_id: The project identifier
            
        Returns:
            Dict with audit results including structure validation
        """
        self._log_audit_action("audit_defense_zip_start", project_id, {})
        
        try:
            defense_file = defense_file_service.get_or_create(project_id)
            defense_data = defense_file.to_dict()
            
            structure_checks = {
                "has_project_data": bool(defense_data.get("project_data")),
                "has_deliberations": len(defense_data.get("deliberations", [])) > 0,
                "has_emails": len(defense_data.get("emails", [])) >= 0,
                "has_documents": len(defense_data.get("documents", [])) >= 0,
                "has_rag_contexts": len(defense_data.get("rag_contexts", [])) >= 0,
                "has_final_decision": defense_data.get("final_decision") is not None,
                "has_compliance_checklist": bool(defense_data.get("compliance_checklist"))
            }
            
            missing_elements = [k for k, v in structure_checks.items() if not v]
            
            compliance_checklist = defense_data.get("compliance_checklist", {})
            compliance_items = {
                "razon_de_negocios": compliance_checklist.get("razon_de_negocios", False),
                "beneficio_economico": compliance_checklist.get("beneficio_economico", False),
                "materialidad": compliance_checklist.get("materialidad", False),
                "trazabilidad": compliance_checklist.get("trazabilidad", False)
            }
            
            pcloud_audit = {
                "has_pcloud_links": bool(defense_data.get("pcloud_links")),
                "pcloud_document_count": len(defense_data.get("pcloud_documents", [])),
                "has_bitacora_link": defense_data.get("bitacora_link") is not None
            }
            
            required_elements = ["has_project_data", "has_deliberations", "has_final_decision"]
            audit_passed = all(structure_checks.get(elem, False) for elem in required_elements)
            
            result = {
                "success": True,
                "audit_passed": audit_passed,
                "project_id": project_id,
                "structure_checks": structure_checks,
                "missing_elements": missing_elements,
                "compliance_checklist": compliance_items,
                "compliance_score": defense_data.get("compliance_score", 0),
                "pcloud_audit": pcloud_audit,
                "deliberation_count": len(defense_data.get("deliberations", [])),
                "document_count": len(defense_data.get("documents", [])),
                "email_count": len(defense_data.get("emails", [])),
                "audit_ready": defense_data.get("audit_ready", False),
                "audited_at": datetime.now(timezone.utc).isoformat()
            }
            
            self._log_audit_action("audit_defense_zip_complete", project_id, {
                "audit_passed": audit_passed,
                "missing_elements": missing_elements,
                "compliance_score": defense_data.get("compliance_score", 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"[AUDIT] Error auditing defense file: {str(e)}")
            return {
                "success": False,
                "audit_passed": False,
                "error": str(e),
                "project_id": project_id
            }
    
    def extract_adjustments_from_analysis(self, analysis_text: str) -> List[Dict[str, str]]:
        """
        Parse adjustment requirements from deliberation analysis text
        
        Looks for patterns like:
        - [AJUSTE 1]: Description
        - ### AJUSTES REQUERIDOS ### ... ### FIN AJUSTES ###
        - Bullet points with adjustment keywords
        
        Args:
            analysis_text: The analysis text from agent deliberation
            
        Returns:
            List of adjustment dicts with 'id' and 'description'
        """
        adjustments = []
        
        ajuste_pattern = r'\[AJUSTE\s*(\d+)\]:\s*(.+?)(?=\[AJUSTE|\Z|###)'
        matches = re.findall(ajuste_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            adj_id = match[0].strip()
            description = match[1].strip()
            description = re.sub(r'\s+', ' ', description)
            if description:
                adjustments.append({
                    "id": f"AJUSTE_{adj_id}",
                    "description": description
                })
        
        if not adjustments:
            section_pattern = r'###\s*AJUSTES\s*REQUERIDOS\s*###(.+?)###\s*FIN\s*AJUSTES\s*###'
            section_match = re.search(section_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
            
            if section_match:
                section_text = section_match.group(1)
                lines = section_text.strip().split('\n')
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        line = re.sub(r'^[-•*]\s*', '', line)
                        line = re.sub(r'^\d+[.)]\s*', '', line)
                        if line:
                            adjustments.append({
                                "id": f"AJUSTE_{i}",
                                "description": line
                            })
        
        if not adjustments:
            keywords = [
                r'(?:se\s+)?(?:requiere|necesita|debe|falta)\s+(.+?)(?:\.|$)',
                r'(?:agregar|incluir|especificar|añadir)\s+(.+?)(?:\.|$)',
                r'(?:es\s+necesario|es\s+obligatorio)\s+(.+?)(?:\.|$)'
            ]
            
            for pattern in keywords:
                matches = re.findall(pattern, analysis_text, re.IGNORECASE)
                for i, match in enumerate(matches):
                    desc = match.strip()
                    if len(desc) > 10 and len(desc) < 500:
                        already_exists = any(adj["description"].lower() == desc.lower() for adj in adjustments)
                        if not already_exists:
                            adjustments.append({
                                "id": f"AJUSTE_{len(adjustments) + 1}",
                                "description": desc
                            })
        
        logger.info(f"[AUDIT] Extracted {len(adjustments)} adjustments from analysis")
        return adjustments
    
    def send_adjustment_email(
        self,
        project_id: str,
        agent_id: str,
        decision: str,
        adjustments: List[Dict[str, str]],
        provider_email: str
    ) -> Dict[str, Any]:
        """
        Send email to provider with required changes
        
        Args:
            project_id: The project identifier
            agent_id: The agent requesting adjustments
            decision: The review decision (e.g., 'REQUIRES_ADJUSTMENTS')
            adjustments: List of adjustment dicts with 'id' and 'description'
            provider_email: The provider's email address
            
        Returns:
            Dict with email send result
        """
        self._log_audit_action("send_adjustment_email_start", project_id, {
            "agent_id": agent_id,
            "decision": decision,
            "adjustment_count": len(adjustments),
            "provider_email": provider_email
        })
        
        try:
            deadline = datetime.now(timezone.utc) + timedelta(days=10)
            business_days = 0
            current = datetime.now(timezone.utc)
            while business_days < 7:
                current += timedelta(days=1)
                if current.weekday() < 5:
                    business_days += 1
            deadline = current
            deadline_str = deadline.strftime("%d de %B de %Y")
            
            month_translations = {
                "January": "enero", "February": "febrero", "March": "marzo",
                "April": "abril", "May": "mayo", "June": "junio",
                "July": "julio", "August": "agosto", "September": "septiembre",
                "October": "octubre", "November": "noviembre", "December": "diciembre"
            }
            for eng, esp in month_translations.items():
                deadline_str = deadline_str.replace(eng, esp)
            
            project_folder_id = AGENT_FOLDER_IDS.get("PROYECTOS", AGENT_FOLDER_IDS.get("A6_PROVEEDOR"))
            pcloud_upload_link = f"https://u.pcloud.link/publink/show?code={project_folder_id}"
            
            adjustments_list = "\n".join([
                f"   {i+1}. {adj['description']}"
                for i, adj in enumerate(adjustments)
            ])
            
            subject = f"Revisar.ia - Ajustes Requeridos Proyecto {project_id}"
            
            body = f"""Estimado Proveedor,

Le saludamos cordialmente del equipo de Revisar.ia.

Tras la revisión de su propuesta correspondiente al Proyecto {project_id}, nuestro equipo de análisis ha identificado la necesidad de realizar algunos ajustes para asegurar el cumplimiento normativo y documental requerido.

DECISIÓN DE REVISIÓN: {decision}

AJUSTES REQUERIDOS:
{adjustments_list}

DOCUMENTOS A CARGAR:
Por favor, prepare y cargue los siguientes documentos actualizados:
   • Propuesta técnica revisada con los ajustes indicados
   • Documentación soporte que evidencie el cumplimiento de cada ajuste
   • Cualquier anexo técnico o legal que respalde las modificaciones

INSTRUCCIONES DE CARGA:
Puede cargar los documentos actualizados en el siguiente enlace de pCloud:
{pcloud_upload_link}

FECHA LÍMITE:
Los documentos deberán ser entregados a más tardar el {deadline_str} (7 días hábiles).

Si tiene alguna duda sobre los ajustes solicitados, no dude en contactarnos respondiendo a este correo.

Agradecemos su pronta atención a este asunto.

Atentamente,

{self.agent_name}
Verificador de Cumplimiento Documental
Revisar.ia - Sistema de Análisis Multi-Agente
Email: {self.agent_email}

---
Este es un correo automático generado por el sistema Revisar.ia.
Proyecto ID: {project_id}
Fecha de emisión: {datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")} UTC
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background-color: #1a365d; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .adjustments {{ background-color: #f7fafc; border-left: 4px solid #3182ce; padding: 15px; margin: 20px 0; }}
        .deadline {{ background-color: #fed7d7; border-left: 4px solid #c53030; padding: 15px; margin: 20px 0; }}
        .upload-link {{ background-color: #c6f6d5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background-color: #edf2f7; padding: 15px; font-size: 12px; color: #718096; }}
        ul {{ margin: 10px 0; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Revisar.ia</h1>
        <p>Sistema de Análisis Multi-Agente</p>
    </div>
    <div class="content">
        <p>Estimado Proveedor,</p>
        <p>Le saludamos cordialmente del equipo de Revisar.ia.</p>
        <p>Tras la revisión de su propuesta correspondiente al <strong>Proyecto {project_id}</strong>, nuestro equipo de análisis ha identificado la necesidad de realizar algunos ajustes para asegurar el cumplimiento normativo y documental requerido.</p>
        
        <h2>Decisión de Revisión: <span style="color: #c53030;">{decision}</span></h2>
        
        <div class="adjustments">
            <h3>Ajustes Requeridos:</h3>
            <ol>
                {"".join(f'<li>{adj["description"]}</li>' for adj in adjustments)}
            </ol>
        </div>
        
        <h3>Documentos a Cargar:</h3>
        <ul>
            <li>Propuesta técnica revisada con los ajustes indicados</li>
            <li>Documentación soporte que evidencie el cumplimiento de cada ajuste</li>
            <li>Cualquier anexo técnico o legal que respalde las modificaciones</li>
        </ul>
        
        <div class="upload-link">
            <h3>Enlace de Carga pCloud:</h3>
            <p><a href="{pcloud_upload_link}">{pcloud_upload_link}</a></p>
        </div>
        
        <div class="deadline">
            <h3>Fecha Límite:</h3>
            <p><strong>{deadline_str}</strong> (7 días hábiles)</p>
        </div>
        
        <p>Si tiene alguna duda sobre los ajustes solicitados, no dude en contactarnos respondiendo a este correo.</p>
        <p>Agradecemos su pronta atención a este asunto.</p>
        
        <p>Atentamente,</p>
        <p><strong>{self.agent_name}</strong><br>
        Verificador de Cumplimiento Documental<br>
        Revisar.ia - Sistema de Análisis Multi-Agente<br>
        Email: {self.agent_email}</p>
    </div>
    <div class="footer">
        <p>Este es un correo automático generado por el sistema Revisar.ia.</p>
        <p>Proyecto ID: {project_id} | Fecha de emisión: {datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")} UTC</p>
    </div>
</body>
</html>
"""
            
            email_result = self.email_service.send_to_provider(
                from_agent_id="A2_PMO",
                provider_email=provider_email,
                subject=subject,
                body=body,
                project_id=project_id,
                cc_pmo=True
            )
            
            if email_result.get("success"):
                defense_file = defense_file_service.get_or_create(project_id)
                defense_file.add_provider_communication({
                    "type": "adjustment_request",
                    "agent_id": self.agent_id,
                    "decision": decision,
                    "adjustments": adjustments,
                    "provider_email": provider_email,
                    "deadline": deadline.isoformat(),
                    "email_result": email_result
                })
                defense_file.save()
            
            result = {
                "success": email_result.get("success", False),
                "project_id": project_id,
                "agent_id": agent_id,
                "decision": decision,
                "adjustment_count": len(adjustments),
                "provider_email": provider_email,
                "deadline": deadline.isoformat(),
                "deadline_display": deadline_str,
                "email_result": email_result,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
            
            self._log_audit_action("send_adjustment_email_complete", project_id, {
                "success": email_result.get("success", False),
                "adjustment_count": len(adjustments)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"[AUDIT] Error sending adjustment email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id,
                "provider_email": provider_email
            }
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent configuration information"""
        return {
            "id": self.agent_id,
            "name": self.agent_name,
            "email": self.agent_email,
            "role": "Verificador de Cumplimiento Documental"
        }
    
    def generate_completeness_checklist(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a complete checklist showing document completeness status
        for a project's Defense File.
        
        Returns a detailed checklist with:
        - All required documents by category
        - Status of each document (present/missing)
        - Overall completion percentage
        - List of missing items for provider action
        """
        self._log_audit_action("generate_checklist_start", project_id, {})
        
        try:
            defense_file = defense_file_service.get_or_create(project_id)
            defense_data = defense_file.to_dict()
            
            documents = defense_data.get("documents", [])
            pcloud_docs = defense_data.get("pcloud_documents", [])
            deliberations = defense_data.get("deliberations", [])
            
            existing_doc_types = set()
            for doc in documents:
                doc_type = doc.get("doc_type", "").lower()
                existing_doc_types.add(doc_type)
            
            for doc in pcloud_docs:
                doc_type = doc.get("doc_type", "").lower()
                existing_doc_types.add(doc_type)
            
            agent_reports = {}
            for delib in deliberations:
                agent_id = delib.get("agent_id", "")
                if "SPONSOR" in agent_id or "A1" in agent_id:
                    agent_reports["reporte_estrategia"] = True
                elif "FISCAL" in agent_id or "A3" in agent_id:
                    agent_reports["reporte_fiscal"] = True
                elif "FINANZAS" in agent_id or "A5" in agent_id:
                    agent_reports["reporte_finanzas"] = True
                elif "LEGAL" in agent_id or "A4" in agent_id:
                    agent_reports["reporte_legal"] = True
            
            checklist_result = {
                "project_id": project_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "categories": {},
                "summary": {
                    "total_required": 0,
                    "total_present": 0,
                    "total_missing": 0,
                    "completion_percentage": 0
                },
                "missing_items": [],
                "present_items": []
            }
            
            total_required = 0
            total_present = 0
            
            for category_id, category_data in DOCUMENTO_CHECKLIST.items():
                category_result = {
                    "nombre": category_data["nombre"],
                    "descripcion": category_data["descripcion"],
                    "items": [],
                    "category_complete": True
                }
                
                for doc_req in category_data["requeridos"]:
                    doc_id = doc_req["id"]
                    is_obligatorio = doc_req["obligatorio"]
                    
                    is_present = (
                        doc_id in existing_doc_types or
                        doc_id in agent_reports or
                        any(doc_id in dt.lower() for dt in existing_doc_types)
                    )
                    
                    if is_obligatorio:
                        total_required += 1
                        if is_present:
                            total_present += 1
                    
                    item_status = {
                        "id": doc_id,
                        "nombre": doc_req["nombre"],
                        "descripcion": doc_req["descripcion"],
                        "obligatorio": is_obligatorio,
                        "presente": is_present,
                        "formatos_aceptados": doc_req["formatos"],
                        "validaciones": doc_req["validaciones"]
                    }
                    
                    category_result["items"].append(item_status)
                    
                    if is_obligatorio and not is_present:
                        category_result["category_complete"] = False
                        checklist_result["missing_items"].append({
                            "categoria": category_data["nombre"],
                            "documento": doc_req["nombre"],
                            "descripcion": doc_req["descripcion"],
                            "formatos": doc_req["formatos"],
                            "validaciones": doc_req["validaciones"]
                        })
                    elif is_present:
                        checklist_result["present_items"].append({
                            "categoria": category_data["nombre"],
                            "documento": doc_req["nombre"]
                        })
                
                checklist_result["categories"][category_id] = category_result
            
            completion_pct = (total_present / total_required * 100) if total_required > 0 else 0
            checklist_result["summary"] = {
                "total_required": total_required,
                "total_present": total_present,
                "total_missing": total_required - total_present,
                "completion_percentage": round(completion_pct, 1),
                "is_complete": completion_pct >= 100,
                "approval_ready": completion_pct >= 80
            }
            
            self._log_audit_action("generate_checklist_complete", project_id, {
                "completion_percentage": completion_pct,
                "missing_count": len(checklist_result["missing_items"])
            })
            
            return {
                "success": True,
                **checklist_result
            }
            
        except Exception as e:
            logger.error(f"[AUDIT] Error generating checklist: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }
    
    def generate_provider_checklist_pdf(self, project_id: str) -> Dict[str, Any]:
        """
        Generate a PDF checklist document for the provider showing:
        - What documents are present
        - What documents are missing
        - Detailed requirements for each missing document
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch
            import io
            
            checklist = self.generate_completeness_checklist(project_id)
            if not checklist.get("success"):
                return checklist
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=20
            )
            
            story = []
            
            story.append(Paragraph("Revisar.ia - Checklist de Expediente de Defensa", title_style))
            story.append(Paragraph(f"<b>Proyecto:</b> {project_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            summary = checklist["summary"]
            summary_text = f"""
            <b>Resumen de Completitud:</b><br/>
            - Documentos Requeridos: {summary['total_required']}<br/>
            - Documentos Presentes: {summary['total_present']}<br/>
            - Documentos Faltantes: {summary['total_missing']}<br/>
            - Porcentaje de Completitud: {summary['completion_percentage']}%<br/>
            - Estado: {'LISTO PARA APROBACIÓN' if summary['approval_ready'] else 'REQUIERE DOCUMENTOS ADICIONALES'}
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 20))
            
            if checklist["missing_items"]:
                story.append(Paragraph("<b>DOCUMENTOS FALTANTES:</b>", styles['Heading2']))
                story.append(Spacer(1, 10))
                
                for i, item in enumerate(checklist["missing_items"], 1):
                    item_text = f"""
                    <b>{i}. {item['documento']}</b><br/>
                    <i>Categoría:</i> {item['categoria']}<br/>
                    <i>Descripción:</i> {item['descripcion']}<br/>
                    <i>Formatos Aceptados:</i> {', '.join(item['formatos'])}<br/>
                    <i>Validaciones:</i> {', '.join(item['validaciones'])}
                    """
                    story.append(Paragraph(item_text, styles['Normal']))
                    story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>DOCUMENTOS PRESENTES:</b>", styles['Heading2']))
            for item in checklist["present_items"]:
                story.append(Paragraph(f"✓ {item['documento']} ({item['categoria']})", styles['Normal']))
            
            doc.build(story)
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            reports_dir = Path("./reports")
            reports_dir.mkdir(exist_ok=True)
            pdf_filename = f"CHECKLIST_{project_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            pdf_path = reports_dir / pdf_filename
            
            with open(pdf_path, "wb") as f:
                f.write(pdf_content)
            
            return {
                "success": True,
                "project_id": project_id,
                "pdf_path": str(pdf_path),
                "pdf_filename": pdf_filename,
                "checklist": checklist
            }
            
        except ImportError:
            logger.warning("reportlab not available, returning JSON checklist only")
            return {
                "success": True,
                "project_id": project_id,
                "pdf_path": None,
                "checklist": self.generate_completeness_checklist(project_id)
            }
        except Exception as e:
            logger.error(f"[AUDIT] Error generating PDF checklist: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "project_id": project_id
            }


auditor_service = AuditorService()
