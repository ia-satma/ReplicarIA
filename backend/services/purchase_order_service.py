import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class PurchaseOrderService:
    """Servicio para generar Órdenes de Compra con numeración consecutiva"""
    
    def __init__(self, db):
        self.db = db
        ROOT_DIR = Path(__file__).parent.parent
        self.po_dir = ROOT_DIR / "purchase_orders"
        self.po_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
    
    async def get_next_po_number(self) -> str:
        """Genera el siguiente número de PO consecutivo"""
        
        # Obtener el último PO number
        last_po = await self.db.purchase_orders.find_one(
            {},
            sort=[("po_number_int", -1)]
        )
        
        if last_po:
            next_number = last_po.get('po_number_int', 0) + 1
        else:
            next_number = 1
        
        # Formato: PO-2025-0001
        year = datetime.now(timezone.utc).year
        po_number = f"PO-{year}-{next_number:04d}"
        
        return po_number, next_number
    
    async def generate_purchase_order(
        self,
        project_id: str,
        project_data: Dict,
        consolidated_analysis: str,
        approved_by_agents: list
    ) -> Dict:
        """
        Genera Orden de Compra formal con número consecutivo.
        Guarda PDF en Drive de PMO.
        """
        
        try:
            # Generar número de PO
            po_number, po_number_int = await self.get_next_po_number()
            
            logger.info(f"📄 Generando Orden de Compra: {po_number}")
            
            # Crear PDF de PO
            pdf_filename = f"{po_number}.pdf"
            pdf_path = self.po_dir / pdf_filename
            
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            story = []
            
            # Título
            title_style = ParagraphStyle(
                'POTitle',
                parent=self.styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1e40af'),
                alignment=1,  # Center
                spaceAfter=20
            )
            
            story.append(Paragraph(f"ORDEN DE COMPRA", title_style))
            story.append(Paragraph(f"<b>{po_number}</b>", title_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Información de la empresa
            company_info = f"""
            <b>GRUPO revisar S.A. DE C.V.</b><br/>
            Dirección: [Dirección de Revisar.ia]<br/>
            RFC: [RFC de Revisar.ia]<br/>
            Fecha de Emisión: {datetime.now(timezone.utc).strftime('%d/%m/%Y')}<br/>
            """
            story.append(Paragraph(company_info, self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Información del proyecto
            story.append(Paragraph("<b>INFORMACIÓN DEL SERVICIO:</b>", self.styles['Heading2']))
            
            project_info_data = [
                ['Proyecto:', project_data.get('project_name', 'N/A')],
                ['ID Proyecto:', project_id],
                ['Solicitante:', project_data.get('sponsor_name', 'N/A')],
                ['Departamento:', project_data.get('department', 'N/A')],
                ['Presupuesto Aprobado:', f"${project_data.get('budget_estimate', 0):,.2f} MXN"],
                ['Duración:', f"{project_data.get('duration_months', 12)} meses"]
            ]
            
            table = Table(project_info_data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
            
            # Alcance del servicio
            story.append(Paragraph("<b>ALCANCE DEL SERVICIO:</b>", self.styles['Heading2']))
            story.append(Paragraph(project_data.get('description', 'N/A'), self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Análisis consolidado
            story.append(Paragraph("<b>ANÁLISIS Y ACUERDOS DEL EQUIPO:</b>", self.styles['Heading2']))
            story.append(Paragraph(consolidated_analysis[:1000] + "...", self.styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Aprobaciones
            story.append(Paragraph("<b>APROBADO POR:</b>", self.styles['Heading2']))
            for agent in approved_by_agents:
                story.append(Paragraph(f"✓ {agent}", self.styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Firmas
            story.append(Paragraph("<b>AUTORIZACIONES:</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.5*inch))
            
            signatures = [
                ['_____________________', '_____________________'],
                ['Carlos Mendoza', 'Roberto Torres'],
                ['PMO', 'Director Financiero']
            ]
            
            sig_table = Table(signatures, colWidths=[3*inch, 3*inch])
            sig_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 10)
            ]))
            
            story.append(sig_table)
            
            # Construir PDF
            doc.build(story)
            
            # Guardar en base de datos
            po_record = {
                "po_id": str(project_id),
                "po_number": po_number,
                "po_number_int": po_number_int,
                "project_id": project_id,
                "project_name": project_data.get('project_name'),
                "amount": project_data.get('budget_estimate', 0),
                "status": "issued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "A2_PMO",
                "approved_by": approved_by_agents,
                "pdf_path": str(pdf_path)
            }
            
            await self.db.purchase_orders.insert_one(po_record)
            
            logger.info(f"✅ Orden de Compra generada: {po_number}")
            
            return {
                "po_number": po_number,
                "pdf_path": str(pdf_path),
                "amount": project_data.get('budget_estimate', 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating PO: {str(e)}")
            return None
