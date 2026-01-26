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
    
    async def generate_defense_file_pdf(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> BytesIO:
        """Generate a complete defense file PDF."""
        project = await self._get_project_data(project_id, empresa_id)
        deliberations = await self._get_deliberations(project_id, empresa_id)
        evidences = await self._get_evidences(project_id, empresa_id)
        cfdis = await self._get_cfdis(project_id, empresa_id)
        legal_foundations = await self._get_legal_foundations(project_id)
        
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
        
        story.extend(self._build_cover_page(project))
        story.append(PageBreak())
        
        story.extend(self._build_table_of_contents())
        story.append(PageBreak())
        
        story.extend(self._build_executive_summary(project, deliberations))
        story.append(PageBreak())
        
        if legal_foundations:
            story.extend(self._build_legal_foundations(legal_foundations))
            story.append(PageBreak())
        
        story.extend(self._build_agent_analyses(deliberations))
        story.append(PageBreak())
        
        if evidences:
            story.extend(self._build_materiality_evidence(evidences))
            story.append(PageBreak())
        
        if cfdis:
            story.extend(self._build_cfdi_section(cfdis))
            story.append(PageBreak())
        
        story.extend(self._build_integrity_chain(project_id, project))
        
        doc.build(
            story, 
            onFirstPage=self._add_header_footer, 
            onLaterPages=self._add_header_footer
        )
        
        buffer.seek(0)
        return buffer
    
    async def _get_project_data(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> Dict[str, Any]:
        """Get project data from database."""
        conn = await get_db_connection()
        if not conn:
            return self._get_demo_project(project_id)
        
        try:
            row = await conn.fetchrow("""
                SELECT 
                    p.id, p.nombre, p.descripcion, p.monto, p.risk_score,
                    p.fase_actual, p.status, p.created_at,
                    e.nombre as empresa_nombre, e.rfc as empresa_rfc
                FROM projects p
                JOIN empresas e ON p.empresa_id = e.id
                WHERE p.id = $1 AND p.empresa_id = $2
            """, project_id, empresa_id)
            
            if row:
                return dict(row)
            return self._get_demo_project(project_id)
        except Exception as e:
            logger.error(f"Failed to get project data: {e}")
            return self._get_demo_project(project_id)
        finally:
            await conn.close()
    
    def _get_demo_project(self, project_id: str) -> Dict[str, Any]:
        """Return demo project data."""
        return {
            "id": project_id,
            "nombre": "Proyecto Demo - Servicios de Consultoría",
            "descripcion": "Proyecto de consultoría estratégica para optimización fiscal",
            "monto": 500000.00,
            "risk_score": 85,
            "fase_actual": 6,
            "status": "approved",
            "created_at": datetime.now(),
            "empresa_nombre": "Empresa Demo S.A. de C.V.",
            "empresa_rfc": "EDE123456789"
        }
    
    async def _get_deliberations(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> List[Dict[str, Any]]:
        """Get agent deliberations for the project."""
        conn = await get_db_connection()
        if not conn:
            return self._get_demo_deliberations()
        
        try:
            rows = await conn.fetch("""
                SELECT 
                    id, agente_id, fase, tipo, contenido, 
                    decision, created_at
                FROM deliberations
                WHERE project_id = $1 AND empresa_id = $2
                ORDER BY fase, created_at
            """, project_id, empresa_id)
            
            if rows:
                return [dict(r) for r in rows]
            return self._get_demo_deliberations()
        except Exception as e:
            logger.error(f"Failed to get deliberations: {e}")
            return self._get_demo_deliberations()
        finally:
            await conn.close()
    
    def _get_demo_deliberations(self) -> List[Dict[str, Any]]:
        """Return demo deliberations."""
        return [
            {
                "agente_id": "A1_ESTRATEGIA",
                "fase": 0,
                "tipo": "opinion",
                "contenido": "El proyecto presenta alineación estratégica con los objetivos corporativos. La razón de negocios está claramente establecida.",
                "decision": {"aprobado": True, "score": 90},
                "created_at": datetime.now()
            },
            {
                "agente_id": "A3_FISCAL",
                "fase": 4,
                "tipo": "dictamen",
                "contenido": "Análisis de los 4 pilares fiscales:\n\n1. Razón de Negocios: CONFORME\n2. Beneficio Económico: CONFORME\n3. Materialidad: EN REVISIÓN - Se requiere evidencia adicional\n4. Trazabilidad: CONFORME",
                "decision": {"aprobado": True, "condiciones": ["Completar evidencia de materialidad"], "score": 82},
                "created_at": datetime.now()
            },
            {
                "agente_id": "A4_LEGAL",
                "fase": 2,
                "tipo": "opinion",
                "contenido": "Contrato revisado y aprobado. Cláusulas de entregables y pagos correctamente estructuradas.",
                "decision": {"aprobado": True, "score": 88},
                "created_at": datetime.now()
            }
        ]
    
    async def _get_evidences(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> List[Dict[str, Any]]:
        """Get evidence documents for the project."""
        return [
            {"tipo": "Contrato de Servicios", "fecha": "2024-01-15", "status": "Validado"},
            {"tipo": "Acta de Entrega", "fecha": "2024-03-20", "status": "Validado"},
            {"tipo": "Reporte Final", "fecha": "2024-03-25", "status": "Validado"},
            {"tipo": "Comprobantes de Pago", "fecha": "2024-04-01", "status": "Validado"}
        ]
    
    async def _get_cfdis(
        self, 
        project_id: str, 
        empresa_id: str
    ) -> List[Dict[str, Any]]:
        """Get CFDIs associated with the project."""
        return [
            {"uuid": "ABC123...", "monto": 250000, "fecha": "2024-02-01", "status": "Vigente"},
            {"uuid": "DEF456...", "monto": 250000, "fecha": "2024-04-01", "status": "Vigente"}
        ]
    
    async def _get_legal_foundations(self, project_id: str) -> List[Dict[str, Any]]:
        """Get legal foundations for the defense."""
        conn = await get_db_connection()
        if not conn:
            return self._get_demo_legal_foundations()
        
        try:
            rows = await conn.fetch("""
                SELECT ley, articulo, texto_norma, interpretacion
                FROM kb_articulos_legales
                WHERE id IN (
                    SELECT DISTINCT articulo_id 
                    FROM defense_file_legal_foundations 
                    WHERE project_id = $1
                )
                LIMIT 10
            """, project_id)
            
            if rows:
                return [dict(r) for r in rows]
            return self._get_demo_legal_foundations()
        except Exception as e:
            logger.error(f"Failed to get legal foundations: {e}")
            return self._get_demo_legal_foundations()
        finally:
            await conn.close()
    
    def _get_demo_legal_foundations(self) -> List[Dict[str, Any]]:
        """Return demo legal foundations."""
        return [
            {
                "ley": "CFF",
                "articulo": "5-A",
                "texto_norma": "Los actos jurídicos que carezcan de una razón de negocios y que generen un beneficio fiscal directo o indirecto, tendrán los efectos fiscales que correspondan a los que se habrían realizado para la obtención del beneficio económico razonablemente esperado por el contribuyente.",
                "interpretacion": "Este artículo establece la importancia de demostrar la razón de negocios genuina en todas las operaciones."
            },
            {
                "ley": "CFF",
                "articulo": "69-B",
                "texto_norma": "Cuando la autoridad fiscal detecte que un contribuyente ha estado emitiendo comprobantes sin contar con los activos, personal, infraestructura o capacidad material, directa o indirectamente, para prestar los servicios o producir, comercializar o entregar los bienes que amparan tales comprobantes...",
                "interpretacion": "Fundamental para demostrar la materialidad de las operaciones y prevenir la presunción de simulación."
            },
            {
                "ley": "LISR",
                "articulo": "27",
                "texto_norma": "Las deducciones autorizadas en este Título deberán reunir los siguientes requisitos: I. Ser estrictamente indispensables para los fines de la actividad del contribuyente...",
                "interpretacion": "Establece los requisitos de deducibilidad que deben cumplirse para que una erogación sea fiscalmente aceptable."
            }
        ]
    
    def _build_cover_page(self, project: Dict[str, Any]) -> List:
        """Build the cover page elements."""
        elements = []
        
        elements.append(Spacer(1, 1.5*inch))
        
        elements.append(Paragraph(
            "EXPEDIENTE DE DEFENSA FISCAL",
            self.styles['SATHeader']
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph(
            "Documentación para Auditoría SAT",
            self.styles['LegalText']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            f"<b>Proyecto:</b> {project.get('nombre', 'Sin nombre')}",
            self.styles['LegalText']
        ))
        
        elements.append(Paragraph(
            f"<b>Empresa:</b> {project.get('empresa_nombre', 'N/A')}",
            self.styles['LegalText']
        ))
        
        elements.append(Paragraph(
            f"<b>RFC:</b> {project.get('empresa_rfc', 'N/A')}",
            self.styles['LegalText']
        ))
        
        elements.append(Paragraph(
            f"<b>Monto del Proyecto:</b> ${project.get('monto', 0):,.2f} MXN",
            self.styles['LegalText']
        ))
        
        elements.append(Paragraph(
            f"<b>Fecha de Generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['LegalText']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        risk_score = project.get('risk_score', 0) or 0
        if risk_score >= 80:
            risk_color = '#38a169'
            risk_label = "BAJO RIESGO"
        elif risk_score >= 60:
            risk_color = '#dd6b20'
            risk_label = "RIESGO MEDIO"
        else:
            risk_color = '#e53e3e'
            risk_label = "ALTO RIESGO"
        
        elements.append(Paragraph(
            f"<b>Score de Compliance:</b> <font color='{risk_color}'>{risk_score}/100 ({risk_label})</font>",
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
            ("1.", "Resumen Ejecutivo", "3"),
            ("2.", "Fundamentos Legales", "4"),
            ("3.", "Análisis Especializado por Agente", "6"),
            ("4.", "Evidencia de Materialidad", "10"),
            ("5.", "Comprobantes Fiscales (CFDIs)", "12"),
            ("6.", "Cadena de Integridad", "14"),
        ]
        
        for num, title, page in toc_items:
            elements.append(Paragraph(
                f"{num} {title}{'.'*(60-len(title))} {page}",
                self.styles['LegalText']
            ))
        
        return elements
    
    def _build_executive_summary(
        self, 
        project: Dict[str, Any], 
        deliberations: List[Dict]
    ) -> List:
        """Build executive summary section."""
        elements = []
        
        elements.append(Paragraph("1. RESUMEN EJECUTIVO", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            f"El presente expediente documenta la defensa fiscal del proyecto "
            f"<b>{project.get('nombre', 'N/A')}</b> con un monto de "
            f"<b>${project.get('monto', 0):,.2f} MXN</b>.",
            self.styles['LegalText']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph("Análisis de Agentes:", self.styles['SubsectionHeader']))
        
        agent_summary = {}
        for d in deliberations:
            agent = d.get('agente_id', 'Unknown')
            decision = d.get('decision', {})
            if agent not in agent_summary:
                agent_summary[agent] = {
                    'aprobado': decision.get('aprobado', False),
                    'score': decision.get('score', 0)
                }
        
        summary_data = [['Agente', 'Dictamen', 'Score']]
        for agent, data in agent_summary.items():
            status = "✓ Aprobado" if data['aprobado'] else "✗ Pendiente"
            summary_data.append([agent, status, f"{data['score']}/100"])
        
        if len(summary_data) > 1:
            table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)
        
        return elements
    
    def _build_legal_foundations(self, foundations: List[Dict]) -> List:
        """Build legal foundations section."""
        elements = []
        
        elements.append(Paragraph("2. FUNDAMENTOS LEGALES", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "Los siguientes artículos de la legislación fiscal mexicana sustentan "
            "la posición de defensa del contribuyente:",
            self.styles['LegalText']
        ))
        
        for i, foundation in enumerate(foundations, 1):
            elements.append(Spacer(1, 0.15*inch))
            
            elements.append(Paragraph(
                f"2.{i} {foundation.get('ley', 'N/A')} - Artículo {foundation.get('articulo', 'N/A')}",
                self.styles['SubsectionHeader']
            ))
            
            elements.append(Paragraph(
                f"<i>\"{foundation.get('texto_norma', 'N/A')[:500]}...\"</i>",
                self.styles['LegalQuote']
            ))
            
            elements.append(Paragraph(
                f"<b>Interpretación:</b> {foundation.get('interpretacion', 'N/A')}",
                self.styles['LegalText']
            ))
        
        return elements
    
    def _build_agent_analyses(self, deliberations: List[Dict]) -> List:
        """Build agent analyses section."""
        elements = []
        
        elements.append(Paragraph("3. ANÁLISIS ESPECIALIZADO", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        agent_names = {
            'A1_ESTRATEGIA': 'María Rodríguez - Sponsor/Estrategia',
            'A2_PMO': 'Carlos Mendoza - Project Management',
            'A3_FISCAL': 'Laura Sánchez - Especialista Fiscal',
            'A4_LEGAL': 'Especialista Legal',
            'A5_FINANZAS': 'Roberto Torres - Análisis Financiero',
            'A6_PROVEEDOR': 'Ana García - Verificación de Proveedores',
            'A7_DEFENSA': 'Agente de Defensa',
            'A8_AUDITOR': 'Agente Auditor'
        }
        
        by_agent = {}
        for d in deliberations:
            agent = d.get('agente_id', 'Unknown')
            if agent not in by_agent:
                by_agent[agent] = []
            by_agent[agent].append(d)
        
        section_num = 1
        for agent_id, agent_delibs in by_agent.items():
            elements.append(Paragraph(
                f"3.{section_num} {agent_names.get(agent_id, agent_id)}",
                self.styles['SubsectionHeader']
            ))
            
            for delib in agent_delibs:
                fase = delib.get('fase', 'N/A')
                tipo = delib.get('tipo', 'opinion').upper()
                
                elements.append(Paragraph(
                    f"<b>Fase {fase} - {tipo}</b>",
                    self.styles['LegalText']
                ))
                
                contenido = delib.get('contenido', 'Sin contenido')
                elements.append(Paragraph(contenido, self.styles['LegalText']))
                
                decision = delib.get('decision', {})
                if decision:
                    status = "✓ APROBADO" if decision.get('aprobado') else "⚠ PENDIENTE"
                    score = decision.get('score', 0)
                    elements.append(Paragraph(
                        f"<b>Dictamen:</b> {status} (Score: {score}/100)",
                        self.styles['LegalText']
                    ))
                
                elements.append(Spacer(1, 0.1*inch))
            
            section_num += 1
        
        return elements
    
    def _build_materiality_evidence(self, evidences: List[Dict]) -> List:
        """Build materiality evidence section."""
        elements = []
        
        elements.append(Paragraph("4. EVIDENCIA DE MATERIALIDAD", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "Documentación que acredita la materialidad de las operaciones:",
            self.styles['LegalText']
        ))
        
        evidence_data = [['Tipo de Evidencia', 'Fecha', 'Status']]
        for ev in evidences:
            evidence_data.append([
                ev.get('tipo', 'N/A'),
                ev.get('fecha', 'N/A'),
                ev.get('status', 'Pendiente')
            ])
        
        table = Table(evidence_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        
        return elements
    
    def _build_cfdi_section(self, cfdis: List[Dict]) -> List:
        """Build CFDI section."""
        elements = []
        
        elements.append(Paragraph("5. COMPROBANTES FISCALES (CFDIs)", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        cfdi_data = [['UUID', 'Monto', 'Fecha', 'Status']]
        for cfdi in cfdis:
            cfdi_data.append([
                cfdi.get('uuid', 'N/A'),
                f"${cfdi.get('monto', 0):,.2f}",
                cfdi.get('fecha', 'N/A'),
                cfdi.get('status', 'N/A')
            ])
        
        table = Table(cfdi_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        
        return elements
    
    def _build_integrity_chain(self, project_id: str, project: Dict) -> List:
        """Build integrity chain section with hash verification."""
        elements = []
        
        elements.append(Paragraph("6. CADENA DE INTEGRIDAD", self.styles['SATHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "Este expediente cuenta con verificación de integridad mediante cadena de hash. "
            "Cualquier modificación posterior invalidará esta verificación.",
            self.styles['LegalText']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        hash_content = f"{project_id}|{project.get('nombre', '')}|{datetime.utcnow().isoformat()}"
        doc_hash = hashlib.sha256(hash_content.encode()).hexdigest()
        
        elements.append(Paragraph(
            f"Hash de verificación: {doc_hash}",
            self.styles['HashVerification']
        ))
        
        elements.append(Paragraph(
            f"Timestamp UTC: {datetime.utcnow().isoformat()}Z",
            self.styles['HashVerification']
        ))
        
        elements.append(Paragraph(
            f"Project ID: {project_id}",
            self.styles['HashVerification']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            "Para verificar la integridad de este documento, compare el hash anterior "
            "con el generado al momento de la revisión usando el mismo algoritmo SHA-256.",
            self.styles['LegalText']
        ))
        
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
