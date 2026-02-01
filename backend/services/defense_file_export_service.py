"""
Defense File PDF Export Service
Generates professional PDF documents for SAT audit defense files
"""

import os
import hashlib
import logging
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import asyncpg

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '')


async def get_db_connection():
    """Get a database connection."""
    if not DATABASE_URL:
        return None
    try:
        return await asyncpg.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


class DefenseFileExportService:
    """Service for exporting defense files as PDF documents."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        self.styles.add(ParagraphStyle(
            name='SATHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#1a365d'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#4a5568'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='LegalText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=10,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='LegalQuote',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            spaceAfter=8,
            leftIndent=20,
            rightIndent=20,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#4a5568')
        ))
        
        self.styles.add(ParagraphStyle(
            name='HashVerification',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            fontName='Courier'
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.white
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica'
        ))
    
    def _generate_defense_file_pdf_sync(
        self, 
        defense_file_data: Dict[str, Any]
    ) -> BytesIO:
        """Internal synchronous method to generate PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        story.extend(self._build_cover_page(defense_file_data))
        story.append(PageBreak())
        
        story.extend(self._build_table_of_contents())
        story.append(PageBreak())
        
        story.extend(self._build_executive_summary(defense_file_data))
        story.append(PageBreak())
        
        story.extend(self._build_legal_contractual(defense_file_data))
        story.append(PageBreak())
        
        story.extend(self._build_execution_evidence(defense_file_data))
        story.append(PageBreak())
        
        story.extend(self._build_financial_section(defense_file_data))
        story.append(PageBreak())

        story.extend(self._build_closing_section(defense_file_data))
        story.append(PageBreak())
        
        story.extend(self._build_integrity_chain(defense_file_data))
        
        doc.build(
            story, 
            onFirstPage=self._add_header_footer, 
            onLaterPages=self._add_header_footer
        )
        
        buffer.seek(0)
        return buffer

    async def generate_defense_file_pdf(
        self, 
        defense_file_data: Dict[str, Any]
    ) -> BytesIO:
        """Generate a complete defense file PDF from V2 data structure (Non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            self._generate_defense_file_pdf_sync, 
            defense_file_data
        )
    
    def _build_cover_page(self, data: Dict[str, Any]) -> List:
        """Build the cover page elements."""
        elements = []
        elements.append(Spacer(1, 1.5*inch))
        elements.append(Paragraph("EXPEDIENTE DE DEFENSA FISCAL", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("Documentación para Auditoría SAT", self.styles['LegalText']))
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(f"<b>Folio Defensa:</b> {data.get('folio_defensa', 'N/A')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Título:</b> {data.get('titulo', 'Sin nombre')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>ID Proyecto:</b> {data.get('proyecto_id', 'N/A')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Fecha de Generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", self.styles['LegalText']))
        
        elements.append(Spacer(1, 0.5*inch))
        
        indice = data.get('indice_defendibilidad', 0)
        if indice >= 80:
            risk_color = '#38a169'
            risk_label = "ALTA DEFENDIBILIDAD"
        elif indice >= 60:
            risk_color = '#dd6b20'
            risk_label = "MEDIA DEFENDIBILIDAD"
        else:
            risk_color = '#e53e3e'
            risk_label = "BAJA DEFENDIBILIDAD"
        
        elements.append(Paragraph(
            f"<b>Índice de Defendibilidad:</b> <font color='{risk_color}'>{indice}/100 ({risk_label})</font>",
            self.styles['LegalText']
        ))
        
        elements.append(Spacer(1, 1*inch))
        elements.append(Paragraph(
            "<b>CONFIDENCIAL</b>",
            ParagraphStyle(
                'Confidential',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.red,
                alignment=1
            )
        ))
        elements.append(Paragraph(
            "Este documento contiene información privilegiada para uso exclusivo en procedimientos de auditoría fiscal.",
            self.styles['LegalText']
        ))
        
        return elements
    
    def _build_table_of_contents(self) -> List:
        """Build table of contents."""
        elements = []
        elements.append(Paragraph("ÍNDICE", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.3*inch))
        
        toc_items = [
            ("1.", "Contexto Estratégico y Razón de Negocios"),
            ("2.", "Marco Contractual y Legal"),
            ("3.", "Evidencia de Ejecución (Materialidad)"),
            ("4.", "Soporte Financiero y Fiscal"),
            ("5.", "Cierre, BEE y Lecciones Aprendidas"),
            ("6.", "Cadena de Integridad"),
        ]
        
        for num, title in toc_items:
            elements.append(Paragraph(f"{num} {title}", self.styles['LegalText']))
        
        return elements
    
    def _build_executive_summary(self, data: Dict[str, Any]) -> List:
        """Build executive summary section (Section 1)."""
        elements = []
        s1 = data.get('secciones', {}).get('contexto', {})
        
        elements.append(Paragraph("1. CONTEXTO ESTRATÉGICO", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph("Razón de Negocios:", self.styles['SubsectionHeader']))
        elements.append(Paragraph(s1.get('razon_negocios_descripcion', 'No especificado'), self.styles['LegalText']))
        
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Objetivo de Negocio:", self.styles['SubsectionHeader']))
        elements.append(Paragraph(s1.get('objetivo_negocio', 'No especificado'), self.styles['LegalText']))
        
        if s1.get('pilares_estrategicos'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Pilares Estratégicos:", self.styles['SubsectionHeader']))
            for item in s1.get('pilares_estrategicos', []):
                elements.append(Paragraph(f"• {item}", self.styles['LegalText']))
        
        if s1.get('riesgos_de_no_hacer'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Riesgos de No Hacer:", self.styles['SubsectionHeader']))
            elements.append(Paragraph(s1.get('riesgos_de_no_hacer', ''), self.styles['LegalText']))

        return elements
    
    def _build_legal_contractual(self, data: Dict[str, Any]) -> List:
        """Build legal/contractual section (Section 2)."""
        elements = []
        s2 = data.get('secciones', {}).get('contractual', {})
        
        elements.append(Paragraph("2. MARCO CONTRACTUAL", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(f"<b>Contrato ID:</b> {s2.get('contrato_id', 'N/A')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>SOW ID:</b> {s2.get('sow_id', 'N/A')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Monto Total Pactado:</b> ${s2.get('monto_total', 0):,.2f}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Forma de Pago:</b> {s2.get('forma_pago', 'N/A')}", self.styles['LegalText']))
        
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Objeto del Servicio:", self.styles['SubsectionHeader']))
        elements.append(Paragraph(s2.get('objeto_servicio', 'No especificado'), self.styles['LegalText']))
        
        elements.append(Paragraph("Alcance Detallado:", self.styles['SubsectionHeader']))
        elements.append(Paragraph(s2.get('alcance_detallado', 'No especificado'), self.styles['LegalText']))
        
        if s2.get('entregables_pactados'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Entregables Pactados:", self.styles['SubsectionHeader']))
            ent_data = [['Entregable', 'Descripción']]
            for ent in s2.get('entregables_pactados', []):
                ent_data.append([ent.get('nombre', ''), ent.get('descripcion', '')])
            
            table = Table(ent_data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
            
        return elements
    
    def _build_execution_evidence(self, data: Dict[str, Any]) -> List:
        """Build execution/materiality section (Section 3)."""
        elements = []
        s3 = data.get('secciones', {}).get('ejecucion', {})
        
        elements.append(Paragraph("3. EVIDENCIA DE EJECUCIÓN (MATERIALIDAD)", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        if s3.get('acta_aceptacion_id'):
            elements.append(Paragraph(f"<b>Acta de Aceptación ID:</b> {s3.get('acta_aceptacion_id')}", self.styles['LegalText']))
            elements.append(Paragraph(f"<b>Fecha Aceptación:</b> {s3.get('fecha_aceptacion', 'N/A')}", self.styles['LegalText']))
            elements.append(Spacer(1, 0.1*inch))
        
        if s3.get('evidencia_trabajo'):
            elements.append(Paragraph("Evidencia de Trabajo Realizado:", self.styles['SubsectionHeader']))
            for item in s3.get('evidencia_trabajo', []):
                elements.append(Paragraph(f"• {item.get('nombre', '')} ({item.get('tipo', 'Doc')})", self.styles['LegalText']))

        if s3.get('minutas'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Minutas y Reuniones:", self.styles['SubsectionHeader']))
            min_data = [['Fecha', 'Asunto', 'Acuerdos']]
            for m in s3.get('minutas', []):
                min_data.append([m.get("fecha", ""), m.get("asunto", ""), str(len(m.get("acuerdos", []))) + " acuerdos"])
            
            table = Table(min_data, colWidths=[1.5*inch, 2.5*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(table)

        return elements

    def _build_financial_section(self, data: Dict[str, Any]) -> List:
        """Build financial section (Section 4)."""
        elements = []
        s4 = data.get('secciones', {}).get('financiero', {})
        
        elements.append(Paragraph("4. SOPORTE FINANCIERO Y FISCAL", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(f"<b>CFDI UUID:</b> {s4.get('cfdi_uuid', 'No registrado')}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Monto Facurado:</b> ${s4.get('cfdi_monto', 0):,.2f}", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Concepto:</b> {s4.get('cfdi_concepto', 'N/A')}", self.styles['LegalText']))
        
        # 3-Way Match Status
        status_match = s4.get('three_way_match_status', 'pendiente')
        color_match = 'green' if status_match == 'completo' else 'orange'
        elements.append(Paragraph(
            f"<b>Estatus 3-Way Match:</b> <font color='{color_match}'>{status_match.upper()}</font>", 
            self.styles['LegalText']
        ))
        
        if s4.get('pago_referencia'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Información de Pago:", self.styles['SubsectionHeader']))
            elements.append(Paragraph(f"Referencia: {s4.get('pago_referencia')}", self.styles['LegalText']))
            elements.append(Paragraph(f"Fecha Pago: {s4.get('pago_fecha')}", self.styles['LegalText']))
            elements.append(Paragraph(f"Monto Pago: ${s4.get('pago_monto', 0):,.2f}", self.styles['LegalText']))

        return elements

    def _build_closing_section(self, data: Dict[str, Any]) -> List:
        """Build closing section (Section 5)."""
        elements = []
        s5 = data.get('secciones', {}).get('cierre', {})
        
        elements.append(Paragraph("5. CIERRE Y BENEFICIO ECONÓMICO ESPERADO", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph("Beneficio Económico (BEE):", self.styles['SubsectionHeader']))
        bee_orig = s5.get('bee_original', {})
        bee_real = s5.get('bee_alcanzado', {})
        
        elements.append(Paragraph(f"<b>Original:</b> {bee_orig.get('descripcion', 'N/A')} (${bee_orig.get('valor_estimado', 0):,.2f})", self.styles['LegalText']))
        elements.append(Paragraph(f"<b>Alcanzado:</b> {bee_real.get('descripcion', 'N/A')} (${bee_real.get('valor_real', 0):,.2f})", self.styles['LegalText']))

        if s5.get('lecciones_aprendidas'):
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("Lecciones Aprendidas:", self.styles['SubsectionHeader']))
            elements.append(Paragraph(s5.get('lecciones_aprendidas', ''), self.styles['LegalText']))

        return elements
    
    def _build_integrity_chain(self, data: Dict[str, Any]) -> List:
        """Build integrity chain section."""
        elements = []
        elements.append(Paragraph("6. CADENA DE INTEGRIDAD", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph("Este expediente cuenta con verificación de integridad mediante cadena de hash.", self.styles['LegalText']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(f"Hash Contenido: {data.get('hash_contenido', 'No generado')}", self.styles['HashVerification']))
        elements.append(Paragraph(f"Timestamp Generación: {datetime.utcnow().isoformat()}Z", self.styles['HashVerification']))
        elements.append(Paragraph(f"ID Interno: {data.get('id', 'N/A')}", self.styles['HashVerification']))
        
        return elements
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.HexColor('#4a5568'))
        canvas_obj.drawString(72, 750, "EXPEDIENTE DE DEFENSA FISCAL - CONFIDENCIAL")
        canvas_obj.setStrokeColor(colors.HexColor('#e2e8f0'))
        canvas_obj.line(72, 745, 540, 745)
        
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#718096'))
        canvas_obj.drawString(72, 30, f"Generado por Revisar.IA - {datetime.now().strftime('%d/%m/%Y')}")
        canvas_obj.drawRightString(540, 30, f"Página {doc.page}")
        canvas_obj.restoreState()


defense_file_export_service = DefenseFileExportService()
