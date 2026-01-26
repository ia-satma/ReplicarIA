"""
API endpoints para plantillas RAG multi-tenant.
Las plantillas sirven como guía para que cada empresa complete con su información.
Carga dinámica desde archivos _metadata.json en cada carpeta de agente.
Incluye endpoints para templates .docx en backend/templates/
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.template_engine import (
    generate_document,
    validate_data as validate_template_data,
    get_template_placeholders
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


class GenerateTemplateRequest(BaseModel):
    data: Dict[str, str]
    validate_fields: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "EMPRESA_NOMBRE": "Mi Empresa S.A. de C.V.",
                    "EMPRESA_RFC": "ABC123456789",
                    "FECHA_ACTUAL": "19/01/2026",
                    "PROYECTO_NOMBRE": "Consultoría Estratégica",
                    "MONTO_CREDITO": "500,000"
                },
                "validate_fields": True
            }
        }

TEMPLATES_DIR = Path(__file__).parent.parent / "rag" / "templates"
DOCX_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

AGENT_DISPLAY_NAMES = {
    "A1_ESTRATEGIA": "Estrategia",
    "A2_PMO": "PMO",
    "A3_FISCAL": "Fiscal",
    "A4_LEGAL": "Legal",
    "A5_FINANZAS": "Finanzas",
    "A6_PROVEEDOR": "Proveedor",
    "A7_DEFENSA": "Defensa",
    "KNOWLEDGE_BASE": "Knowledge Base"
}


class DocumentoInfo(BaseModel):
    id: str
    titulo: str
    tipo: str
    uso: str
    personalizable: bool
    campos_clave: List[str]


class PlantillaInfo(BaseModel):
    id: str
    nombre: str
    descripcion: str
    agente: str
    archivo: str
    version: str
    tipo: Optional[str] = None
    personalizable: Optional[bool] = True


class ContextoRequerido(BaseModel):
    obligatorio: List[str]
    deseable: List[str]


class MetadataAgente(BaseModel):
    agente_id: str
    nombre: str
    descripcion: str
    documentos: List[DocumentoInfo]
    contexto_requerido: ContextoRequerido


class PlantillaCatalogo(BaseModel):
    agente: str
    agente_nombre: str
    descripcion: str
    plantillas: List[PlantillaInfo]
    contexto_requerido: Optional[ContextoRequerido] = None


def cargar_metadata_agente(agente_dir: Path) -> Optional[Dict[str, Any]]:
    """Carga el _metadata.json de una carpeta de agente"""
    metadata_path = agente_dir / "_metadata.json"
    if not metadata_path.exists():
        return None
    
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data.get("agente_id"):
                logger.warning(f"Metadata sin agente_id en {metadata_path}")
            if not data.get("documentos"):
                logger.warning(f"Metadata sin documentos en {metadata_path}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error JSON en {metadata_path}: {e}")
        return None
    except IOError as e:
        logger.error(f"Error IO en {metadata_path}: {e}")
        return None


def encontrar_archivo_plantilla(agente_dir: Path, doc_id: str) -> Optional[str]:
    """
    Encuentra el archivo .md correspondiente a un documento por su ID.
    Usa matching determinístico basado en el ID del documento.
    """
    archivo_exacto = agente_dir / f"{doc_id}.md"
    if archivo_exacto.exists():
        return archivo_exacto.name
    
    for archivo in agente_dir.glob("*.md"):
        if archivo.name.startswith(doc_id):
            return archivo.name
    
    prefix = doc_id.split("_")[0] if "_" in doc_id else doc_id
    for archivo in agente_dir.glob(f"{prefix}_*.md"):
        return archivo.name
    
    logger.warning(f"No se encontró archivo para doc_id={doc_id} en {agente_dir}")
    return None


def cargar_catalogo_completo() -> Dict[str, Dict[str, Any]]:
    """Carga todos los catálogos de plantillas desde los _metadata.json"""
    catalogo = {}
    
    if not TEMPLATES_DIR.exists():
        logger.warning(f"Directorio de templates no existe: {TEMPLATES_DIR}")
        return catalogo
    
    for agente_dir in sorted(TEMPLATES_DIR.iterdir()):
        if not agente_dir.is_dir():
            continue
        
        metadata = cargar_metadata_agente(agente_dir)
        if not metadata:
            continue
        
        agente_id = metadata.get("agente_id", agente_dir.name)
        
        plantillas = []
        for doc in metadata.get("documentos", []):
            doc_id = doc.get("id")
            if not doc_id:
                logger.warning(f"Documento sin ID en {agente_dir}")
                continue
            
            archivo = encontrar_archivo_plantilla(agente_dir, doc_id)
            if not archivo:
                archivo = f"{doc_id}.md"
            
            plantillas.append({
                "id": doc_id,
                "nombre": doc.get("titulo", doc_id),
                "descripcion": doc.get("uso", ""),
                "archivo": archivo,
                "version": "1.0",
                "tipo": doc.get("tipo", "plantilla"),
                "personalizable": doc.get("personalizable", True),
                "campos_clave": doc.get("campos_clave", [])
            })
        
        catalogo[agente_id] = {
            "agente_nombre": metadata.get("nombre", agente_id),
            "descripcion": metadata.get("descripcion", ""),
            "plantillas": plantillas,
            "contexto_requerido": metadata.get("contexto_requerido", {"obligatorio": [], "deseable": []})
        }
    
    return catalogo


PLANTILLAS_CATALOGO = cargar_catalogo_completo()


@router.get("/", response_model=List[PlantillaCatalogo])
async def listar_plantillas():
    """Lista todas las plantillas disponibles organizadas por agente"""
    global PLANTILLAS_CATALOGO
    PLANTILLAS_CATALOGO = cargar_catalogo_completo()
    
    resultado = []
    for agente_id, data in PLANTILLAS_CATALOGO.items():
        plantillas = []
        for p in data["plantillas"]:
            plantillas.append(PlantillaInfo(
                id=p["id"],
                nombre=p["nombre"],
                descripcion=p["descripcion"],
                agente=agente_id,
                archivo=p["archivo"],
                version=p["version"],
                tipo=p.get("tipo"),
                personalizable=p.get("personalizable", True)
            ))
        
        contexto = None
        if data.get("contexto_requerido"):
            contexto = ContextoRequerido(**data["contexto_requerido"])
        
        resultado.append(PlantillaCatalogo(
            agente=agente_id,
            agente_nombre=data["agente_nombre"],
            descripcion=data.get("descripcion", ""),
            plantillas=plantillas,
            contexto_requerido=contexto
        ))
    
    return resultado


@router.get("/metadata")
async def obtener_metadata_completo():
    """Obtiene el metadata completo de todos los agentes con contextos requeridos"""
    global PLANTILLAS_CATALOGO
    PLANTILLAS_CATALOGO = cargar_catalogo_completo()
    
    return {
        "agentes": len(PLANTILLAS_CATALOGO),
        "total_plantillas": sum(len(d["plantillas"]) for d in PLANTILLAS_CATALOGO.values()),
        "catalogo": PLANTILLAS_CATALOGO
    }


@router.get("/docx")
async def list_all_docx_templates():
    """List all .docx templates grouped by agent"""
    agents_data = []
    total = 0
    
    for agent_info in get_docx_agents():
        agent_templates = get_docx_templates_by_agent(agent_info["agent_id"])
        if agent_templates:
            agents_data.append(agent_templates)
            total += agent_templates["template_count"]
    
    return {
        "total_templates": total,
        "agents": agents_data
    }


@router.get("/docx/{agent_id}")
async def list_docx_agent_templates(agent_id: str):
    """List all .docx templates for a specific agent"""
    result = get_docx_templates_by_agent(agent_id)
    if result is None:
        raise HTTPException(404, f"Agent '{agent_id}' not found or has no templates")
    return result


@router.get("/docx/{agent_id}/{template_id}/info")
async def get_docx_template_info(agent_id: str, template_id: str):
    """Get metadata for a specific .docx template"""
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    template_file = agent_dir / f"{template_id}.docx"
    
    if not template_file.exists():
        raise HTTPException(404, f"Template '{template_id}' not found in agent '{agent_id}'")
    
    file_size = template_file.stat().st_size
    modified_time = template_file.stat().st_mtime
    
    info = {
        "agent_id": agent_id,
        "agent_name": AGENT_DISPLAY_NAMES.get(agent_id, agent_id),
        "template_id": template_id,
        "filename": template_file.name,
        "file_size": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "modified_timestamp": modified_time,
        "download_url": f"/api/templates/docx/{agent_id}/{template_id}/download"
    }
    
    manifest = load_docx_manifest(agent_dir)
    if manifest:
        for t in manifest.get("templates", []):
            if t.get("filename") == template_file.name:
                info["title"] = t.get("title", "")
                info["section_count"] = t.get("section_count", 0)
                info["placeholders"] = t.get("placeholders", [])
                break
    
    return info


@router.get("/docx/{agent_id}/{template_id}/download")
async def download_docx_template(agent_id: str, template_id: str):
    """Download a .docx template file"""
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    template_file = agent_dir / f"{template_id}.docx"
    
    if not template_file.exists():
        raise HTTPException(404, f"Template '{template_id}' not found in agent '{agent_id}'")
    
    return FileResponse(
        path=str(template_file),
        filename=template_file.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/docx/{agent_id}/{template_id}/placeholders")
async def get_template_placeholders_endpoint(agent_id: str, template_id: str):
    """Get list of placeholders for a template"""
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    template_file = agent_dir / f"{template_id}.docx"
    
    if not template_file.exists():
        raise HTTPException(404, f"Template '{template_id}' not found in agent '{agent_id}'")
    
    placeholders = get_template_placeholders(agent_id, template_id)
    
    return {
        "agent_id": agent_id,
        "template_id": template_id,
        "placeholders": sorted(placeholders),
        "count": len(placeholders)
    }


@router.post("/docx/{agent_id}/{template_id}/generate")
async def generate_filled_template(
    agent_id: str, 
    template_id: str, 
    request: GenerateTemplateRequest
):
    """
    Generate a filled document by replacing placeholders with provided data.
    
    The request body should contain a 'data' dict mapping placeholder names to values.
    Example: {"data": {"EMPRESA_NOMBRE": "Mi Empresa", "RFC": "ABC123456789"}}
    """
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    template_file = agent_dir / f"{template_id}.docx"
    
    if not agent_dir.exists():
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    
    if not template_file.exists():
        raise HTTPException(404, f"Template '{template_id}' not found in agent '{agent_id}'")
    
    try:
        output_path, validation = generate_document(
            agent_id=agent_id,
            template_id=template_id,
            data=request.data,
            validate=request.validate_fields
        )
        
        if request.validate_fields and not validation.get("valid", True):
            return {
                "success": False,
                "error": "Missing required fields",
                "validation": validation
            }
        
        output_filename = f"{template_id}_{agent_id}_filled.docx"
        
        return FileResponse(
            path=str(output_path),
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "X-Validation-Status": "valid" if validation.get("valid", True) else "incomplete",
                "X-Missing-Fields": ",".join(validation.get("missing", []))
            }
        )
        
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(500, f"Error generating document: {str(e)}")


@router.post("/docx/{agent_id}/{template_id}/validate")
async def validate_template_data_endpoint(
    agent_id: str,
    template_id: str,
    request: GenerateTemplateRequest
):
    """
    Validate provided data against template placeholders without generating document.
    Returns which fields are missing, extra, and provided.
    """
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    template_file = agent_dir / f"{template_id}.docx"
    
    if not template_file.exists():
        raise HTTPException(404, f"Template '{template_id}' not found in agent '{agent_id}'")
    
    validation = validate_template_data(agent_id, template_id, request.data)
    
    return {
        "agent_id": agent_id,
        "template_id": template_id,
        "validation": validation
    }


@router.get("/{agente_id}")
async def listar_plantillas_agente(agente_id: str):
    """Lista plantillas disponibles para un agente específico"""
    global PLANTILLAS_CATALOGO
    PLANTILLAS_CATALOGO = cargar_catalogo_completo()
    
    if agente_id not in PLANTILLAS_CATALOGO:
        raise HTTPException(404, f"No hay plantillas para el agente {agente_id}")
    
    data = PLANTILLAS_CATALOGO[agente_id]
    plantillas = []
    for p in data["plantillas"]:
        plantillas.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "descripcion": p["descripcion"],
            "agente": agente_id,
            "archivo": p["archivo"],
            "version": p["version"],
            "tipo": p.get("tipo", "plantilla"),
            "personalizable": p.get("personalizable", True),
            "campos_clave": p.get("campos_clave", []),
            "url_descarga": f"/api/templates/{agente_id}/{p['id']}/download"
        })
    
    return {
        "agente": agente_id,
        "agente_nombre": data["agente_nombre"],
        "descripcion": data.get("descripcion", ""),
        "plantillas": plantillas,
        "contexto_requerido": data.get("contexto_requerido", {"obligatorio": [], "deseable": []})
    }


@router.get("/{agente_id}/{plantilla_id:path}")
async def obtener_plantilla(agente_id: str, plantilla_id: str):
    """Obtiene el contenido de una plantilla específica"""
    if plantilla_id.endswith("/download"):
        plantilla_id = plantilla_id[:-9]
        return await descargar_plantilla(agente_id, plantilla_id)
    
    global PLANTILLAS_CATALOGO
    PLANTILLAS_CATALOGO = cargar_catalogo_completo()
    
    if agente_id not in PLANTILLAS_CATALOGO:
        raise HTTPException(404, f"Agente {agente_id} no encontrado")
    
    plantilla = next(
        (p for p in PLANTILLAS_CATALOGO[agente_id]["plantillas"] if p["id"] == plantilla_id),
        None
    )
    
    if not plantilla:
        raise HTTPException(404, f"Plantilla {plantilla_id} no encontrada en agente {agente_id}")
    
    archivo_path = TEMPLATES_DIR / agente_id / plantilla["archivo"]
    
    if not archivo_path.exists():
        logger.error(f"Archivo no existe: {archivo_path}")
        raise HTTPException(404, f"Archivo de plantilla no encontrado: {plantilla['archivo']}")
    
    with open(archivo_path, "r", encoding="utf-8") as f:
        contenido = f.read()
    
    return {
        "id": plantilla["id"],
        "nombre": plantilla["nombre"],
        "descripcion": plantilla["descripcion"],
        "agente": agente_id,
        "version": plantilla["version"],
        "tipo": plantilla.get("tipo", "plantilla"),
        "personalizable": plantilla.get("personalizable", True),
        "campos_clave": plantilla.get("campos_clave", []),
        "contenido": contenido
    }


@router.get("/{agente_id}/{plantilla_id}/download")
async def descargar_plantilla(agente_id: str, plantilla_id: str):
    """Descarga una plantilla como archivo Markdown"""
    global PLANTILLAS_CATALOGO
    PLANTILLAS_CATALOGO = cargar_catalogo_completo()
    
    if agente_id not in PLANTILLAS_CATALOGO:
        raise HTTPException(404, f"Agente {agente_id} no encontrado")
    
    plantilla = next(
        (p for p in PLANTILLAS_CATALOGO[agente_id]["plantillas"] if p["id"] == plantilla_id),
        None
    )
    
    if not plantilla:
        raise HTTPException(404, f"Plantilla {plantilla_id} no encontrada en agente {agente_id}")
    
    archivo_path = TEMPLATES_DIR / agente_id / plantilla["archivo"]
    
    if not archivo_path.exists():
        logger.error(f"Archivo no existe para descarga: {archivo_path}")
        raise HTTPException(404, f"Archivo no encontrado")
    
    nombre_descarga = f"{plantilla['nombre'].replace(' ', '_').replace('/', '-')}.md"
    
    return FileResponse(
        path=str(archivo_path),
        filename=nombre_descarga,
        media_type="text/markdown"
    )


def load_docx_manifest(agent_dir: Path) -> Optional[Dict[str, Any]]:
    """Load manifest.json from a docx template agent folder"""
    manifest_path = agent_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading manifest {manifest_path}: {e}")
        return None


def get_docx_agents() -> List[Dict[str, Any]]:
    """Get list of all agents with docx templates"""
    agents = []
    if not DOCX_TEMPLATES_DIR.exists():
        return agents
    
    for agent_dir in sorted(DOCX_TEMPLATES_DIR.iterdir()):
        if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
            manifest = load_docx_manifest(agent_dir)
            template_count = len(list(agent_dir.glob("*.docx")))
            
            agents.append({
                "agent_id": agent_dir.name,
                "agent_name": AGENT_DISPLAY_NAMES.get(agent_dir.name, agent_dir.name),
                "template_count": template_count,
                "has_manifest": manifest is not None
            })
    return agents


def get_docx_templates_by_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get all docx templates for a specific agent"""
    agent_dir = DOCX_TEMPLATES_DIR / agent_id
    if not agent_dir.exists() or not agent_dir.is_dir():
        return None
    
    manifest = load_docx_manifest(agent_dir)
    templates = []
    
    for template_file in sorted(agent_dir.glob("*.docx")):
        template_id = template_file.stem
        file_size = template_file.stat().st_size
        
        template_info = {
            "template_id": template_id,
            "filename": template_file.name,
            "file_size": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "download_url": f"/api/templates/docx/{agent_id}/{template_id}/download"
        }
        
        if manifest:
            for t in manifest.get("templates", []):
                if t.get("filename") == template_file.name:
                    template_info["title"] = t.get("title", "")
                    template_info["section_count"] = t.get("section_count", 0)
                    template_info["placeholders"] = t.get("placeholders", [])
                    break
        
        templates.append(template_info)
    
    return {
        "agent_id": agent_id,
        "agent_name": AGENT_DISPLAY_NAMES.get(agent_id, agent_id),
        "template_count": len(templates),
        "templates": templates
    }
