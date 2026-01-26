"""
GENERADOR DE PDF BASE
Funciones comunes para crear documentos PDF profesionales
"""

import os
import io
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, HRFlowable
)
from reportlab.lib import colors

try:
    import qrcode
    from PIL import Image
    HAS_QR = True
except ImportError:
    HAS_QR = False

from .styles import (
    COLORS, PAGE_CONFIG, FONTS, get_styles, 
    SEVERITY_COLORS, STATUS_COLORS, LEGAL_TEXTS
)


class PDFGenerator:
    """Generador base de documentos PDF"""
    
    def __init__(self, output_path: str, title: str = "Documento"):
        self.output_path = output_path
        self.title = title
        self.styles = get_styles()
        self.elements = []
        self.page_count = 0
        self.generation_timestamp = datetime.now()
        
    def add_header(self, canvas_obj, doc):
        """Agrega encabezado a cada página"""
        canvas_obj.saveState()
        
        canvas_obj.setStrokeColor(COLORS['primary'])
        canvas_obj.setLineWidth(2)
        canvas_obj.line(
            PAGE_CONFIG['margin_left'],
            letter[1] - 0.5 * inch,
            letter[0] - PAGE_CONFIG['margin_right'],
            letter[1] - 0.5 * inch
        )
        
        canvas_obj.setFont(*FONTS['small'])
        canvas_obj.setFillColor(COLORS['primary'])
        canvas_obj.drawString(
            PAGE_CONFIG['margin_left'],
            letter[1] - 0.4 * inch,
            self.title
        )
        
        canvas_obj.drawRightString(
            letter[0] - PAGE_CONFIG['margin_right'],
            letter[1] - 0.4 * inch,
            self.generation_timestamp.strftime("%d/%m/%Y %H:%M")
        )
        
        canvas_obj.restoreState()
    
    def add_footer(self, canvas_obj, doc):
        """Agrega pie de página a cada página"""
        canvas_obj.saveState()
        
        canvas_obj.setStrokeColor(COLORS['light_gray'])
        canvas_obj.setLineWidth(1)
        canvas_obj.line(
            PAGE_CONFIG['margin_left'],
            0.5 * inch,
            letter[0] - PAGE_CONFIG['margin_right'],
            0.5 * inch
        )
        
        canvas_obj.setFont(*FONTS['tiny'])
        canvas_obj.setFillColor(COLORS['dark_gray'])
        canvas_obj.drawCentredString(
            letter[0] / 2,
            0.35 * inch,
            f"Página {doc.page} | Expediente generado por Revisar.IA"
        )
        
        canvas_obj.setFont(*FONTS['tiny'])
        canvas_obj.drawCentredString(
            letter[0] / 2,
            0.2 * inch,
            "CONFIDENCIAL - Solo para uso del destinatario autorizado"
        )
        
        canvas_obj.restoreState()
    
    def add_title_page(
        self,
        project_name: str,
        client_name: str,
        rfc: str,
        periodo_fiscal: str,
        folio: str,
        qr_data: str = None
    ):
        """Genera página de carátula"""
        
        self.elements.append(Spacer(1, 1.5 * inch))
        
        self.elements.append(Paragraph(
            "REVISAR.IA",
            self.styles['Title']
        ))
        
        self.elements.append(Paragraph(
            "Sistema de Auditoría de Intangibles",
            self.styles['Subtitle']
        ))
        
        self.elements.append(Spacer(1, 0.5 * inch))
        self.elements.append(HRFlowable(
            width="80%",
            thickness=2,
            color=COLORS['primary'],
            spaceBefore=10,
            spaceAfter=30
        ))
        
        self.elements.append(Paragraph(
            "EXPEDIENTE DE DEFENSA FISCAL",
            self.styles['Title']
        ))
        
        self.elements.append(Spacer(1, 0.3 * inch))
        
        info_data = [
            ['PROYECTO:', project_name],
            ['CONTRIBUYENTE:', client_name],
            ['RFC:', rfc],
            ['PERÍODO FISCAL:', periodo_fiscal],
            ['FOLIO EXPEDIENTE:', folio],
            ['FECHA GENERACIÓN:', self.generation_timestamp.strftime("%d de %B de %Y")],
        ]
        
        info_table = Table(info_data, colWidths=[2.5 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (0, -1), COLORS['primary']),
            ('TEXTCOLOR', (1, 0), (1, -1), COLORS['text']),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        self.elements.append(info_table)
        
        if HAS_QR and qr_data:
            self.elements.append(Spacer(1, 0.5 * inch))
            qr_img = self._generate_qr_code(qr_data)
            if qr_img:
                self.elements.append(qr_img)
                self.elements.append(Paragraph(
                    "Escanea para verificar autenticidad",
                    self.styles['Small']
                ))
        
        self.elements.append(Spacer(1, 0.5 * inch))
        
        self.elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=COLORS['light_gray'],
            spaceBefore=20,
            spaceAfter=10
        ))
        
        self.elements.append(Paragraph(
            LEGAL_TEXTS['confidentiality'].strip(),
            self.styles['Legal']
        ))
        
        self.elements.append(PageBreak())
    
    def add_executive_summary(
        self,
        risk_score: float,
        risk_level: str,
        total_documents: int,
        validated_documents: int,
        vulnerabilities_found: int,
        key_findings: List[str],
        recommendation: str
    ):
        """Genera sección de resumen ejecutivo"""
        
        self.elements.append(Paragraph(
            "RESUMEN EJECUTIVO",
            self.styles['Heading1']
        ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        indicators = [
            ['INDICADOR', 'VALOR', 'ESTADO'],
            ['Risk Score General', f"{risk_score:.1f}/100", self._get_risk_badge(risk_level)],
            ['Documentos Totales', str(total_documents), '—'],
            ['Documentos Validados', str(validated_documents), 
             '✓' if validated_documents == total_documents else '⚠'],
            ['Tasa de Validación', f"{(validated_documents/total_documents*100):.0f}%" if total_documents > 0 else 'N/A', '—'],
            ['Vulnerabilidades Red Team', str(vulnerabilities_found),
             '✓' if vulnerabilities_found == 0 else '⚠'],
        ]
        
        indicator_table = Table(indicators, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
        indicator_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['white'], COLORS['light_gray']]),
        ]))
        
        self.elements.append(indicator_table)
        self.elements.append(Spacer(1, 0.3 * inch))
        
        if key_findings:
            self.elements.append(Paragraph(
                "Hallazgos Clave:",
                self.styles['Heading2']
            ))
            
            for finding in key_findings[:5]:
                self.elements.append(Paragraph(
                    f"• {finding}",
                    self.styles['Body']
                ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        self.elements.append(Paragraph(
            "Recomendación:",
            self.styles['Heading2']
        ))
        
        rec_color = COLORS['success'] if risk_level in ['LOW', 'MEDIUM'] else COLORS['danger']
        self.elements.append(Paragraph(
            f"<font color='{rec_color.hexval()}'><b>{recommendation}</b></font>",
            self.styles['Body']
        ))
        
        self.elements.append(PageBreak())
    
    def add_document_index(
        self,
        documents: List[Dict[str, Any]],
        title: str = "ÍNDICE DE DOCUMENTOS"
    ):
        """Genera índice de documentos con checklist"""
        
        self.elements.append(Paragraph(title, self.styles['Heading1']))
        self.elements.append(Spacer(1, 0.2 * inch))
        
        table_data = [['#', 'DOCUMENTO', 'TIPO', 'ESTADO', 'PÁGINA']]
        
        for i, doc in enumerate(documents, 1):
            status = doc.get('status', 'PENDING')
            status_symbol = '✓' if status in ['VALIDATED', 'COMPLETE'] else '✗' if status == 'MISSING' else '○'
            
            table_data.append([
                str(i),
                doc.get('nombre', 'Sin nombre')[:40],
                doc.get('tipo', 'N/A'),
                status_symbol,
                str(doc.get('pagina', '—'))
            ])
        
        doc_table = Table(
            table_data,
            colWidths=[0.5 * inch, 3 * inch, 1.5 * inch, 0.7 * inch, 0.8 * inch]
        )
        
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['light_gray']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['white'], colors.HexColor('#f7fafc')]),
        ]))
        
        self.elements.append(doc_table)
        self.elements.append(Spacer(1, 0.3 * inch))
        
        legend = """
        <b>Leyenda:</b> ✓ = Documento validado | ○ = Pendiente de validación | ✗ = Documento faltante
        """
        self.elements.append(Paragraph(legend.strip(), self.styles['Small']))
        
        self.elements.append(PageBreak())
    
    def add_validation_report(
        self,
        ocr_results: List[Dict[str, Any]],
        title: str = "REPORTE DE VALIDACIÓN OCR"
    ):
        """Genera sección de reporte de validación OCR"""
        
        self.elements.append(Paragraph(title, self.styles['Heading1']))
        self.elements.append(Spacer(1, 0.2 * inch))
        
        self.elements.append(Paragraph(
            """Los siguientes documentos fueron procesados mediante reconocimiento 
            óptico de caracteres (OCR) y validados contra los datos registrados 
            en el sistema para garantizar consistencia e integridad.""",
            self.styles['Body']
        ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        for result in ocr_results:
            doc_name = result.get('document_name', 'Documento')
            confidence = result.get('confidence', 0)
            status = result.get('status', 'PENDING')
            findings = result.get('findings', [])
            
            status_color = STATUS_COLORS.get(status, COLORS['dark_gray'])
            
            self.elements.append(Paragraph(
                f"<b>{doc_name}</b>",
                self.styles['Heading2']
            ))
            
            self.elements.append(Paragraph(
                f"Confianza: {confidence*100:.0f}% | Estado: <font color='{status_color.hexval()}'>{status}</font>",
                self.styles['Body']
            ))
            
            if findings:
                for finding in findings[:3]:
                    severity = finding.get('severity', 'INFO')
                    message = finding.get('message', '')
                    sev_color = SEVERITY_COLORS.get(severity, COLORS['dark_gray'])
                    self.elements.append(Paragraph(
                        f"  • <font color='{sev_color.hexval()}'>[{severity}]</font> {message}",
                        self.styles['Small']
                    ))
            
            self.elements.append(Spacer(1, 0.15 * inch))
        
        self.elements.append(PageBreak())
    
    def add_red_team_report(
        self,
        vulnerabilities: List[Dict[str, Any]],
        overall_score: float,
        bulletproof: bool,
        title: str = "REPORTE RED TEAM - SIMULACIÓN SAT"
    ):
        """Genera sección de reporte Red Team"""
        
        self.elements.append(Paragraph(title, self.styles['Heading1']))
        self.elements.append(Spacer(1, 0.2 * inch))
        
        self.elements.append(Paragraph(
            """Este reporte presenta los resultados de la simulación de auditoría 
            fiscal, donde el sistema actuó como auditor del SAT para identificar 
            posibles vulnerabilidades en la documentación del expediente.""",
            self.styles['Body']
        ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        cert_text = "CERTIFICADO BULLETPROOF" if bulletproof else "REQUIERE ATENCIÓN"
        cert_color = COLORS['success'] if bulletproof else COLORS['danger']
        
        self.elements.append(Paragraph(
            f"<font color='{cert_color.hexval()}' size='14'><b>{cert_text}</b></font>",
            self.styles['Body']
        ))
        
        self.elements.append(Paragraph(
            f"Score de Defensa: {overall_score:.1f}/100",
            self.styles['Body']
        ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        if vulnerabilities:
            self.elements.append(Paragraph(
                "Vulnerabilidades Identificadas:",
                self.styles['Heading2']
            ))
            
            vuln_data = [['SEVERIDAD', 'VECTOR', 'DESCRIPCIÓN', 'RECOMENDACIÓN']]
            
            for vuln in vulnerabilities[:10]:
                vuln_data.append([
                    vuln.get('severity', 'N/A'),
                    vuln.get('vector_name', 'N/A')[:20],
                    vuln.get('description', 'N/A')[:40],
                    vuln.get('recommendation', 'N/A')[:40]
                ])
            
            vuln_table = Table(vuln_data, colWidths=[1 * inch, 1.3 * inch, 2 * inch, 2 * inch])
            vuln_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, COLORS['light_gray']),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            self.elements.append(vuln_table)
        else:
            self.elements.append(Paragraph(
                "No se identificaron vulnerabilidades significativas.",
                self.styles['Body']
            ))
        
        self.elements.append(PageBreak())
    
    def add_integrity_section(
        self,
        file_hashes: Dict[str, str],
        title: str = "VERIFICACIÓN DE INTEGRIDAD"
    ):
        """Genera sección de integridad con hashes"""
        
        self.elements.append(Paragraph(title, self.styles['Heading1']))
        self.elements.append(Spacer(1, 0.2 * inch))
        
        self.elements.append(Paragraph(
            LEGAL_TEXTS['integrity'].strip(),
            self.styles['Body']
        ))
        
        self.elements.append(Spacer(1, 0.2 * inch))
        
        hash_data = [['ARCHIVO', 'HASH SHA-256']]
        for filename, hash_value in file_hashes.items():
            hash_data.append([
                filename[:30],
                hash_value[:32] + '...' if len(hash_value) > 32 else hash_value
            ])
        
        hash_table = Table(hash_data, colWidths=[2.5 * inch, 4 * inch])
        hash_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['light_gray']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        self.elements.append(hash_table)
        self.elements.append(Spacer(1, 0.3 * inch))
        
        self.elements.append(Paragraph(
            f"<b>Timestamp de Generación:</b> {self.generation_timestamp.isoformat()}",
            self.styles['Small']
        ))
    
    def _generate_qr_code(self, data: str) -> Optional[RLImage]:
        """Genera código QR como imagen para el PDF"""
        if not HAS_QR:
            return None
        
        try:
            qr = qrcode.make(data)
            buffer = io.BytesIO()
            qr.save(buffer, format='PNG')
            buffer.seek(0)
            
            return RLImage(buffer, width=1.5 * inch, height=1.5 * inch)
        except Exception:
            return None
    
    def _get_risk_badge(self, risk_level: str) -> str:
        """Retorna badge de texto para nivel de riesgo"""
        badges = {
            'LOW': '🟢 BAJO',
            'MEDIUM': '🟡 MEDIO',
            'HIGH': '🟠 ALTO',
            'CRITICAL': '🔴 CRÍTICO'
        }
        return badges.get(risk_level.upper(), risk_level)
    
    def build(self) -> str:
        """Construye el PDF final"""
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=PAGE_CONFIG['size'],
            topMargin=PAGE_CONFIG['margin_top'],
            bottomMargin=PAGE_CONFIG['margin_bottom'],
            leftMargin=PAGE_CONFIG['margin_left'],
            rightMargin=PAGE_CONFIG['margin_right']
        )
        
        doc.build(
            self.elements,
            onFirstPage=lambda c, d: (self.add_header(c, d), self.add_footer(c, d)),
            onLaterPages=lambda c, d: (self.add_header(c, d), self.add_footer(c, d))
        )
        
        return self.output_path
    
    def get_hash(self) -> str:
        """Calcula hash SHA-256 del PDF generado"""
        if os.path.exists(self.output_path):
            with open(self.output_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        return ""
