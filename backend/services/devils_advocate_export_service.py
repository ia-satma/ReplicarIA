"""
Devils Advocate PDF Export Service
Generates professional PDF reports for the Devil's Advocate module
Sends automatic email notifications with the report attached
"""

import os
import base64
import logging
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)

# Email configuration
ADMIN_EMAIL = os.environ.get('DEVILS_ADVOCATE_ADMIN_EMAIL', 'santiago@satma.mx')

# Severity colors
SEVERITY_COLORS = {
    'critico': colors.HexColor('#e53e3e'),      # Red
    'importante': colors.HexColor('#dd6b20'),    # Orange
    'informativo': colors.HexColor('#3182ce'),   # Blue
}

# Block colors
BLOCK_COLORS = {
    'B1_hechos_objeto': colors.HexColor('#6366f1'),      # Indigo
    'B2_materialidad': colors.HexColor('#ef4444'),        # Red
    'B3_razon_negocios': colors.HexColor('#22c55e'),     # Green
    'B4_proveedor_efos': colors.HexColor('#f59e0b'),     # Amber
    'B5_formal_fiscal': colors.HexColor('#3b82f6'),      # Blue
    'B6_riesgo_residual': colors.HexColor('#8b5cf6'),    # Purple
}

# Semaforo colors
SEMAFORO_COLORS = {
    'verde': colors.HexColor('#38a169'),
    'amarillo': colors.HexColor('#d69e2e'),
    'rojo': colors.HexColor('#e53e3e'),
}

BLOCK_NAMES = {
    'B1_hechos_objeto': 'Hechos y Objeto del Servicio',
    'B2_materialidad': 'Materialidad / CFF 69-B',
    'B3_razon_negocios': 'Razon de Negocios / CFF 5-A',
    'B4_proveedor_efos': 'Proveedor y EFOS',
    'B5_formal_fiscal': 'Requisitos Fiscales Formales',
    'B6_riesgo_residual': 'Riesgo Residual y Lecciones',
}

BLOCK_WEIGHTS = {
    'B1_hechos_objeto': 0.15,
    'B2_materialidad': 0.25,
    'B3_razon_negocios': 0.20,
    'B4_proveedor_efos': 0.20,
    'B5_formal_fiscal': 0.15,
    'B6_riesgo_residual': 0.05,
}


def get_logo_path() -> Optional[str]:
    """Find the logo file path"""
    logo_paths = [
        Path(__file__).parent.parent / "static" / "logo-revisar-white.png",
        Path(__file__).parent.parent / "static" / "logo-revisar.png",
    ]
    for path in logo_paths:
        if path.exists():
            return str(path)
    return None


