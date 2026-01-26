"""
DEFENSE FILE GENERATOR - Generador de Expedientes de Defensa Fiscal
Genera PDFs profesionales y ZIPs organizados para entrega a SAT/abogados
"""

import os
import io
import json
import hashlib
import zipfile
import qrcode
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image as RLImage, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

logger = logging.getLogger(__name__)

REVISAR_IA_BLUE = colors.HexColor("#1e3a5f")
REVISAR_IA_GOLD = colors.HexColor("#c9a227")
RISK_COLORS = {
    "BAJO": colors.HexColor("#22c55e"),
    "MODERADO": colors.HexColor("#eab308"),
    "ALTO": colors.HexColor("#f97316"),
    "CRITICO": colors.HexColor("#ef4444")
}


@dataclass
class DefenseFileMetadata:
    project_id: str
    generated_at: str
    generated_by: str
    total_pages: int
    total_documents: int
    hash_sha256: str
    qr_verification_url: str


@dataclass
class DefenseFileResult:
    success: bool
    project_id: str
    zip_path: str
    metadata: Optional[DefenseFileMetadata]
    files_generated: List[str]
    total_size_bytes: int
    error: Optional[str] = None


class DefenseFileGenerator:
    """
    Generador de Expedientes de Defensa Fiscal
    Crea documentación profesional para auditorías SAT
    """
    
    OUTPUT_DIR = "defense_files"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para los PDFs"""
        self.styles.add(ParagraphStyle(
            name='TitleRevisar',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=REVISAR_IA_BLUE,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SubtitleRevisar',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=REVISAR_IA_BLUE,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='BodyRevisar',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY
        ))
        self.styles.add(ParagraphStyle(
            name='HeaderSection',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=REVISAR_IA_BLUE,
            spaceBefore=15,
            spaceAfter=8,
            borderColor=REVISAR_IA_BLUE,
            borderWidth=1,
            borderPadding=5
        ))
    
    async def generate_defense_file(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        deliberations: List[Dict[str, Any]],
        documents: List[Dict[str, Any]],
        risk_assessment: Optional[Dict[str, Any]] = None
    ) -> DefenseFileResult:
        """
        Genera el expediente de defensa completo
        
        Args:
            project_id: ID del proyecto
            project_data: Datos del proyecto (tipologia, monto, descripcion, etc.)
            deliberations: Lista de deliberaciones de agentes
            documents: Lista de documentos del proyecto
            risk_assessment: Evaluación de riesgo (opcional)
        """
        try:
            logger.info(f"[DefenseFile] Iniciando generación para proyecto {project_id}")
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            project_dir = os.path.join(self.OUTPUT_DIR, f"{project_id}_{timestamp}")
            os.makedirs(project_dir, exist_ok=True)
            
            files_generated = []
            
            cover_pdf = await self._generate_cover_pdf(project_dir, project_id, project_data, risk_assessment)
            files_generated.append(cover_pdf)
            
            index_pdf = await self._generate_index_pdf(project_dir, project_id, documents, deliberations)
            files_generated.append(index_pdf)
            
            deliberations_pdf = await self._generate_deliberations_pdf(project_dir, project_id, deliberations)
            files_generated.append(deliberations_pdf)
            
            risk_pdf = await self._generate_risk_assessment_pdf(project_dir, project_id, risk_assessment or {})
            files_generated.append(risk_pdf)
            
            metadata_json = await self._generate_metadata_json(project_dir, project_id, project_data, files_generated)
            files_generated.append(metadata_json)
            
            zip_path = await self._create_defense_zip(project_dir, project_id, files_generated, documents)
            
            with open(zip_path, 'rb') as f:
                zip_hash = hashlib.sha256(f.read()).hexdigest()
            
            total_size = os.path.getsize(zip_path)
            
            metadata = DefenseFileMetadata(
                project_id=project_id,
                generated_at=datetime.now(timezone.utc).isoformat(),
                generated_by="Revisar.ia - Revisar.IA",
                total_pages=self._count_total_pages(files_generated),
                total_documents=len(documents),
                hash_sha256=zip_hash,
                qr_verification_url=f"https://revisar.ia/verify/{project_id}/{zip_hash[:16]}"
            )
            
            logger.info(f"[DefenseFile] Expediente generado exitosamente: {zip_path}")
            
            return DefenseFileResult(
                success=True,
                project_id=project_id,
                zip_path=zip_path,
                metadata=metadata,
                files_generated=files_generated,
                total_size_bytes=total_size
            )
            
        except Exception as e:
            logger.error(f"[DefenseFile] Error generando expediente: {e}")
            return DefenseFileResult(
                success=False,
                project_id=project_id,
                zip_path="",
                metadata=None,
                files_generated=[],
                total_size_bytes=0,
                error=str(e)
            )
    
    async def _generate_cover_pdf(
        self,
        output_dir: str,
        project_id: str,
        project_data: Dict[str, Any],
        risk_assessment: Optional[Dict[str, Any]]
    ) -> str:
        """Genera PDF de carátula con resumen ejecutivo"""
        
        filename = os.path.join(output_dir, "00_CARATULA.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        story.append(Paragraph("EXPEDIENTE DE DEFENSA FISCAL", self.styles['TitleRevisar']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Sistema Revisar.IA - Revisar.ia", self.styles['SubtitleRevisar']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(HRFlowable(width="100%", thickness=2, color=REVISAR_IA_BLUE))
        story.append(Spacer(1, 0.3*inch))
        
        info_data = [
            ["ID Proyecto:", project_id],
            ["Tipología:", project_data.get("tipologia", "N/A")],
            ["Monto Contrato:", f"${project_data.get('monto_contrato', 0):,.2f} MXN"],
            ["Fecha Generación:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Proveedor:", project_data.get("proveedor", "N/A")],
            ["RFC Proveedor:", project_data.get("rfc_proveedor", "N/A")]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), REVISAR_IA_BLUE),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("RESUMEN EJECUTIVO", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        descripcion = project_data.get("descripcion_servicio", project_data.get("descripcion", "Sin descripción disponible"))
        story.append(Paragraph(f"<b>Descripción del Servicio:</b> {descripcion}", self.styles['BodyRevisar']))
        story.append(Spacer(1, 0.2*inch))
        
        justificacion = project_data.get("justificacion_economica", "Sin justificación registrada")
        story.append(Paragraph(f"<b>Justificación Económica:</b> {justificacion}", self.styles['BodyRevisar']))
        story.append(Spacer(1, 0.3*inch))
        
        if risk_assessment:
            story.append(Paragraph("EVALUACIÓN DE RIESGO", self.styles['HeaderSection']))
            story.append(Spacer(1, 0.2*inch))
            
            risk_score = risk_assessment.get("score", 0)
            risk_level = self._get_risk_level(risk_score)
            
            risk_data = [
                ["Score de Riesgo:", f"{risk_score}/100"],
                ["Nivel:", risk_level],
                ["Certificación:", "BULLETPROOF" if risk_assessment.get("bulletproof", False) else "REQUIERE REVISIÓN"]
            ]
            
            risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
            risk_color = RISK_COLORS.get(risk_level, colors.gray)
            risk_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (1, 1), (1, 1), risk_color),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(risk_table)
        
        story.append(Spacer(1, 0.5*inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.gray))
        story.append(Spacer(1, 0.2*inch))
        
        qr_data = f"REVISAR.IA|{project_id}|{datetime.now().isoformat()}"
        qr = qrcode.make(qr_data)
        qr_img = qr
        
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        qr_path = os.path.join(output_dir, "temp_qr.png")
        with open(qr_path, 'wb') as f:
            f.write(qr_buffer.getvalue())
        
        story.append(Paragraph("Código de Verificación:", self.styles['BodyRevisar']))
        story.append(RLImage(qr_path, width=1.5*inch, height=1.5*inch))
        
        doc.build(story)
        
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        logger.info(f"[DefenseFile] Carátula generada: {filename}")
        return filename
    
    async def _generate_index_pdf(
        self,
        output_dir: str,
        project_id: str,
        documents: List[Dict[str, Any]],
        deliberations: List[Dict[str, Any]]
    ) -> str:
        """Genera PDF de índice con checklist de documentos"""
        
        filename = os.path.join(output_dir, "01_INDICE_MAESTRO.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.75*inch)
        
        story = []
        
        story.append(Paragraph("ÍNDICE MAESTRO DEL EXPEDIENTE", self.styles['TitleRevisar']))
        story.append(Paragraph(f"Proyecto: {project_id}", self.styles['SubtitleRevisar']))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("ESTRUCTURA DEL EXPEDIENTE", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        structure = [
            ["Carpeta", "Contenido", "Estado"],
            ["00_CARATULA", "Resumen ejecutivo y datos generales", "✓"],
            ["01_INDICE_MAESTRO", "Este documento - índice completo", "✓"],
            ["02_DELIBERACIONES", "Análisis de agentes IA", "✓"],
            ["03_EVALUACION_RIESGO", "Assessment de vulnerabilidades", "✓"],
            ["04_DOCUMENTOS", "Evidencia documental", f"{len(documents)} docs"],
            ["05_METADATOS", "Hashes y verificación de integridad", "✓"]
        ]
        
        structure_table = Table(structure, colWidths=[1.8*inch, 3*inch, 1.2*inch])
        structure_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), REVISAR_IA_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(structure_table)
        story.append(Spacer(1, 0.4*inch))
        
        story.append(Paragraph("CHECKLIST DE DOCUMENTOS", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        doc_data = [["#", "Tipo", "Nombre", "Estado", "Validado"]]
        for i, doc_item in enumerate(documents, 1):
            doc_data.append([
                str(i),
                doc_item.get("tipo", doc_item.get("type", "N/A")),
                doc_item.get("nombre", doc_item.get("name", "Sin nombre"))[:30],
                "✓" if doc_item.get("existe", doc_item.get("exists", True)) else "✗",
                "✓" if doc_item.get("validado", doc_item.get("validated", False)) else "Pendiente"
            ])
        
        if len(doc_data) > 1:
            doc_table = Table(doc_data, colWidths=[0.4*inch, 1.2*inch, 2.5*inch, 0.8*inch, 1*inch])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), REVISAR_IA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (3, 0), (4, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(doc_table)
        else:
            story.append(Paragraph("No hay documentos registrados en este expediente.", self.styles['BodyRevisar']))
        
        story.append(Spacer(1, 0.4*inch))
        
        story.append(Paragraph("DELIBERACIONES DE AGENTES", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        delib_data = [["Agente", "Decisión", "Score", "Fecha"]]
        for delib in deliberations:
            agent = delib.get("agent_id", delib.get("agente", "N/A"))
            decision = delib.get("decision", delib.get("resultado", "N/A"))
            score = delib.get("score", delib.get("confidence", "N/A"))
            fecha = delib.get("timestamp", delib.get("fecha", "N/A"))
            if isinstance(fecha, str) and len(fecha) > 16:
                fecha = fecha[:16]
            delib_data.append([agent, decision, str(score), fecha])
        
        if len(delib_data) > 1:
            delib_table = Table(delib_data, colWidths=[1.5*inch, 1.8*inch, 1*inch, 1.7*inch])
            delib_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), REVISAR_IA_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(delib_table)
        
        doc.build(story)
        logger.info(f"[DefenseFile] Índice generado: {filename}")
        return filename
    
    async def _generate_deliberations_pdf(
        self,
        output_dir: str,
        project_id: str,
        deliberations: List[Dict[str, Any]]
    ) -> str:
        """Genera PDF con todas las deliberaciones de agentes"""
        
        filename = os.path.join(output_dir, "02_DELIBERACIONES.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.75*inch)
        
        story = []
        
        story.append(Paragraph("DELIBERACIONES DE AGENTES IA", self.styles['TitleRevisar']))
        story.append(Paragraph(f"Proyecto: {project_id}", self.styles['SubtitleRevisar']))
        story.append(Spacer(1, 0.3*inch))
        
        agent_names = {
            "A1": "Estrategia (María)",
            "A2": "PMO (Carlos)",
            "A3": "Fiscal (Laura)",
            "A4": "Legal (Gestor IA)",
            "A5": "Finanzas (Roberto)",
            "A6": "Proveedor (Ana)",
            "A7": "Defensa (Sistema)",
            "A8": "Auditor (Sistema)"
        }
        
        for delib in deliberations:
            agent_id = delib.get("agent_id", delib.get("agente", "Unknown"))
            agent_display = agent_names.get(agent_id, agent_id)
            
            story.append(Paragraph(f"AGENTE: {agent_display}", self.styles['HeaderSection']))
            story.append(Spacer(1, 0.15*inch))
            
            decision = delib.get("decision", delib.get("resultado", "N/A"))
            decision_color = {
                "approved": "green",
                "aprobado": "green",
                "rejected": "red",
                "rechazado": "red",
                "request_adjustment": "orange",
                "ajuste": "orange"
            }.get(decision.lower(), "black")
            
            story.append(Paragraph(f"<b>Decisión:</b> <font color='{decision_color}'>{decision.upper()}</font>", self.styles['BodyRevisar']))
            story.append(Paragraph(f"<b>Score/Confianza:</b> {delib.get('score', delib.get('confidence', 'N/A'))}", self.styles['BodyRevisar']))
            story.append(Paragraph(f"<b>Timestamp:</b> {delib.get('timestamp', delib.get('fecha', 'N/A'))}", self.styles['BodyRevisar']))
            story.append(Spacer(1, 0.1*inch))
            
            reasoning = delib.get("reasoning", delib.get("razonamiento", delib.get("analisis", "")))
            if reasoning:
                story.append(Paragraph("<b>Razonamiento:</b>", self.styles['BodyRevisar']))
                story.append(Paragraph(str(reasoning)[:1000], self.styles['BodyRevisar']))
            
            recommendations = delib.get("recommendations", delib.get("recomendaciones", []))
            if recommendations:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Recomendaciones:</b>", self.styles['BodyRevisar']))
                for rec in recommendations[:5]:
                    story.append(Paragraph(f"• {rec}", self.styles['BodyRevisar']))
            
            story.append(Spacer(1, 0.3*inch))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.gray))
            story.append(Spacer(1, 0.2*inch))
        
        if not deliberations:
            story.append(Paragraph("No hay deliberaciones registradas para este proyecto.", self.styles['BodyRevisar']))
        
        doc.build(story)
        logger.info(f"[DefenseFile] Deliberaciones generadas: {filename}")
        return filename
    
    async def _generate_risk_assessment_pdf(
        self,
        output_dir: str,
        project_id: str,
        risk_assessment: Dict[str, Any]
    ) -> str:
        """Genera PDF con evaluación de riesgos"""
        
        filename = os.path.join(output_dir, "03_EVALUACION_RIESGO.pdf")
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.75*inch)
        
        story = []
        
        story.append(Paragraph("EVALUACIÓN DE RIESGO FISCAL", self.styles['TitleRevisar']))
        story.append(Paragraph(f"Proyecto: {project_id}", self.styles['SubtitleRevisar']))
        story.append(Spacer(1, 0.3*inch))
        
        score = risk_assessment.get("score", risk_assessment.get("risk_score", 0))
        level = self._get_risk_level(score)
        bulletproof = risk_assessment.get("bulletproof", False)
        
        story.append(Paragraph("RESUMEN DE RIESGO", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        summary_data = [
            ["Métrica", "Valor"],
            ["Score Total", f"{score}/100"],
            ["Nivel de Riesgo", level],
            ["Certificación BULLETPROOF", "SÍ" if bulletproof else "NO"],
            ["Vectores Evaluados", str(risk_assessment.get("vectores_testeados", 7))],
            ["Vulnerabilidades Encontradas", str(risk_assessment.get("vulnerabilidades_encontradas", 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), REVISAR_IA_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4*inch))
        
        story.append(Paragraph("4 PILARES DE EVALUACIÓN", self.styles['HeaderSection']))
        story.append(Spacer(1, 0.2*inch))
        
        pilares = risk_assessment.get("pilares", {
            "razon_negocios": 25,
            "beneficio_economico": 25,
            "materialidad": 25,
            "trazabilidad": 25
        })
        
        pilares_data = [
            ["Pilar", "Puntuación", "Máximo"],
            ["Razón de Negocios", str(pilares.get("razon_negocios", 25)), "25"],
            ["Beneficio Económico", str(pilares.get("beneficio_economico", 25)), "25"],
            ["Materialidad", str(pilares.get("materialidad", 25)), "25"],
            ["Trazabilidad", str(pilares.get("trazabilidad", 25)), "25"],
            ["TOTAL", str(sum(pilares.values()) if isinstance(pilares, dict) else 100), "100"]
        ]
        
        pilares_table = Table(pilares_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        pilares_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), REVISAR_IA_BLUE),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e5e7eb")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(pilares_table)
        story.append(Spacer(1, 0.4*inch))
        
        vulnerabilities = risk_assessment.get("vulnerabilidades", [])
        if vulnerabilities:
            story.append(Paragraph("VULNERABILIDADES DETECTADAS", self.styles['HeaderSection']))
            story.append(Spacer(1, 0.2*inch))
            
            for vuln in vulnerabilities[:10]:
                severity = vuln.get("severity", "MEDIUM")
                severity_color = {
                    "CRITICAL": "red",
                    "HIGH": "orange",
                    "MEDIUM": "goldenrod",
                    "LOW": "green"
                }.get(severity, "gray")
                
                story.append(Paragraph(
                    f"<font color='{severity_color}'><b>[{severity}]</b></font> {vuln.get('description', vuln.get('vector_name', 'N/A'))}",
                    self.styles['BodyRevisar']
                ))
                
                if vuln.get("recommendation"):
                    story.append(Paragraph(f"  → Recomendación: {vuln['recommendation']}", self.styles['BodyRevisar']))
                
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        conclusion = risk_assessment.get("conclusion", "Evaluación completada. Revisar vulnerabilidades identificadas.")
        story.append(Paragraph(f"<b>Conclusión:</b> {conclusion}", self.styles['BodyRevisar']))
        
        doc.build(story)
        logger.info(f"[DefenseFile] Evaluación de riesgo generada: {filename}")
        return filename
    
    async def _generate_metadata_json(
        self,
        output_dir: str,
        project_id: str,
        project_data: Dict[str, Any],
        files_generated: List[str]
    ) -> str:
        """Genera archivo JSON con metadatos e integridad"""
        
        filename = os.path.join(output_dir, "05_METADATOS.json")
        
        file_hashes = {}
        for filepath in files_generated:
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    file_hashes[os.path.basename(filepath)] = hashlib.sha256(f.read()).hexdigest()
        
        metadata = {
            "expediente": {
                "proyecto_id": project_id,
                "generado_por": "Revisar.ia - Revisar.IA",
                "version": "4.0.0",
                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
                "timezone": "UTC"
            },
            "proyecto": {
                "tipologia": project_data.get("tipologia", "N/A"),
                "monto_contrato": project_data.get("monto_contrato", 0),
                "proveedor": project_data.get("proveedor", "N/A"),
                "rfc_proveedor": project_data.get("rfc_proveedor", "N/A")
            },
            "integridad": {
                "algoritmo": "SHA-256",
                "archivos": file_hashes
            },
            "legal": {
                "disclaimer": "Este expediente fue generado automáticamente por el sistema Revisar.IA de Revisar.ia. La información contenida es confidencial y está protegida por la normatividad aplicable.",
                "normativa_aplicable": ["CFF Art. 5-A", "CFF Art. 69-B", "NOM-151-SCFI-2016"],
                "contacto": "soporte@revisar-ia.com"
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[DefenseFile] Metadatos generados: {filename}")
        return filename
    
    async def _create_defense_zip(
        self,
        project_dir: str,
        project_id: str,
        files_generated: List[str],
        documents: List[Dict[str, Any]]
    ) -> str:
        """Crea el archivo ZIP final con estructura organizada"""
        
        zip_filename = os.path.join(self.OUTPUT_DIR, f"EXPEDIENTE_{project_id}.zip")
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filepath in files_generated:
                if os.path.exists(filepath):
                    arcname = os.path.basename(filepath)
                    zipf.write(filepath, arcname)
            
            zipf.writestr("04_DOCUMENTOS/.gitkeep", "")
            
            for i, doc in enumerate(documents, 1):
                doc_info = f"Documento {i}: {doc.get('nombre', doc.get('name', 'N/A'))}\n"
                doc_info += f"Tipo: {doc.get('tipo', doc.get('type', 'N/A'))}\n"
                doc_info += f"Ruta original: {doc.get('path', doc.get('file_path', 'N/A'))}\n"
                zipf.writestr(f"04_DOCUMENTOS/doc_{i:02d}_info.txt", doc_info)
            
            readme = f"""EXPEDIENTE DE DEFENSA FISCAL
