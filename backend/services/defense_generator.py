"""
Defense File Generator
PROPÓSITO: Generar ZIP con expediente completo + PDF índice narrativo
para defensa fiscal ante SAT
"""

import os
import json
import shutil
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from services.defense_file_service import defense_file_service, DefenseFile

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("./uploads")
REPORTS_DIR = Path("./reports")
TEMP_DIR = Path("/tmp/expedientes")
TEMP_DIR.mkdir(exist_ok=True)


class DefenseFileGenerator:
    """
    Genera expediente de defensa completo en formato ZIP con:
    - Índice maestro en PDF (narrativa legal)
    - Estructura de carpetas organizada
    - Todos los documentos de evidencia
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        self.styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#1e3a5f'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282'),
            borderWidth=1,
            borderColor=colors.HexColor('#2c5282'),
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyCustom',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=5
        ))
    
    def generate_dossier(self, project_id: str) -> str:
        """
        Genera expediente de defensa con estructura:
        
        EXPEDIENTE_PROYECTO_ABC123.zip
        ├── 00_INDICE_MAESTRO.pdf  ← Narrativa legal
        ├── 01_SOLICITUD_COMPRA/
        │   ├── SOW_firmado.pdf
        │   └── metadata.json
        ├── 02_APROBACIONES/
        │   ├── F2_BUDGET_APPROVED.json
        │   └── F6_MATERIALITY_APPROVED.json
        ├── 03_EVIDENCIAS_EJECUCION/
        │   ├── entregables/
        │   └── minutas/
        ├── 04_COMPROBANTES_PAGO/
        │   ├── factura_XXXX.pdf
        │   └── transferencia_YYYY.pdf
        └── 05_ANALISIS_RIESGO/
            ├── risk_assessment.json
            └── defense_strategy.md
        """
        df = defense_file_service.get_or_create(project_id)
        project = df.project_data
        
        temp_dir = TEMP_DIR / f"expediente_{project_id}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        
        folders = [
            "01_SOLICITUD_COMPRA",
            "02_APROBACIONES",
            "03_EVIDENCIAS_EJECUCION",
            "03_EVIDENCIAS_EJECUCION/entregables",
            "03_EVIDENCIAS_EJECUCION/minutas",
            "04_COMPROBANTES_PAGO",
            "05_ANALISIS_RIESGO"
        ]
        for folder in folders:
            (temp_dir / folder).mkdir(parents=True, exist_ok=True)
        
        self._copy_evidence_files(df, temp_dir)
        self._generate_approval_files(df, temp_dir)
        self._generate_risk_assessment(df, temp_dir)
        
        indice_path = temp_dir / "00_INDICE_MAESTRO.pdf"
        self._generate_master_index(df, str(indice_path))
        
        zip_path = str(TEMP_DIR / f"EXPEDIENTE_{project_id}")
        shutil.make_archive(zip_path, 'zip', temp_dir)
        
        logger.info(f"Expediente generado: {zip_path}.zip")
        return f"{zip_path}.zip"
    
    def _copy_evidence_files(self, df: DefenseFile, temp_dir: Path):
        """Copia archivos de evidencia a la estructura"""
        for doc in df.documents:
            src_path = Path(doc.get("file_path", ""))
            if src_path.exists():
                doc_type = doc.get("doc_type", "unknown")
                if "sow" in doc_type.lower() or "contrato" in doc_type.lower():
                    dest_folder = temp_dir / "01_SOLICITUD_COMPRA"
                elif "factura" in doc_type.lower() or "cfdi" in doc_type.lower():
                    dest_folder = temp_dir / "04_COMPROBANTES_PAGO"
                elif "transferencia" in doc_type.lower() or "pago" in doc_type.lower():
                    dest_folder = temp_dir / "04_COMPROBANTES_PAGO"
                elif "entregable" in doc_type.lower():
                    dest_folder = temp_dir / "03_EVIDENCIAS_EJECUCION/entregables"
                elif "minuta" in doc_type.lower() or "acta" in doc_type.lower():
                    dest_folder = temp_dir / "03_EVIDENCIAS_EJECUCION/minutas"
                else:
                    dest_folder = temp_dir / "03_EVIDENCIAS_EJECUCION"
                
                dest_path = dest_folder / src_path.name
                shutil.copy2(src_path, dest_path)
        
        project_uploads = UPLOADS_DIR / df.project_id
        if project_uploads.exists():
            for file_path in project_uploads.glob("**/*"):
                if file_path.is_file():
                    dest_folder = temp_dir / "03_EVIDENCIAS_EJECUCION"
                    shutil.copy2(file_path, dest_folder / file_path.name)
    
    def _generate_approval_files(self, df: DefenseFile, temp_dir: Path):
        """Genera archivos JSON de aprobaciones"""
        approvals_dir = temp_dir / "02_APROBACIONES"
        
        for delib in df.deliberations:
            agent_id = delib.get("agent_id", "unknown")
            stage = delib.get("stage", "unknown")
            decision = delib.get("decision", "unknown")
            
            approval_data = {
                "agent_id": agent_id,
                "stage": stage,
                "decision": decision,
                "timestamp": delib.get("recorded_at"),
                "reasoning": delib.get("reasoning", ""),
                "score": delib.get("score", 0),
                "compliance_items": delib.get("compliance_items", [])
            }
            
            filename = f"{stage}_{agent_id}_{decision}.json"
            with open(approvals_dir / filename, "w", encoding="utf-8") as f:
                json.dump(approval_data, f, ensure_ascii=False, indent=2)
    
    def _generate_risk_assessment(self, df: DefenseFile, temp_dir: Path):
        """Genera evaluación de riesgo y estrategia de defensa"""
        risk_dir = temp_dir / "05_ANALISIS_RIESGO"
        
        risk_data = {
            "project_id": df.project_id,
            "evaluation_date": datetime.now(timezone.utc).isoformat(),
            "risk_score": self._calculate_risk_score(df),
            "compliance_checklist": df.compliance_checklist,
            "deliberation_summary": [
                {
                    "agent": d.get("agent_id"),
                    "decision": d.get("decision"),
                    "score": d.get("score", 0)
                }
                for d in df.deliberations
            ],
            "evidence_count": {
                "deliberations": len(df.deliberations),
                "emails": len(df.emails),
                "documents": len(df.documents),
                "pcloud_documents": len(df.pcloud_documents)
            }
        }
        
        with open(risk_dir / "risk_assessment.json", "w", encoding="utf-8") as f:
            json.dump(risk_data, f, ensure_ascii=False, indent=2)
        
        defense_strategy = self._generate_defense_strategy(df)
        with open(risk_dir / "defense_strategy.md", "w", encoding="utf-8") as f:
            f.write(defense_strategy)
    
    def _calculate_risk_score(self, df: DefenseFile) -> int:
        """Calcula score de riesgo basado en compliance"""
        base_score = 100
        checklist = df.compliance_checklist
        
        if not checklist.get("razon_de_negocios", False):
            base_score -= 25
        if not checklist.get("beneficio_economico", False):
            base_score -= 25
        if not checklist.get("materialidad", False):
            base_score -= 25
        if not checklist.get("trazabilidad", False):
            base_score -= 25
        
        risk = 100 - base_score
        return risk
    
    def _generate_defense_strategy(self, df: DefenseFile) -> str:
        """Genera documento de estrategia de defensa en Markdown"""
        project = df.project_data
        
        strategy = f"""# Estrategia de Defensa Fiscal