class DevilsAdvocateExportService:
    """Service for exporting Devil's Advocate reports as PDF documents."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Main title
        self.styles.add(ParagraphStyle(
            name='DATitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            textColor=colors.HexColor('#1a202c'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))

        # Section headers
        self.styles.add(ParagraphStyle(
            name='BlockHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#2d3748'),
            fontName='Helvetica-Bold'
        ))

        # Question style
        self.styles.add(ParagraphStyle(
            name='Question',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=4,
            spaceBefore=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a202c')
        ))

        # Question description
        self.styles.add(ParagraphStyle(
            name='QuestionDesc',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            spaceAfter=4,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#718096')
        ))

        # Answer style
        self.styles.add(ParagraphStyle(
            name='Answer',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
            leftIndent=15,
            fontName='Helvetica',
            textColor=colors.HexColor('#2d3748')
        ))

        # No answer style
        self.styles.add(ParagraphStyle(
            name='NoAnswer',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
            leftIndent=15,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#a0aec0')
        ))

        # Severity badge styles
        for severity, color in SEVERITY_COLORS.items():
            self.styles.add(ParagraphStyle(
                name=f'Severity_{severity}',
                parent=self.styles['Normal'],
                fontSize=8,
                fontName='Helvetica-Bold',
                textColor=color
            ))

        # Summary box styles
        self.styles.add(ParagraphStyle(
            name='SummaryLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#4a5568')
        ))

        self.styles.add(ParagraphStyle(
            name='SummaryValue',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a202c')
        ))

        # Footer/header
        self.styles.add(ParagraphStyle(
            name='HeaderFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=colors.HexColor('#718096')
        ))

        # Alert box
        self.styles.add(ParagraphStyle(
            name='AlertText',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=colors.white
        ))

        # Recommendation
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=15,
            spaceAfter=10,
            fontName='Helvetica',
            textColor=colors.HexColor('#2d3748'),
            alignment=TA_JUSTIFY
        ))

    def _generate_pdf_sync(self, data: Dict[str, Any]) -> BytesIO:
        """Internal synchronous method to generate PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=60,
            bottomMargin=50
        )

        story = []

        # Cover page
        story.extend(self._build_cover_page(data))
        story.append(PageBreak())

        # Executive summary
        story.extend(self._build_executive_summary(data))
        story.append(PageBreak())

        # Questions by block
        story.extend(self._build_questions_section(data))

        # Conclusions and recommendations
        story.append(PageBreak())
        story.extend(self._build_conclusions(data))

        doc.build(
            story,
            onFirstPage=self._add_header_footer,
            onLaterPages=self._add_header_footer
        )

        buffer.seek(0)
        return buffer

    async def generate_pdf(self, data: Dict[str, Any]) -> BytesIO:
        """Generate a Devil's Advocate report PDF (Non-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._generate_pdf_sync,
            data
        )

    def _build_cover_page(self, data: Dict[str, Any]) -> List:
        """Build the cover page elements."""
        elements = []

        # Logo placeholder
        elements.append(Spacer(1, 0.5 * inch))

        # Title
        elements.append(Paragraph(
            "REPORTE ABOGADO DEL DIABLO",
            self.styles['DATitle']
        ))
        elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph(
            "Diagnostico de Control Interno y Aprendizaje Organizacional",
            ParagraphStyle(
                'Subtitle',
                parent=self.styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#718096')
            )
        ))

        elements.append(Spacer(1, 0.5 * inch))

        # Project info box
        proyecto_info = data.get('proyecto', {})
        info_data = [
            ['Proyecto ID:', proyecto_info.get('id', 'N/A')],
            ['Empresa:', proyecto_info.get('empresa', 'N/A')],
            ['RFC:', proyecto_info.get('rfc', 'N/A')],
            ['Tipo Servicio:', proyecto_info.get('tipo_servicio', 'N/A')],
            ['Industria:', proyecto_info.get('industria', 'N/A')],
            ['Monto:', f"${proyecto_info.get('monto', 0):,.2f} MXN"],
            ['Fecha Evaluacion:', datetime.now().strftime('%d/%m/%Y %H:%M')],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1a202c')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(info_table)

        elements.append(Spacer(1, 0.5 * inch))

        # Semaforo result
        evaluacion = data.get('evaluacion', {})
        semaforo = evaluacion.get('semaforo', 'amarillo')
        score_total = evaluacion.get('score_total', 0)
        semaforo_color = SEMAFORO_COLORS.get(semaforo, colors.grey)

        # Score display
        score_data = [
            [Paragraph(f"<font size='32'><b>{score_total:.0f}</b></font>", self.styles['SummaryValue']),
             Paragraph(f"<font color='{semaforo_color.hexval()}'><b>SEMAFORO {semaforo.upper()}</b></font>",
                       self.styles['SummaryValue'])],
            ['PUNTOS DE 100', 'RESULTADO'],
        ]

        score_table = Table(score_data, colWidths=[3 * inch, 3 * inch])
        score_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, 1), 9),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#718096')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(score_table)

        elements.append(Spacer(1, 0.3 * inch))

        # Banderas rojas alert
        banderas_rojas = evaluacion.get('total_banderas_rojas', 0)
        if banderas_rojas > 0:
            alert_data = [[
                Paragraph(
                    f"ATENCION: {banderas_rojas} BANDERA(S) ROJA(S) DETECTADA(S)",
                    self.styles['AlertText']
                )
            ]]
            alert_table = Table(alert_data, colWidths=[5.5 * inch])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e53e3e')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 20),
                ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(alert_table)

        elements.append(Spacer(1, 1 * inch))

        # Confidential notice
        elements.append(Paragraph(
            "<b>DOCUMENTO CONFIDENCIAL - USO INTERNO</b>",
            ParagraphStyle(
                'Confidential',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#e53e3e'),
                alignment=TA_CENTER
            )
        ))
        elements.append(Paragraph(
            "Este reporte contiene informacion privilegiada para control interno.",
            ParagraphStyle(
                'ConfidentialSub',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#718096'),
                alignment=TA_CENTER
            )
        ))

        return elements

    def _build_executive_summary(self, data: Dict[str, Any]) -> List:
        """Build executive summary section."""
        elements = []
        evaluacion = data.get('evaluacion', {})

        elements.append(Paragraph("RESUMEN EJECUTIVO", self.styles['BlockHeader']))
        elements.append(Spacer(1, 0.2 * inch))

        # Scores by block
        elements.append(Paragraph("Scores por Bloque:", self.styles['SummaryLabel']))
        elements.append(Spacer(1, 0.1 * inch))

        score_por_bloque = evaluacion.get('score_por_bloque', {})

        block_data = [['Bloque', 'Peso', 'Score', 'Estado']]
        for bloque_id, nombre in BLOCK_NAMES.items():
            score = score_por_bloque.get(bloque_id, 0)
            peso = BLOCK_WEIGHTS.get(bloque_id, 0) * 100

            if score >= 80:
                estado = 'BIEN'
                estado_color = '#38a169'
            elif score >= 50:
                estado = 'REVISAR'
                estado_color = '#d69e2e'
            else:
                estado = 'CRITICO'
                estado_color = '#e53e3e'

            block_data.append([
                nombre,
                f"{peso:.0f}%",
                f"{score:.0f}",
                Paragraph(f"<font color='{estado_color}'><b>{estado}</b></font>", self.styles['Normal'])
            ])

        block_table = Table(block_data, colWidths=[2.8 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch])
        block_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        elements.append(block_table)

        elements.append(Spacer(1, 0.3 * inch))

        # Statistics
        stats_data = [
            ['Preguntas Respondidas', f"{evaluacion.get('preguntas_respondidas', 0)} de {evaluacion.get('preguntas_totales', 25)}"],
            ['Completitud', f"{evaluacion.get('completitud', 0):.1f}%"],
            ['Banderas Rojas', str(evaluacion.get('total_banderas_rojas', 0))],
            ['Alertas', str(evaluacion.get('total_alertas', 0))],
        ]

        stats_table = Table(stats_data, colWidths=[3 * inch, 3 * inch])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(stats_table)

        elements.append(Spacer(1, 0.3 * inch))

        # Recommendation
        recomendacion = evaluacion.get('recomendacion', '')
        if recomendacion:
            elements.append(Paragraph("Recomendacion:", self.styles['SummaryLabel']))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(recomendacion, self.styles['Recommendation']))

        # List of red flags if any
        banderas_rojas = evaluacion.get('banderas_rojas', [])
        if banderas_rojas:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Banderas Rojas Detectadas:", self.styles['SummaryLabel']))
            for br in banderas_rojas:
                pregunta_id = br.get('pregunta_id', '')
                pregunta_text = br.get('pregunta', pregunta_id)
                elements.append(Paragraph(
                    f"<font color='#e53e3e'>X</font> {pregunta_text}",
                    self.styles['Answer']
                ))

        return elements

    def _build_questions_section(self, data: Dict[str, Any]) -> List:
        """Build the questions and answers section organized by block."""
        elements = []
        preguntas_respuestas = data.get('preguntas_respuestas', {})

        elements.append(Paragraph("DETALLE DE PREGUNTAS Y RESPUESTAS", self.styles['DATitle']))
        elements.append(Spacer(1, 0.3 * inch))

        # Organize by block
        for bloque_id, bloque_nombre in BLOCK_NAMES.items():
            preguntas_bloque = preguntas_respuestas.get(bloque_id, [])
            if not preguntas_bloque:
                continue

            block_color = BLOCK_COLORS.get(bloque_id, colors.grey)

            # Block header
            block_header_data = [[
                Paragraph(f"<font color='white'><b>{bloque_nombre.upper()}</b></font>", self.styles['Normal'])
            ]]
            block_header_table = Table(block_header_data, colWidths=[6 * inch])
            block_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), block_color),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ]))
            elements.append(block_header_table)
            elements.append(Spacer(1, 0.1 * inch))

            # Questions in this block
            for pregunta in preguntas_bloque:
                pregunta_id = pregunta.get('id', '')
                numero = pregunta.get('numero', 0)
                texto_pregunta = pregunta.get('pregunta', '')
                descripcion = pregunta.get('descripcion', '')
                severidad = pregunta.get('severidad', 'informativo')
                respuesta = pregunta.get('respuesta', '')
                bandera_roja = pregunta.get('bandera_roja', False)

                severity_color = SEVERITY_COLORS.get(severidad, colors.grey)

                # Question with severity badge
                severity_text = f"[{severidad.upper()}]"
                question_content = KeepTogether([
                    Paragraph(
                        f"<font color='{severity_color.hexval()}'><b>{severity_text}</b></font> "
                        f"<b>P{numero}.</b> {texto_pregunta}",
                        self.styles['Question']
                    ),
                    Paragraph(descripcion, self.styles['QuestionDesc']) if descripcion else Spacer(1, 0),
                ])
                elements.append(question_content)

                # Answer
                if respuesta and respuesta.strip():
                    answer_prefix = ""
                    if bandera_roja:
                        answer_prefix = "<font color='#e53e3e'>[BANDERA ROJA]</font> "
                    elements.append(Paragraph(f"{answer_prefix}{respuesta}", self.styles['Answer']))
                else:
                    elements.append(Paragraph("Sin respuesta proporcionada", self.styles['NoAnswer']))

                elements.append(Spacer(1, 0.1 * inch))

            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _build_conclusions(self, data: Dict[str, Any]) -> List:
        """Build conclusions and next steps section."""
        elements = []
        evaluacion = data.get('evaluacion', {})

        elements.append(Paragraph("CONCLUSIONES Y SIGUIENTES PASOS", self.styles['DATitle']))
        elements.append(Spacer(1, 0.3 * inch))

        # Overall assessment
        semaforo = evaluacion.get('semaforo', 'amarillo')
        score_total = evaluacion.get('score_total', 0)

        if semaforo == 'verde':
            conclusion = "El proyecto ha pasado satisfactoriamente la revision del Abogado del Diablo. El expediente cuenta con evidencia suficiente y documentacion adecuada para soportar la operacion ante una eventual auditoria del SAT."
        elif semaforo == 'amarillo':
            conclusion = "El proyecto presenta areas de oportunidad que deben ser atendidas. Se recomienda reforzar la documentacion en los bloques con menor puntaje antes de cerrar definitivamente el expediente."
        else:
            conclusion = "El proyecto presenta debilidades significativas que requieren atencion inmediata. NO se recomienda aprobar el expediente hasta resolver las banderas rojas identificadas."

        elements.append(Paragraph("Evaluacion General:", self.styles['BlockHeader']))
        elements.append(Paragraph(conclusion, self.styles['Recommendation']))

        # Pending items
        requieren_revision = evaluacion.get('requieren_revision', [])
        if requieren_revision:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Preguntas que Requieren Revision Adicional:", self.styles['BlockHeader']))
            for pregunta_id in requieren_revision:
                elements.append(Paragraph(f"* {pregunta_id}", self.styles['Answer']))

        # Alerts
        alertas = evaluacion.get('alertas', [])
        if alertas:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Alertas Generadas:", self.styles['BlockHeader']))
            for alerta in alertas[:10]:  # Limit to 10
                elements.append(Paragraph(f"* {alerta}", self.styles['Answer']))

        # Timestamp and signature
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(
            f"Reporte generado automaticamente por Revisar.IA",
            self.styles['HeaderFooter']
        ))
        elements.append(Paragraph(
            f"Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            self.styles['HeaderFooter']
        ))
        elements.append(Paragraph(
            f"Modulo: Abogado del Diablo v1.0",
            self.styles['HeaderFooter']
        ))

        return elements

    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        canvas_obj.saveState()

        # Header
        canvas_obj.setFont('Helvetica-Bold', 9)
        canvas_obj.setFillColor(colors.HexColor('#4a5568'))
        canvas_obj.drawString(50, 765, "REPORTE ABOGADO DEL DIABLO")

        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#718096'))
        canvas_obj.drawRightString(562, 765, "CONFIDENCIAL - USO INTERNO")

        canvas_obj.setStrokeColor(colors.HexColor('#e2e8f0'))
        canvas_obj.line(50, 758, 562, 758)

        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#718096'))
        canvas_obj.drawString(50, 30, f"Generado por Revisar.IA - {datetime.now().strftime('%d/%m/%Y')}")
        canvas_obj.drawRightString(562, 30, f"Pagina {doc.page}")

        canvas_obj.restoreState()

    async def generate_and_send_report(
        self,
        proyecto_data: Dict[str, Any],
        respuestas: Dict[str, Dict[str, Any]],
        admin_email: str = None
    ) -> Dict[str, Any]:
        """
        Generate Devil's Advocate report, upload to pCloud, and send email.

        Args:
            proyecto_data: Project information
            respuestas: Dictionary of responses {pregunta_id: {respuesta, indice_opcion}}
            admin_email: Override email recipient (default: santiago@satma.mx)

        Returns:
            Result with PDF buffer, pCloud link, and email status
        """
        from services.devils_advocate_service import get_devils_advocate_service
        from services.email_service import email_service

        try:
            # Get the Devil's Advocate service
            da_service = get_devils_advocate_service()

            # Generate evaluation
            evaluacion = da_service.generar_resumen_evaluacion(respuestas)

            # Get all questions for the report
            todas_preguntas = da_service.obtener_preguntas_estructuradas()

            # Organize questions by block with their responses
            preguntas_respuestas = {}
            for pregunta in todas_preguntas:
                bloque = pregunta['bloque']
                if bloque not in preguntas_respuestas:
                    preguntas_respuestas[bloque] = []

                pregunta_id = pregunta['id']
                respuesta_data = respuestas.get(pregunta_id, {})

                preguntas_respuestas[bloque].append({
                    **pregunta,
                    'respuesta': respuesta_data.get('respuesta', ''),
                    'indice_opcion': respuesta_data.get('indice_opcion'),
                    'bandera_roja': any(
                        br.get('pregunta_id') == pregunta_id
                        for br in evaluacion.get('banderas_rojas', [])
                    )
                })

            # Build report data
            report_data = {
                'proyecto': proyecto_data,
                'evaluacion': evaluacion,
                'preguntas_respuestas': preguntas_respuestas,
                'fecha_generacion': datetime.now().isoformat()
            }

            # Generate PDF
            pdf_buffer = await self.generate_pdf(report_data)

            # Generate filename
            proyecto_id = proyecto_data.get('id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"AbogadoDelDiablo_{proyecto_id}_{timestamp}.pdf"

            result = {
                'success': True,
                'pdf_buffer': pdf_buffer,
                'filename': filename,
                'evaluacion': evaluacion,
            }

            # Try to upload to pCloud
            try:
                from services.pcloud_service import pcloud_service

                rfc = proyecto_data.get('rfc', 'SIN_RFC')
                year = datetime.now().strftime('%Y')
                code = proyecto_id

                upload_result = pcloud_service.sincronizar_documento(
                    defense_file_path=f"{rfc}/{year}/{code}",
                    tipo_documento="reporte",
                    nombre=filename,
                    contenido=pdf_buffer.getvalue()
                )

                if upload_result.get('success'):
                    result['pcloud_link'] = upload_result.get('public_link')
                    result['pcloud_file_id'] = upload_result.get('file_id')
                    logger.info(f"Devils Advocate report uploaded to pCloud: {result['pcloud_link']}")
                else:
                    logger.warning(f"pCloud upload failed: {upload_result.get('error')}")
                    result['pcloud_error'] = upload_result.get('error')

            except Exception as e:
                logger.warning(f"pCloud integration not available: {e}")
                result['pcloud_error'] = str(e)

            # Send email notification
            recipient = admin_email or ADMIN_EMAIL
            try:
                email_result = await self._send_report_email(
                    to=recipient,
                    proyecto_data=proyecto_data,
                    evaluacion=evaluacion,
                    pdf_buffer=pdf_buffer,
                    filename=filename,
                    pcloud_link=result.get('pcloud_link')
                )
                result['email_sent'] = email_result.get('success', False)
                result['email_result'] = email_result
            except Exception as e:
                logger.error(f"Email sending failed: {e}")
                result['email_error'] = str(e)
                result['email_sent'] = False

            return result

        except Exception as e:
            logger.error(f"Error generating Devil's Advocate report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _send_report_email(
        self,
        to: str,
        proyecto_data: Dict[str, Any],
        evaluacion: Dict[str, Any],
        pdf_buffer: BytesIO,
        filename: str,
        pcloud_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email with the Devil's Advocate report attached."""
        from services.email_service import email_service

        proyecto_id = proyecto_data.get('id', 'N/A')
        empresa = proyecto_data.get('empresa', 'N/A')
        semaforo = evaluacion.get('semaforo', 'amarillo')
        score = evaluacion.get('score_total', 0)
        banderas_rojas = evaluacion.get('total_banderas_rojas', 0)

        # Color for semaforo
        semaforo_colors = {
            'verde': '#38a169',
            'amarillo': '#d69e2e',
            'rojo': '#e53e3e'
        }
        semaforo_color = semaforo_colors.get(semaforo, '#718096')

        subject = f"[Abogado del Diablo] Reporte Proyecto {proyecto_id} - Semaforo {semaforo.upper()}"

        # Build HTML email
        pcloud_section = ""
        if pcloud_link:
            pcloud_section = f"""
            <tr>
                <td style="padding: 15px 0; border-bottom: 1px solid #e2e8f0;">
                    <a href="{pcloud_link}" style="color: #3182ce; text-decoration: none;">
                        Ver/Descargar desde pCloud
                    </a>
                </td>
            </tr>
            """

        banderas_alert = ""
        if banderas_rojas > 0:
            banderas_alert = f"""
            <div style="background-color: #fed7d7; border-left: 4px solid #e53e3e; padding: 15px; margin: 20px 0;">
                <strong style="color: #c53030;">ATENCION:</strong>
                Se detectaron <strong>{banderas_rojas}</strong> bandera(s) roja(s) que requieren revision inmediata.
            </div>
            """

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f7fafc; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">REPORTE ABOGADO DEL DIABLO</h1>
            <p style="color: #a0aec0; margin: 10px 0 0 0; font-size: 14px;">
                Control Interno y Aprendizaje Organizacional
            </p>
        </div>

        <!-- Content -->
        <div style="padding: 30px;">

            <h2 style="color: #2d3748; font-size: 18px; margin-bottom: 20px;">
                Proyecto: {empresa}
            </h2>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>ID Proyecto:</strong>
                    </td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        {proyecto_id}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>Score Total:</strong>
                    </td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        <span style="font-size: 24px; font-weight: bold;">{score:.0f}</span>/100
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>Semaforo:</strong>
                    </td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right;">
                        <span style="background-color: {semaforo_color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                            {semaforo.upper()}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>Banderas Rojas:</strong>
                    </td>
                    <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0; text-align: right; color: {'#e53e3e' if banderas_rojas > 0 else '#38a169'};">
                        <strong>{banderas_rojas}</strong>
                    </td>
                </tr>
                {pcloud_section}
            </table>

            {banderas_alert}

            <p style="color: #718096; font-size: 14px; margin-top: 20px;">
                El reporte completo en PDF se encuentra adjunto a este correo.
            </p>

        </div>

        <!-- Footer -->
        <div style="background-color: #f7fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                Generado automaticamente por Revisar.IA<br>
                {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
        </div>

    </div>
</body>
</html>
        """

        body_text = f"""
REPORTE ABOGADO DEL DIABLO
Control Interno y Aprendizaje Organizacional

Proyecto: {empresa}
ID: {proyecto_id}
Score: {score:.0f}/100
Semaforo: {semaforo.upper()}
Banderas Rojas: {banderas_rojas}

{"ATENCION: Se detectaron banderas rojas que requieren revision inmediata." if banderas_rojas > 0 else ""}

El reporte completo en PDF se encuentra adjunto a este correo.

---
Generado automaticamente por Revisar.IA
{datetime.now().strftime('%d/%m/%Y %H:%M')}
        """

        # Reset buffer position
        pdf_buffer.seek(0)

        return await email_service.send_email(
            to=to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachments=[{
                'filename': filename,
                'content': pdf_buffer.getvalue()
            }]
        )


# Global instance
devils_advocate_export_service = DevilsAdvocateExportService()


def get_devils_advocate_export_service() -> DevilsAdvocateExportService:
    """Get the Devil's Advocate export service instance."""
    return devils_advocate_export_service
