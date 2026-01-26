import os
import logging
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)

class ReportGeneratorService:
    """Servicio para generar reportes formales en PDF para los agentes"""
    
    def __init__(self):
        # Usar path relativo
        ROOT_DIR = Path(__file__).parent.parent
        self.reports_dir = ROOT_DIR / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Estilos personalizados
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12
        )
    
    def generate_agent_report(
        self,
        project_id: str,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        report_type: str,
        version: int,
        project_data: Dict,
        analysis: str,
        decision: str,
        findings: List[str],
        recommendations: List[str]
    ) -> str:
        """
        Genera un reporte formal en PDF para un agente.
        
        Returns:
            Path del archivo PDF generado
        """
        try:
            # Validar project_id
            if not project_id:
                project_id = f"PROJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Nombre de archivo según protocolo (usar primeros 8 caracteres del ID)
            safe_id = str(project_id)[:8] if project_id else "UNKNOWN"
            filename = f"ID{safe_id}_{agent_id}_Reporte_{report_type}_V{version}.pdf"
            filepath = self.reports_dir / filename
            
            # Crear documento PDF
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            
            # Título
            title_text = f"Reporte de {report_type.replace('_', ' ').title()}"
            story.append(Paragraph(title_text, self.title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Información del agente
            agent_info = f"""
            <b>Agente:</b> {agent_name} ({agent_role.upper()})<br/>
            <b>ID Agente:</b> {agent_id}<br/>
            <b>Modelo LLM:</b> Claude 3.7 Sonnet<br/>
            <b>Fecha:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}<br/>
            <b>Versión:</b> V{version}
            """
            story.append(Paragraph(agent_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Información del proyecto
            story.append(Paragraph("INFORMACIÓN DEL PROYECTO", self.heading_style))
            # Soportar ambos formatos de datos (API y formulario)
            project_name = project_data.get('name') or project_data.get('project_name', 'N/A')
            client_name = project_data.get('client_name') or project_data.get('sponsor_name', 'N/A')
            amount = project_data.get('amount') or project_data.get('budget_estimate', 0)
            service_type = project_data.get('service_type') or project_data.get('strategic_alignment', 'Consultoría')
            project_info = f"""
            <b>ID Proyecto:</b> {project_id}<br/>
            <b>Nombre:</b> {project_name}<br/>
            <b>Cliente/Sponsor:</b> {client_name}<br/>
            <b>Monto:</b> ${amount:,.2f} MXN<br/>
            <b>Tipo de Servicio:</b> {service_type}<br/>
            <b>Descripción:</b> {project_data.get('description', 'N/A')[:200]}
            """
            story.append(Paragraph(project_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Decisión
            story.append(Paragraph("DECISIÓN", self.heading_style))
            decision_color = 'green' if decision == 'APROBADO' else 'red' if decision == 'RECHAZADO' else 'orange'
            decision_text = f"<b><font color='{decision_color}'>{decision}</font></b>"
            story.append(Paragraph(decision_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Análisis
            story.append(Paragraph("ANÁLISIS DETALLADO", self.heading_style))
            # Dividir el análisis en párrafos
            for para in analysis.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.2*inch))
            
            # Hallazgos
            if findings:
                story.append(Paragraph("HALLAZGOS PRINCIPALES", self.heading_style))
                for finding in findings:
                    story.append(Paragraph(f"• {finding}", self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Recomendaciones
            if recommendations:
                story.append(Paragraph("RECOMENDACIONES", self.heading_style))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer = f"""
            <i>Este reporte fue generado automáticamente por el Agent Network System.<br/>
            Agente: {agent_name} - {agent_role.upper()}<br/>
            Revisar.ia - Trazabilidad de Servicios Intangibles</i>
            """
            story.append(Paragraph(footer, self.styles['Normal']))
            
            # Construir PDF
            doc.build(story)
            
            logger.info(f"✅ Reporte PDF generado: {filename}")
            return f"/reports/{filename}"
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return None
    
    def generate_consolidated_report(
        self,
        project_id: str,
        cycle: int,
        project_data: Dict,
        agent_decisions: Dict[str, Dict],
        conflicts: List[str],
        pmo_analysis: str
    ) -> str:
        """
        Genera reporte consolidado de A2-PMO para revisión iterativa.
        
        Returns:
            Path del archivo PDF generado
        """
        try:
            filename = f"ID{project_id[:8]}_A2_Reporte_Consolidado_C{cycle}.pdf"
            filepath = self.reports_dir / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            
            # Título
            story.append(Paragraph(f"Reporte Consolidado - Ciclo {cycle}", self.title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Info del proyecto
            story.append(Paragraph("INFORMACIÓN DEL PROYECTO", self.heading_style))
            project_info = f"""
            <b>Proyecto:</b> {project_data.get('project_name', 'N/A')}<br/>
            <b>ID:</b> {project_id}<br/>
            <b>Ciclo de Revisión:</b> {cycle}<br/>
            <b>Generado por:</b> A2-PMO (Carlos Mendoza)
            """
            story.append(Paragraph(project_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Resumen de decisiones
            story.append(Paragraph("RESUMEN DE VALIDACIONES", self.heading_style))
            
            for agent_id, decision_data in agent_decisions.items():
                agent_name = decision_data.get('agent_name', agent_id)
                decision = decision_data.get('decision', 'PENDIENTE')
                
                decision_color = 'green' if decision == 'APROBADO' else 'red' if decision == 'RECHAZADO' else 'orange'
                agent_text = f"<b>{agent_name}:</b> <font color='{decision_color}'>{decision}</font>"
                story.append(Paragraph(agent_text, self.styles['Normal']))
                
                # Resumen breve
                if decision_data.get('summary'):
                    story.append(Paragraph(f"  {decision_data['summary'][:200]}...", self.styles['Normal']))
                
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Conflictos detectados
            if conflicts:
                story.append(Paragraph("⚠️ CONFLICTOS DETECTADOS", self.heading_style))
                for conflict in conflicts:
                    story.append(Paragraph(f"• {conflict}", self.styles['Normal']))
                story.append(Spacer(1, 0.3*inch))
            
            # Análisis consolidado de PMO
            story.append(Paragraph("ANÁLISIS CONSOLIDADO (A2-PMO)", self.heading_style))
            for para in pmo_analysis.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Instrucciones para próximo ciclo
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("INSTRUCCIONES PARA REVISIÓN CRUZADA", self.heading_style))
            instructions_text = f"Los agentes deben revisar este reporte consolidado que incluye las opiniones de todos. Favor de emitir un nuevo dictamen (V{cycle + 1}) considerando los argumentos de otros agentes. Pueden mantener su postura o modificarla basándose en nueva información."
            story.append(Paragraph(instructions_text, self.styles['Normal']))
            
            # Build
            doc.build(story)
            
            logger.info(f"✅ Reporte consolidado generado: {filename}")
            return f"/reports/{filename}"
            
        except Exception as e:
            logger.error(f"Error generating consolidated report: {str(e)}")
            return None
    
    def generate_bitacora_pdf(
        self,
        project_id: str,
        communications: List[Dict],
        project_data: Dict = None
    ) -> Optional[str]:
        """
        Genera un PDF formal de la bitácora de comunicaciones del proyecto.
        
        Args:
            project_id: ID del proyecto
            communications: Lista de entradas de comunicación
            project_data: Datos del proyecto (opcional)
        
        Returns:
            Path del archivo PDF generado o None si hay error
        """
        try:
            safe_id = str(project_id)[:8] if project_id else "UNKNOWN"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ID{safe_id}_BITACORA_{timestamp}.pdf"
            filepath = self.reports_dir / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []
            
            story.append(Paragraph("BITÁCORA DE COMUNICACIONES", self.title_style))
            story.append(Paragraph("Registro de Evidencias para Auditoría SAT", self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            story.append(Paragraph("INFORMACIÓN DEL PROYECTO", self.heading_style))
            
            if project_data:
                project_name = project_data.get('name') or project_data.get('project_name', 'N/A')
                client_name = project_data.get('client_name') or project_data.get('sponsor_name', 'N/A')
                amount = project_data.get('amount') or project_data.get('budget_estimate', 0)
                project_info = f"""
                <b>ID Proyecto:</b> {project_id}<br/>
                <b>Nombre:</b> {project_name}<br/>
                <b>Cliente/Sponsor:</b> {client_name}<br/>
                <b>Monto:</b> ${amount:,.2f} MXN<br/>
                <b>Fecha de Generación:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                """
            else:
                project_info = f"""
                <b>ID Proyecto:</b> {project_id}<br/>
                <b>Fecha de Generación:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
                """
            story.append(Paragraph(project_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            story.append(Paragraph("RESUMEN DE COMUNICACIONES", self.heading_style))
            
            emails_count = len([c for c in communications if c.get("action") == "email_sent"])
            docs_count = len([c for c in communications if c.get("action") == "document_uploaded"])
            
            agents = set()
            for comm in communications:
                if comm.get("from_agent"):
                    agents.add(comm["from_agent"])
                if comm.get("to_agent"):
                    agents.add(comm["to_agent"])
            
            summary_info = f"""
            <b>Total de Registros:</b> {len(communications)}<br/>
            <b>Emails Enviados:</b> {emails_count}<br/>
            <b>Documentos Subidos:</b> {docs_count}<br/>
            <b>Agentes Participantes:</b> {', '.join(agents) if agents else 'N/A'}
            """
            story.append(Paragraph(summary_info, self.styles['Normal']))
            story.append(Spacer(1, 0.4*inch))
            
            story.append(Paragraph("REGISTRO DETALLADO DE COMUNICACIONES", self.heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            for i, comm in enumerate(communications, 1):
                seq = comm.get("sequence_number", i)
                timestamp_str = comm.get("timestamp") or comm.get("recorded_at", "N/A")
                action = comm.get("action", "comunicación")
                from_agent = comm.get("from_agent", "N/A")
                to_agent = comm.get("to_agent", "N/A")
                subject = comm.get("email_subject", "")
                attachment = comm.get("attachment_name", "")
                pcloud_link = comm.get("pcloud_link", "")
                
                action_color = '#1e40af' if action == "email_sent" else '#059669' if action == "document_uploaded" else '#6b7280'
                
                entry_header = f"""
                <b><font color='{action_color}'>#{seq} - {action.upper().replace('_', ' ')}</font></b><br/>
                <b>Fecha/Hora:</b> {timestamp_str}<br/>
                <b>De:</b> {from_agent} → <b>Para:</b> {to_agent}
                """
                story.append(Paragraph(entry_header, self.styles['Normal']))
                
                if subject:
                    story.append(Paragraph(f"<b>Asunto:</b> {subject}", self.styles['Normal']))
                
                if attachment:
                    story.append(Paragraph(f"<b>Documento:</b> {attachment}", self.styles['Normal']))
                
                if pcloud_link:
                    story.append(Paragraph(f"<b>Enlace pCloud:</b> <font color='blue'>{pcloud_link[:60]}...</font>", self.styles['Normal']))
                
                story.append(Spacer(1, 0.15*inch))
                
                separator_style = ParagraphStyle(
                    'Separator',
                    parent=self.styles['Normal'],
                    textColor=colors.HexColor('#e5e7eb'),
                    fontSize=8
                )
                story.append(Paragraph("─" * 80, separator_style))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(PageBreak())
            
            story.append(Paragraph("DECLARACIÓN DE CUMPLIMIENTO", self.heading_style))
            compliance_text = """
            Esta bitácora constituye evidencia documental de las comunicaciones realizadas 
            durante el proceso de deliberación del proyecto, conforme a los siguientes 
            lineamientos de cumplimiento SAT:
            
            <b>• Artículo 5-A CFF:</b> Razón de Negocios - Documentación del propósito empresarial
            <b>• Artículo 27 LISR:</b> Beneficio Económico - Registro de análisis de viabilidad
            <b>• Artículo 69-B CFF:</b> Materialidad - Evidencia de servicios efectivamente prestados
            <b>• NOM-151:</b> Trazabilidad - Trail completo de deliberaciones y comunicaciones
            
            Los documentos referenciados en esta bitácora se encuentran almacenados en pCloud 
            y constituyen parte integral del expediente de defensa del proyecto.
            """
            story.append(Paragraph(compliance_text, self.styles['Normal']))
            story.append(Spacer(1, 0.5*inch))
            
            footer = f"""
            <i>Bitácora generada automáticamente por Revisar.IA<br/>
            Revisar.ia - Trazabilidad de Servicios Intangibles<br/>
            Fecha de generación: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
            """
            story.append(Paragraph(footer, self.styles['Normal']))
            
            doc.build(story)
            
            logger.info(f"✅ Bitácora PDF generada: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating bitácora PDF: {str(e)}")
            return None