## Proyecto: {project.get('name', df.project_id)}

### Fecha de Evaluación
{datetime.now().strftime('%d de %B de %Y')}

---

## 1. Resumen Ejecutivo

Este expediente contiene toda la documentación necesaria para defender
la deducibilidad fiscal de los servicios contratados bajo el proyecto
**{project.get('name', df.project_id)}**.

### Datos del Proyecto
- **RFC Contribuyente:** {project.get('taxpayer_rfc', 'N/A')}
- **Proveedor:** {project.get('vendor_name', 'N/A')}
- **RFC Proveedor:** {project.get('vendor_rfc', 'N/A')}
- **Monto:** ${project.get('budget', 0):,.2f} MXN
- **Periodo Fiscal:** {project.get('fiscal_year', datetime.now().year)}

---

## 2. Fundamentación Legal

### Artículo 5-A CFF - Razón de Negocios
{'✅ CUMPLE' if df.compliance_checklist.get('razon_de_negocios') else '⚠️ PENDIENTE'}
- Los actos jurídicos tienen una razón de negocios documentada
- Existe un propósito económico distinto al beneficio fiscal

### Artículo 27 LISR - Requisitos de Deducibilidad
{'✅ CUMPLE' if df.compliance_checklist.get('beneficio_economico') else '⚠️ PENDIENTE'}
- El gasto es estrictamente indispensable para la actividad
- Se cuenta con documentación comprobatoria adecuada

