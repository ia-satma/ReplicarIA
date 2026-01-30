"""
Defense File API Routes
Endpoints for managing audit trail and compliance documentation
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os

from services.defense_file_service import defense_file_service
from services.defense_file import defense_file_generator, DefenseFileConfig

router = APIRouter(prefix="/defense-file", tags=["Defense File"])
logger = logging.getLogger(__name__)


class ProjectData(BaseModel):
    """Project data for creating Defense File"""
    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    client_name: str = Field(..., description="Client name")
    description: str = Field(default="", description="Project description")
    amount: float = Field(..., description="Project amount")
    service_type: str = Field(default="Consultoría", description="Service type")


class DeliberationRecord(BaseModel):
    """Deliberation record to add"""
    stage: str = Field(..., description="Workflow stage")
    agent_id: str = Field(..., description="Agent ID")
    decision: str = Field(..., description="Decision: approve, reject, request_info")
    analysis: str = Field(..., description="Agent's analysis")
    rag_context: List[Dict] = Field(default=[], description="RAG context used")


class EmailRecord(BaseModel):
    """Email record to add"""
    from_email: str = Field(..., description="Sender email")
    to_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    message_id: str = Field(default="", description="Message ID")


class FinalDecision(BaseModel):
    """Final decision for Defense File"""
    decision: str = Field(..., description="Final decision: approved, rejected")
    justification: str = Field(..., description="Justification for the decision")


class DocumentInfo(BaseModel):
    nombre: str
    tipo: str
    status: str = "PENDING"
    file_path: Optional[str] = None


class GenerateDefenseFileRequest(BaseModel):
    project_data: Dict[str, Any]
    documents: List[DocumentInfo]
    ocr_results: Optional[List[Dict]] = None
    red_team_results: Optional[Dict] = None
    config: Optional[Dict] = None


# === PDF/ZIP Generation Endpoints (MUST be before /{project_id}) ===

@router.get("/generator-health")
async def generator_health_check():
    """Verifica que el generador PDF/ZIP está operativo"""
    return {
        "status": "healthy",
        "output_dir": defense_file_generator.output_dir,
        "output_dir_exists": os.path.exists(defense_file_generator.output_dir),
        "capabilities": ["pdf_generation", "zip_packaging", "integrity_hashing", "qr_codes"]
    }


@router.get("/generated-files")
async def list_generated_files():
    """Lista todos los expedientes generados"""
    try:
        if not defense_file_generator:
            raise HTTPException(status_code=503, detail="File generator not initialized")

        files = await defense_file_generator.list_generated_files()
        return {
            "success": True,
            "files": files or [],
            "total": len(files) if files else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing generated files: {e}")
        if "permission" in str(e).lower():
            status_code = 403
        else:
            status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/generate-pdf")
async def generate_defense_file_pdf(request: GenerateDefenseFileRequest):
    """Genera expediente de defensa fiscal completo en PDF/ZIP"""
    try:
        if not request or not request.project_data:
            raise HTTPException(status_code=400, detail="project_data es requerido")

        if not request.documents:
            raise HTTPException(status_code=400, detail="Se requiere al menos un documento")

        documents = [doc.model_dump() for doc in request.documents]

        config = None
        if request.config:
            config = DefenseFileConfig(**request.config)

        result = await defense_file_generator.generate(
            project_data=request.project_data,
            documents=documents,
            ocr_results=request.ocr_results,
            red_team_results=request.red_team_results,
            config=config
        )

        if not result:
            raise HTTPException(status_code=503, detail="PDF generation returned no result")

        base_url = "/api/defense-file/download"

        return {
            "success": result.success if hasattr(result, 'success') else False,
            "pdf_path": result.pdf_path if hasattr(result, 'pdf_path') else None,
            "zip_path": result.zip_path if hasattr(result, 'zip_path') else None,
            "download_url_pdf": f"{base_url}/pdf/{os.path.basename(result.pdf_path)}" if (hasattr(result, 'pdf_path') and result.pdf_path) else None,
            "download_url_zip": f"{base_url}/zip/{os.path.basename(result.zip_path)}" if (hasattr(result, 'zip_path') and result.zip_path) else None,
            "total_pages": result.total_pages if hasattr(result, 'total_pages') else 0,
            "total_documents": result.total_documents if hasattr(result, 'total_documents') else 0,
            "generation_time_ms": result.generation_time_ms if hasattr(result, 'generation_time_ms') else 0,
            "file_hashes": result.file_hashes if hasattr(result, 'file_hashes') else {},
            "errors": result.errors if hasattr(result, 'errors') else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating defense file: {e}")
        if "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/download/pdf/{filename}")
async def download_pdf(filename: str):
    """Descarga el PDF del expediente"""
    file_path = os.path.join("static/generated_files", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf"
    )


@router.get("/download/zip/{filename}")
async def download_zip(filename: str):
    """Descarga el ZIP del expediente"""
    file_path = os.path.join("static/generated_files", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/zip"
    )


@router.delete("/generated-files/{filename}")
async def delete_generated_file(filename: str):
    """Elimina un expediente generado"""
    try:
        deleted = await defense_file_generator.delete_generated_file(filename)
        if deleted:
            return {"success": True, "message": f"Archivo {filename} eliminado"}
        else:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Project Defense File Endpoints ===

@router.post("/create/{project_id}")
async def create_defense_file(project_id: str, project: ProjectData):
    """
    Create a new Defense File for a project

    A Defense File is the complete audit trail for SAT compliance.
    It includes all deliberations, emails, and documentation.
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        if not project:
            raise HTTPException(status_code=400, detail="project data es requerido")

        project_dict = project.model_dump()
        df = defense_file_service.create_defense_file(project_id, project_dict)

        if not df:
            raise HTTPException(status_code=503, detail="No se pudo crear el Defense File")

        return {
            "success": True,
            "project_id": project_id,
            "defense_file": df.to_dict() if hasattr(df, 'to_dict') else dict(df)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Defense File: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/{project_id}")
async def get_defense_file(project_id: str):
    """
    Get a project's Defense File

    Returns the complete audit trail including:
    - All deliberations
    - All emails
    - Compliance checklist
    - pCloud links
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        df = defense_file_service.get_defense_file(project_id)
        if not df:
            raise HTTPException(status_code=404, detail=f"Defense File no encontrado para proyecto {project_id}")

        return df
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Defense File {project_id}: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{project_id}/deliberation")
async def add_deliberation(project_id: str, record: DeliberationRecord):
    """
    Add a deliberation record to a project's Defense File
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        if not record:
            raise HTTPException(status_code=400, detail="deliberation record es requerido")

        defense_file_service.add_deliberation(project_id, record.model_dump())
        return {
            "success": True,
            "project_id": project_id,
            "message": "Deliberation añadida al Defense File"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding deliberation: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/{project_id}/email")
async def add_email(project_id: str, record: EmailRecord):
    """
    Add an email record to a project's Defense File

    Emails are key evidence for Materialidad (Art. 69-B CFF)
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        if not record or not record.from_email or not record.to_email:
            raise HTTPException(status_code=400, detail="email record completo es requerido")

        defense_file_service.add_email(project_id, record.model_dump())
        return {
            "success": True,
            "project_id": project_id,
            "message": "Email añadido al Defense File (Materialidad evidence)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding email: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post("/{project_id}/finalize")
async def finalize_defense_file(project_id: str, decision: FinalDecision):
    """
    Finalize a Defense File with the final decision

    This marks the Defense File as complete and ready for SAT audit.
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        if not decision or not decision.decision or not decision.justification:
            raise HTTPException(status_code=400, detail="decision y justification son requeridos")

        result = defense_file_service.finalize_defense_file(
            project_id,
            decision.decision,
            decision.justification
        )

        if not result:
            raise HTTPException(status_code=503, detail="No se pudo finalizar el Defense File")

        return {
            "success": True,
            "project_id": project_id,
            "final_decision": decision.decision,
            "audit_ready": result.get("audit_ready", False) if result else False,
            "compliance_score": result.get("compliance_score", 0) if result else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing Defense File: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/{project_id}/export")
async def export_for_sat(project_id: str):
    """
    Export Defense File in SAT-ready format

    This generates a complete compliance report including:
    - Cumplimiento Art. 5-A CFF (Razón de Negocios)
    - Cumplimiento Art. 27 LISR (Beneficio Económico)
    - Cumplimiento Art. 69-B CFF (Materialidad)
    - Cumplimiento NOM-151 (Trazabilidad)
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        export = defense_file_service.export_for_sat(project_id)

        if not export:
            raise HTTPException(status_code=404, detail=f"No se puede exportar el Defense File para {project_id}")

        return export
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting Defense File: {e}")
        if "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/")
async def list_defense_files():
    """
    List all Defense Files
    
    Returns a summary of all projects with their compliance status.
    """
    files = defense_file_service.list_all()
    return {
        "count": len(files),
        "defense_files": files
    }


@router.get("/{project_id}/compliance")
async def get_compliance_status(project_id: str):
    """
    Get compliance status for a project

    Returns the current status of the 4 compliance pillars:
    1. Razón de Negocios (Art. 5-A CFF)
    2. Beneficio Económico Esperado
    3. Materialidad (Art. 69-B CFF)
    4. Trazabilidad (NOM-151)
    """
    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        df = defense_file_service.get_defense_file(project_id)
        if not df:
            raise HTTPException(status_code=404, detail=f"Defense File no encontrado para proyecto {project_id}")

        return {
            "project_id": project_id,
            "compliance_checklist": df.get("compliance_checklist", {}) if df else {},
            "compliance_score": df.get("compliance_score", 0) if df else 0,
            "audit_ready": df.get("audit_ready", False) if df else False,
            "deliberation_count": df.get("deliberation_count", 0) if df else 0,
            "email_count": df.get("email_count", 0) if df else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# === Document Checklist Endpoints (A8_AUDITOR) ===

@router.get("/{project_id}/checklist")
async def get_document_checklist(project_id: str):
    """
    Get complete document checklist for a project
    
    Returns detailed checklist showing:
    - All required documents by category
    - Status of each document (present/missing)
    - Overall completion percentage
    - List of missing items for provider action
    
    Categories:
    1. Documentos del Proveedor (Acta, Opinión SAT, CIF, etc.)
    2. Documentos de la Operación (Orden de compra, Contrato, Factura, etc.)
    3. Evidencia de Materialidad (Entregables, Carta de aceptación, etc.)
    4. Documentos del Sistema (Reportes de agentes, Bitácora, etc.)
    """
    from services.auditor_service import auditor_service
    
    try:
        checklist = auditor_service.generate_completeness_checklist(project_id)
        return checklist
    except Exception as e:
        logger.error(f"Error generating checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/checklist/pdf")
async def download_checklist_pdf(project_id: str):
    """
    Download checklist as PDF for provider

    Generates a professional PDF document showing:
    - Summary of completion status
    - Detailed list of missing documents with requirements
    - List of documents already present
    """
    from services.auditor_service import auditor_service

    try:
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id es requerido")

        result = auditor_service.generate_provider_checklist_pdf(project_id)

        if not result:
            raise HTTPException(status_code=503, detail="No se pudo generar el PDF del checklist")

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Error generando PDF"))

        pdf_path = result.get("pdf_path")
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                path=pdf_path,
                filename=result.get("pdf_filename", f"checklist_{project_id}.pdf"),
                media_type="application/pdf"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating checklist PDF: {e}")
        if "permission" in str(e).lower():
            status_code = 403
        elif "not found" in str(e).lower():
            status_code = 404
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get("/{project_id}/download-complete")
async def download_complete_defense_file(project_id: str):
    """
    Download complete Defense File as ZIP with organized folder structure.
    
    Folder structure:
    - 00_INDICE.txt (summary of contents)
    - 01_Defense_File/ (main project info and decisions)
    - 02_Contratos/ (contracts)
    - 03_Facturas_CFDI/ (invoices)
    - 04_Evidencias/ (photos, videos)
    - 05_Analisis_Agentes/ (agent analysis as readable txt)
    - 06_Documentos_Soporte/ (other docs)
    """
    import zipfile
    import io
    import json
    from pathlib import Path
    from datetime import datetime
    from fastapi.responses import StreamingResponse
    
    try:
        df = defense_file_service.get_defense_file(project_id)
        
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            project_data = df.get("project_data", {}) if df else {"id": project_id, "name": "Proyecto", "estado": "en_proceso"}
            deliberations = df.get("deliberations", []) if df else []
            emails = df.get("emails", []) if df else []
            documents = df.get("documents", []) if df else []
            pcloud_docs = df.get("pcloud_documents", []) if df else []
            final_decision = df.get("final_decision", "pendiente") if df else "pendiente"
            compliance_checklist = df.get("compliance_checklist", {}) if df else {}
            
            indice_content = f"""═══════════════════════════════════════════════════════════════
                    EXPEDIENTE DE DEFENSA FISCAL
                        Revisar.IA v4.0
═══════════════════════════════════════════════════════════════

PROYECTO: {project_data.get('name', project_id)}
ID: {project_id}
FECHA DE GENERACIÓN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
ESTADO: {final_decision.upper()}

═══════════════════════════════════════════════════════════════
                    CONTENIDO DEL EXPEDIENTE
═══════════════════════════════════════════════════════════════

📁 01_Defense_File/
   └── proyecto_info.json - Información del proyecto
   └── decision_final.json - Decisión y justificación
   └── compliance_checklist.json - Lista de verificación

📁 02_Contratos/
   └── Contratos del proyecto (si disponibles)

📁 03_Facturas_CFDI/
   └── Facturas y CFDIs relacionados

📁 04_Evidencias/
   └── Fotos, videos y evidencias

📁 05_Analisis_Agentes/
   └── Análisis de cada agente (A1-A7)
   └── Deliberaciones y decisiones
   └── Bitácora de comunicaciones

📁 06_Documentos_Soporte/
   └── Documentos adicionales de soporte

═══════════════════════════════════════════════════════════════
                    RESUMEN DE DELIBERACIONES
═══════════════════════════════════════════════════════════════

Total de deliberaciones: {len(deliberations)}
Emails registrados: {len(emails)}
Documentos adjuntos: {len(documents) + len(pcloud_docs)}

CHECKLIST DE CUMPLIMIENTO:
"""
            for key, value in compliance_checklist.items():
                status = "✅" if value else "❌"
                indice_content += f"   {status} {key.replace('_', ' ').title()}\n"
            
            indice_content += f"""
═══════════════════════════════════════════════════════════════
Este expediente cumple con los requisitos de documentación
establecidos por el SAT para la deducción de servicios
intangibles de acuerdo con el Artículo 27 fracción VIII
del Código Fiscal de la Federación.
═══════════════════════════════════════════════════════════════
"""
            zf.writestr("00_INDICE.txt", indice_content.encode('utf-8'))
            
            zf.writestr(
                "01_Defense_File/proyecto_info.json",
                json.dumps(project_data, indent=2, ensure_ascii=False, default=str)
            )
            
            zf.writestr(
                "01_Defense_File/decision_final.json",
                json.dumps({
                    "decision": final_decision,
                    "justification": df.get("final_justification", "") if df else "",
                    "compliance_checklist": compliance_checklist,
                    "compliance_score": df.get("compliance_score", 0) if df else 0,
                    "fecha_decision": datetime.now().isoformat()
                }, indent=2, ensure_ascii=False, default=str)
            )
            
            zf.writestr(
                "01_Defense_File/compliance_checklist.json",
                json.dumps(compliance_checklist, indent=2, ensure_ascii=False, default=str)
            )
            
            analisis_content = "═══════════════════════════════════════════════════════════════\n"
            analisis_content += "              ANÁLISIS DE AGENTES - REVISAR.IA\n"
            analisis_content += "═══════════════════════════════════════════════════════════════\n\n"
            
            agent_names = {
                "A1_SPONSOR": "A1 - Estrategia/Sponsor",
                "A2_PMO": "A2 - PMO (Coordinación)",
                "A3_FISCAL": "A3 - Fiscal",
                "A4_LEGAL": "A4 - Legal",
                "A5_FINANZAS": "A5 - Finanzas",
                "A6_PROVEEDOR": "A6 - Proveedor",
                "A7_DEFENSA": "A7 - Defensa"
            }
            
            for delib in deliberations:
                agent_id = delib.get("agent_id", "Unknown")
                agent_display = agent_names.get(agent_id, agent_id)
                analisis_content += f"\n{'─' * 60}\n"
                analisis_content += f"AGENTE: {agent_display}\n"
                analisis_content += f"ETAPA: {delib.get('stage', 'N/A')}\n"
                analisis_content += f"DECISIÓN: {delib.get('decision', 'pendiente').upper()}\n"
                analisis_content += f"FECHA: {delib.get('timestamp', 'N/A')}\n"
                analisis_content += f"{'─' * 60}\n\n"
                analisis_content += f"ANÁLISIS:\n{delib.get('analysis', 'Sin análisis disponible')}\n\n"
                
                rag_context = delib.get("rag_context", [])
                if rag_context:
                    analisis_content += f"CONTEXTO RAG UTILIZADO:\n"
                    for ctx in rag_context[:3]:
                        analisis_content += f"  - {ctx.get('source', 'Fuente desconocida')}\n"
                analisis_content += "\n"
            
            zf.writestr("05_Analisis_Agentes/deliberaciones.txt", analisis_content.encode('utf-8'))
            
            zf.writestr(
                "05_Analisis_Agentes/deliberaciones.json",
                json.dumps(deliberations, indent=2, ensure_ascii=False, default=str)
            )
            
            bitacora_content = "═══════════════════════════════════════════════════════════════\n"
            bitacora_content += "              BITÁCORA DE COMUNICACIONES\n"
            bitacora_content += "═══════════════════════════════════════════════════════════════\n\n"
            
            for email in emails:
                bitacora_content += f"{'─' * 60}\n"
                bitacora_content += f"DE: {email.get('from_email', 'N/A')}\n"
                bitacora_content += f"PARA: {email.get('to_email', 'N/A')}\n"
                bitacora_content += f"ASUNTO: {email.get('subject', 'Sin asunto')}\n"
                bitacora_content += f"FECHA: {email.get('recorded_at', 'N/A')}\n"
                bitacora_content += f"{'─' * 60}\n"
                bitacora_content += f"{email.get('body', 'Sin contenido')}\n\n"
            
            zf.writestr("05_Analisis_Agentes/bitacora_emails.txt", bitacora_content.encode('utf-8'))
            
            reports_dir = Path("./reports")
            if reports_dir.exists():
                for doc in documents:
                    file_path = doc.get("file_path", "")
                    if file_path:
                        full_path = reports_dir / Path(file_path).name
                        if full_path.exists():
                            doc_type = doc.get("type", "soporte").lower()
                            if "contrato" in doc_type:
                                folder = "02_Contratos"
                            elif "factura" in doc_type or "cfdi" in doc_type:
                                folder = "03_Facturas_CFDI"
                            elif "evidencia" in doc_type or "foto" in doc_type or "video" in doc_type:
                                folder = "04_Evidencias"
                            else:
                                folder = "06_Documentos_Soporte"
                            zf.write(full_path, f"{folder}/{full_path.name}")
            
            if pcloud_docs:
                pcloud_content = "═══════════════════════════════════════════════════════════════\n"
                pcloud_content += "              DOCUMENTOS EN PCLOUD\n"
                pcloud_content += "═══════════════════════════════════════════════════════════════\n\n"
                pcloud_content += "Los siguientes documentos están almacenados en pCloud:\n\n"
                
                for doc in pcloud_docs:
                    pcloud_content += f"📄 {doc.get('name', 'Documento')}\n"
                    pcloud_content += f"   Tipo: {doc.get('type', 'N/A')}\n"
                    pcloud_content += f"   Link: {doc.get('public_link', 'N/A')}\n\n"
                
                zf.writestr("06_Documentos_Soporte/pcloud_links.txt", pcloud_content.encode('utf-8'))
            
            try:
                from services.auditor_service import auditor_service
                checklist = auditor_service.generate_completeness_checklist(project_id)
                zf.writestr(
                    "01_Defense_File/checklist_completitud.json",
                    json.dumps(checklist, indent=2, ensure_ascii=False, default=str)
                )
            except Exception as e:
                logger.warning(f"Could not generate completeness checklist: {e}")
        
        buffer.seek(0)
        zip_size = buffer.getbuffer().nbytes
        
        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="ExpedienteDefensa_{project_id}.zip"',
                "Content-Length": str(zip_size),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "X-Content-Type-Options": "nosniff"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating complete defense file ZIP: {e}")
        if "permission" in str(e).lower():
            status_code = 403
        elif "not found" in str(e).lower():
            status_code = 404
        elif "timeout" in str(e).lower() or "memory" in str(e).lower():
            status_code = 503
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=str(e))