============================
Proyecto: {project_id}
Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Sistema: Revisar.IA - Revisar.ia

ESTRUCTURA:
- 00_CARATULA.pdf: Resumen ejecutivo
- 01_INDICE_MAESTRO.pdf: Índice y checklist
- 02_DELIBERACIONES.pdf: Análisis de agentes IA
- 03_EVALUACION_RIESGO.pdf: Assessment de vulnerabilidades
- 04_DOCUMENTOS/: Evidencia documental
- 05_METADATOS.json: Hashes y verificación

VERIFICACIÓN DE INTEGRIDAD:
Consulte 05_METADATOS.json para los hashes SHA-256 de cada archivo.

CONTACTO:
soporte@revisar.ia
"""
            zipf.writestr("README.txt", readme)
        
        logger.info(f"[DefenseFile] ZIP creado: {zip_filename}")
        return zip_filename
    
    def _get_risk_level(self, score: int) -> str:
        """Determina el nivel de riesgo basado en el score"""
        if score >= 70:
            return "CRITICO"
        elif score >= 50:
            return "ALTO"
        elif score >= 30:
            return "MODERADO"
        else:
            return "BAJO"
    
    def _count_total_pages(self, files: List[str]) -> int:
        """Cuenta el total de páginas en los PDFs generados"""
        total = 0
        try:
            from PyPDF2 import PdfReader
            for filepath in files:
                if filepath.endswith('.pdf') and os.path.exists(filepath):
                    reader = PdfReader(filepath)
                    total += len(reader.pages)
        except Exception:
            total = len([f for f in files if f.endswith('.pdf')]) * 2
        return total
    
    async def list_defense_files(self) -> List[Dict[str, Any]]:
        """Lista todos los expedientes de defensa generados"""
        files = []
        
        if not os.path.exists(self.OUTPUT_DIR):
            return files
        
        for filename in os.listdir(self.OUTPUT_DIR):
            if filename.startswith("EXPEDIENTE_") and filename.endswith(".zip"):
                filepath = os.path.join(self.OUTPUT_DIR, filename)
                project_id = filename.replace("EXPEDIENTE_", "").replace(".zip", "")
                
                files.append({
                    "filename": filename,
                    "project_id": project_id,
                    "path": filepath,
                    "size_bytes": os.path.getsize(filepath),
                    "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        
        return sorted(files, key=lambda x: x["created_at"], reverse=True)
    
    async def get_defense_file_preview(self, project_id: str) -> Dict[str, Any]:
        """Obtiene preview de un expediente sin generarlo"""
        zip_path = os.path.join(self.OUTPUT_DIR, f"EXPEDIENTE_{project_id}.zip")
        
        if not os.path.exists(zip_path):
            return {"exists": False, "project_id": project_id}
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            return {
                "exists": True,
                "project_id": project_id,
                "path": zip_path,
                "size_bytes": os.path.getsize(zip_path),
                "files": zipf.namelist(),
                "created_at": datetime.fromtimestamp(os.path.getctime(zip_path)).isoformat()
            }


    async def generate_complete_defense_file(
        self,
        proyecto_id: str,
        version: str = "1.0"
    ) -> str:
        """
        Genera expediente de defensa con datos mínimos - wrapper para test_runner
        
        Args:
            proyecto_id: ID del proyecto
            version: Versión del expediente
            
        Returns:
            Path al archivo PDF principal generado
        """
        try:
            project_data = {
                "id": proyecto_id,
                "tipologia": "SOFTWARE_SAAS_DESARROLLO",
                "nombre": f"Proyecto {proyecto_id}",
                "descripcion": "Proyecto generado automáticamente",
                "monto": 1500000,
                "version": version,
                "fecha_inicio": datetime.now().isoformat(),
                "sponsor": "Revisar.IA Test"
            }
            
            deliberations = [
                {
                    "agente": "A1_ESTRATEGIA",
                    "dictamen": "APROBAR",
                    "score": 85,
                    "analisis": "Proyecto alineado con estrategia corporativa",
                    "fecha": datetime.now().isoformat()
                },
                {
                    "agente": "A3_FISCAL",
                    "dictamen": "APROBAR",
                    "score": 80,
                    "analisis": "Cumple requisitos Art. 27 LISR",
                    "fecha": datetime.now().isoformat()
                },
                {
                    "agente": "A5_FINANZAS",
                    "dictamen": "APROBAR",
                    "score": 82,
                    "analisis": "ROI justificado, monto razonable",
                    "fecha": datetime.now().isoformat()
                },
                {
                    "agente": "A6_PROVEEDOR",
                    "dictamen": "APROBAR",
                    "score": 78,
                    "analisis": "Proveedor verificado, no en lista 69-B",
                    "fecha": datetime.now().isoformat()
                }
            ]
            
            documents = [
                {"tipo": "contrato", "nombre": "Contrato de servicios", "estado": "completo"},
                {"tipo": "factura", "nombre": "CFDI Factura", "estado": "completo"},
                {"tipo": "sow", "nombre": "Statement of Work", "estado": "completo"}
            ]
            
            risk_assessment = {
                "nivel_global": "BAJO",
                "score": 81,
                "factores": [
                    {"factor": "Sustancia económica", "nivel": "BAJO"},
                    {"factor": "Razón de negocios", "nivel": "BAJO"},
                    {"factor": "Proveedor verificado", "nivel": "BAJO"}
                ]
            }
            
            result = await self.generate_defense_file(
                project_id=proyecto_id,
                project_data=project_data,
                deliberations=deliberations,
                documents=documents,
                risk_assessment=risk_assessment
            )
            
            if result.success and result.zip_path:
                return result.zip_path
            else:
                logger.error(f"Error generando expediente: {result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error en generate_complete_defense_file: {e}")
            return None


defense_file_generator = DefenseFileGenerator()