### Artículo 69-B CFF - Materialidad de Operaciones
{'✅ CUMPLE' if df.compliance_checklist.get('materialidad') else '⚠️ PENDIENTE'}
- Existe evidencia de servicios realmente prestados
- El proveedor tiene capacidad operativa demostrable

### NOM-151 - Conservación de Mensajes de Datos
{'✅ CUMPLE' if df.compliance_checklist.get('trazabilidad') else '⚠️ PENDIENTE'}
- Trail completo de comunicaciones y deliberaciones
- Documentos electrónicos con integridad verificable

---

## 3. Evidencia Disponible

### Deliberaciones de Agentes
- Total de deliberaciones: {len(df.deliberations)}
- Agentes que aprobaron: {sum(1 for d in df.deliberations if d.get('decision') == 'approved')}

### Documentos
- Documentos locales: {len(df.documents)}
- Documentos en pCloud: {len(df.pcloud_documents)}

### Comunicaciones
- Correos electrónicos registrados: {len(df.emails)}
- Comunicaciones con proveedor: {len(df.provider_communications)}

---

## 4. Puntos de Defensa Recomendados

1. **Razón de Negocios:** El proyecto fue aprobado siguiendo el POE
   institucional con validación de múltiples áreas.

2. **Beneficio Económico:** Se documentó el ROI esperado y los
   beneficios tangibles para la operación.

3. **Materialidad:** Existen entregables verificables y registros
   de ejecución del servicio.

4. **Trazabilidad:** Todo el proceso está documentado con timestamps
   y evidencia electrónica.

---

## 5. Índice de Carpetas

- `01_SOLICITUD_COMPRA/` - SOW y documentos de contratación
- `02_APROBACIONES/` - Registros de aprobación por agente
- `03_EVIDENCIAS_EJECUCION/` - Entregables y minutas
- `04_COMPROBANTES_PAGO/` - Facturas y transferencias
- `05_ANALISIS_RIESGO/` - Este documento y evaluación

---

