"""
Routes for Loop Orchestrator endpoints
OCR Validation, Red Team Simulation, Testing Loops
"""

from fastapi import APIRouter, HTTPException, Path, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from services.ocr_validation_loop import ocr_validation_loop
from services.red_team_loop import red_team_loop
from services.loop_orchestrator import loop_orchestrator

router = APIRouter(prefix="/api/loops", tags=["Loops"])


class DocumentValidationRequest(BaseModel):
    document_path: str
    document_type: str
    expected_data: Optional[Dict[str, Any]] = None


class BatchDocumentRequest(BaseModel):
    documents: List[Dict[str, Any]]


class RedTeamRequest(BaseModel):
    project_data: Dict[str, Any]


class LoopTaskRequest(BaseModel):
    task_name: str
    context: Optional[Dict[str, Any]] = None
    max_iterations: Optional[int] = 10
    timeout_seconds: Optional[float] = 300


@router.post("/projects/{project_id}/documents/{document_id}/validate-ocr")
async def validate_document_ocr(
    project_id: str = Path(..., description="Project ID"),
    document_id: str = Path(..., description="Document ID"),
    request: DocumentValidationRequest = Body(...)
):
    """
    Valida un documento específico con OCR Loop iterativo
    """
    try:
        result = await ocr_validation_loop.validate_document(
            document_path=request.document_path,
            document_type=request.document_type,
            expected_data=request.expected_data
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "document_id": document_id,
            "data": {
                "status": result.status,
                "confidence": result.confidence,
                "iterations": result.iterations,
                "extracted_data": result.extracted_data,
                "findings": result.findings,
                "contradictions": result.contradictions,
                "requires_human_review": result.requires_human_review
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/validate-all-documents")
async def validate_all_documents(
    project_id: str = Path(..., description="Project ID"),
    request: BatchDocumentRequest = Body(...)
):
    """
    Valida TODOS los documentos de un proyecto con OCR Loop
    """
    try:
        results = await ocr_validation_loop.validate_project_documents(
            project_id=project_id,
            documents=request.documents
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "total_documents": results["total_documents"],
            "validated": results["validated"],
            "requires_review": results["requires_review"],
            "failed": results["failed"],
            "success_rate": results["success_rate"],
            "results": results["document_results"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/red-team-simulation")
async def run_red_team_simulation(
    project_id: str = Path(..., description="Project ID"),
    request: RedTeamRequest = Body(...)
):
    """
    Ejecuta simulación Red Team sobre un proyecto
    Simula ataques del SAT para encontrar vulnerabilidades
    """
    try:
        report = await red_team_loop.simulate_attack(
            project_id=project_id,
            project_data=request.project_data
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "data": {
                "fecha": report.fecha,
                "total_iteraciones": report.total_iteraciones,
                "vectores_testeados": report.vectores_testeados,
                "vulnerabilidades_encontradas": report.vulnerabilidades_encontradas,
                "nivel_riesgo": report.nivel_riesgo,
                "bulletproof": report.bulletproof,
                "conclusion": report.conclusion,
                "vulnerabilidades": [
                    {
                        "id": v.id,
                        "severity": v.severity,
                        "description": v.description,
                        "vector_id": v.vector_id,
                        "vector_name": v.vector_name,
                        "articulo_aplicable": v.articulo_aplicable,
                        "recommendation": v.recommendation
                    }
                    for v in report.vulnerabilidades
                ],
                "recomendaciones": report.recomendaciones
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attack-vectors")
async def get_attack_vectors():
    """
    Lista los vectores de ataque disponibles para Red Team
    """
    from services.red_team_loop import ATTACK_VECTORS
    
    return {
        "success": True,
        "total": len(ATTACK_VECTORS),
        "vectors": [
            {
                "id": v["id"],
                "name": v["name"],
                "prompts": v["prompts"]
            }
            for v in ATTACK_VECTORS
        ]
    }


@router.get("/document-types")
async def get_document_types():
    """
    Lista los tipos de documento soportados para OCR Validation
    """
    from services.ocr_validation_loop import REQUIRED_KEYWORDS
    
    return {
        "success": True,
        "total": len(REQUIRED_KEYWORDS),
        "types": [
            {
                "type": doc_type,
                "required_keywords": keywords
            }
            for doc_type, keywords in REQUIRED_KEYWORDS.items()
        ]
    }


@router.get("/status")
async def get_loops_status():
    """
    Estado general de los servicios de Loop
    """
    return {
        "success": True,
        "services": {
            "ocr_validation": {
                "available": True,
                "max_iterations": ocr_validation_loop.orchestrator.max_iterations,
                "timeout_seconds": ocr_validation_loop.orchestrator.timeout_seconds,
                "strategies": ocr_validation_loop.strategies
            },
            "red_team": {
                "available": True,
                "max_iterations": red_team_loop.orchestrator.max_iterations,
                "timeout_seconds": red_team_loop.orchestrator.timeout_seconds,
                "attack_vectors": len(red_team_loop.attack_vectors)
            },
            "generic_loop": {
                "available": True,
                "max_iterations": loop_orchestrator.max_iterations,
                "timeout_seconds": loop_orchestrator.timeout_seconds
            }
        }
    }