*Expediente generado automáticamente por Revisar.IA*
*Sistema de Auditoría Fiscal - Revisar.ia*
"""
        return strategy
    
    def _generate_master_index(self, df: DefenseFile, output_path: str):
        """Genera PDF índice maestro con narrativa legal"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        project = df.project_data
        
        story.append(Paragraph("EXPEDIENTE DE DEFENSA FISCAL", self.styles['TitleCustom']))
        story.append(Spacer(1, 12))
        
        header_data = [
            ["Proyecto:", project.get('name', df.project_id)],
            ["RFC Contribuyente:", project.get('taxpayer_rfc', 'N/A')],
            ["Proveedor:", project.get('vendor_name', 'N/A')],
            ["Periodo Fiscal:", str(project.get('fiscal_year', datetime.now().year))],
            ["Fecha de Generación:", datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e3a5f')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0'))
        ]))
        story.append(header_table)
        story.append(Spacer(1, 24))
        
        story.append(Paragraph("CRONOLOGÍA DE HECHOS", self.styles['SectionHeader']))
        
        events = self._build_chronology(df)
        for i, event in enumerate(events, 1):
            event_text = f"<b>{i}. [{event['date']}]</b> {event['description']}"
            story.append(Paragraph(event_text, self.styles['BodyCustom']))
            if event.get('details'):
                for detail in event['details']:
                    story.append(Paragraph(f"• {detail}", self.styles['BulletPoint']))
        
        story.append(Spacer(1, 12))
        story.append(Paragraph("ANÁLISIS DE CUMPLIMIENTO FISCAL", self.styles['SectionHeader']))
        
        compliance_data = [
            ["Requisito", "Estado", "Fundamento Legal"],
            ["Razón de Negocios", 
             "✓ CUMPLE" if df.compliance_checklist.get('razon_de_negocios') else "⚠ PENDIENTE",
             "Art. 5-A CFF"],
            ["Beneficio Económico",
             "✓ CUMPLE" if df.compliance_checklist.get('beneficio_economico') else "⚠ PENDIENTE",
             "Art. 27 LISR"],
            ["Materialidad",
             "✓ CUMPLE" if df.compliance_checklist.get('materialidad') else "⚠ PENDIENTE",
             "Art. 69-B CFF"],
            ["Trazabilidad",
             "✓ CUMPLE" if df.compliance_checklist.get('trazabilidad') else "⚠ PENDIENTE",
             "NOM-151"]
        ]
        
        compliance_table = Table(compliance_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        compliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        story.append(compliance_table)
        
        risk_score = self._calculate_risk_score(df)
        story.append(Spacer(1, 24))
        story.append(Paragraph("EVALUACIÓN DE RIESGO", self.styles['SectionHeader']))
        
        if risk_score <= 29:
            risk_level = "BAJO"
            risk_color = colors.HexColor('#38a169')
        elif risk_score <= 49:
            risk_level = "MODERADO"
            risk_color = colors.HexColor('#d69e2e')
        elif risk_score <= 69:
            risk_level = "ALTO"
            risk_color = colors.HexColor('#dd6b20')
        else:
            risk_level = "CRÍTICO"
            risk_color = colors.HexColor('#e53e3e')
        
        risk_text = f"Score de Riesgo: <font color='{risk_color.hexval()}'><b>{risk_score}/100 ({risk_level})</b></font>"
        story.append(Paragraph(risk_text, self.styles['BodyCustom']))
        
        story.append(PageBreak())
        story.append(Paragraph("ÍNDICE DE EVIDENCIAS", self.styles['SectionHeader']))
        
        evidence_text = """
        Este expediente contiene la siguiente estructura de carpetas:
        
        <b>01_SOLICITUD_COMPRA/</b> - Documentos de solicitud y contratación
        <b>02_APROBACIONES/</b> - Registros de aprobación por cada agente
        <b>03_EVIDENCIAS_EJECUCION/</b> - Entregables y minutas de seguimiento
        <b>04_COMPROBANTES_PAGO/</b> - Facturas CFDI y comprobantes de transferencia
        <b>05_ANALISIS_RIESGO/</b> - Evaluación de riesgo y estrategia de defensa
        """
        story.append(Paragraph(evidence_text, self.styles['BodyCustom']))
        
        story.append(Spacer(1, 24))
        story.append(Paragraph("DELIBERACIONES DE AGENTES", self.styles['SectionHeader']))
        
        for delib in df.deliberations[:10]:
            agent = delib.get('agent_id', 'Unknown')
            decision = delib.get('decision', 'pending')
            stage = delib.get('stage', 'N/A')
            reasoning = delib.get('reasoning', '')[:200]
            
            delib_text = f"<b>{agent}</b> - {stage}: <i>{decision.upper()}</i>"
            story.append(Paragraph(delib_text, self.styles['BodyCustom']))
            if reasoning:
                story.append(Paragraph(f"→ {reasoning}...", self.styles['BulletPoint']))
        
        story.append(Spacer(1, 36))
        footer_text = """
        <i>Este expediente fue generado automáticamente por el Sistema Revisar.IA
        de Revisar.ia para fines de defensa fiscal ante el SAT.</i>
        """
        story.append(Paragraph(footer_text, self.styles['BodyCustom']))
        
        doc.build(story)
        logger.info(f"Índice maestro PDF generado: {output_path}")
    
    def _build_chronology(self, df: DefenseFile) -> List[Dict]:
        """Construye cronología de eventos del proyecto"""
        events = []
        project = df.project_data
        
        if project.get('start_date'):
            events.append({
                "date": project.get('start_date'),
                "description": "Identificación de Necesidad de Negocio",
                "details": [
                    f"Justificación: {project.get('business_case', 'Documentado en SOW')}"
                ]
            })
        
        if project.get('created_at'):
            events.append({
                "date": project.get('created_at', '')[:10],
                "description": "Registro en Sistema de Gestión",
                "details": [
                    f"Monto estimado: ${project.get('budget', 0):,.2f} MXN"
                ]
            })
        
        for delib in df.deliberations:
            events.append({
                "date": delib.get('recorded_at', '')[:10] if delib.get('recorded_at') else 'N/A',
                "description": f"Deliberación de {delib.get('agent_id', 'Agente')}",
                "details": [
                    f"Etapa: {delib.get('stage', 'N/A')}",
                    f"Decisión: {delib.get('decision', 'pending').upper()}"
                ]
            })
        
        return events


defense_generator = DefenseFileGenerator()
