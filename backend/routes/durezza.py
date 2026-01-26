"""
Revisar.IA - API Routes
REST endpoints for the fiscal audit system
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from services.durezza_database import durezza_db
from services.durezza_seeds import get_checklist_seeds, get_agent_config_seeds
from models.durezza_enums import (
    TipologiaProyecto, FaseProyecto, EstadoGlobal, TipoAgente, AccionAuditLog
)

router = APIRouter(prefix="/api/durezza", tags=["durezza"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "durezza-4.0",
        "demo_mode": durezza_db.demo_mode,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/init")
async def initialize_durezza():
    try:
        try:
            await durezza_db.create_indexes()
        except Exception as idx_err:
            pass
        
        checklist_seeds = get_checklist_seeds()
        for seed in checklist_seeds:
            await durezza_db.create_checklist_template(seed)
        
        agent_seeds = get_agent_config_seeds()
        for seed in agent_seeds:
            await durezza_db.create_agent_config(seed)
        
        return {
            "status": "initialized",
            "demo_mode": durezza_db.demo_mode,
            "checklist_templates_created": len(checklist_seeds),
            "agent_configs_created": len(agent_seeds)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suppliers")
async def create_supplier(supplier_data: dict):
    try:
        supplier = await durezza_db.create_supplier(supplier_data)
        await durezza_db.create_audit_log({
            "accion": AccionAuditLog.PROYECTO_CREADO.value,
            "entidad_tipo": "Supplier",
            "entidad_id": supplier["id"],
            "descripcion": f"Proveedor creado: {supplier.get('nombre_razon_social', 'N/A')}"
        })
        return supplier
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/suppliers")
async def get_suppliers(activo: Optional[bool] = None):
    return await durezza_db.get_suppliers(activo=activo)


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str):
    supplier = await durezza_db.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.get("/suppliers/rfc/{rfc}")
async def get_supplier_by_rfc(rfc: str):
    supplier = await durezza_db.get_supplier_by_rfc(rfc)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, update_data: dict):
    success = await durezza_db.update_supplier(supplier_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"status": "updated"}


@router.post("/projects")
async def create_project(project_data: dict):
    try:
        project = await durezza_db.create_project(project_data)
        
        defense_file = await durezza_db.create_defense_file({
            "proyecto_id": project["id"]
        })
        await durezza_db.update_project(project["id"], {"defense_file_id": defense_file["id"]})
        
        for fase in FaseProyecto:
            await durezza_db.create_project_phase({
                "proyecto_id": project["id"],
                "fase": fase.value
            })
        
        await durezza_db.create_audit_log({
            "proyecto_id": project["id"],
            "accion": AccionAuditLog.PROYECTO_CREADO.value,
            "entidad_tipo": "Project",
            "entidad_id": project["id"],
            "descripcion": f"Proyecto creado: {project.get('nombre', 'N/A')}",
            "datos_despues": project
        })
        
        return project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects")
async def get_projects(
    estado: Optional[str] = None,
    fase: Optional[str] = None,
    tipologia: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    return await durezza_db.get_projects(estado=estado, fase=fase, tipologia=tipologia, limit=limit)


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await durezza_db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/full")
async def get_project_full(project_id: str):
    project = await durezza_db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    phases = await durezza_db.get_project_phases(project_id)
    deliberations = await durezza_db.get_deliberations(project_id)
    defense_file = await durezza_db.get_defense_file(project_id)
    documents = await durezza_db.get_documents(project_id)
    
    supplier = None
    if project.get("proveedor_id"):
        supplier = await durezza_db.get_supplier(project["proveedor_id"])
    
    return {
        "project": project,
        "supplier": supplier,
        "phases": phases,
        "deliberations": deliberations,
        "defense_file": defense_file,
        "documents": documents
    }


@router.put("/projects/{project_id}")
async def update_project(project_id: str, update_data: dict):
    old_project = await durezza_db.get_project(project_id)
    if not old_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    success = await durezza_db.update_project(project_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Update failed")
    
    await durezza_db.create_audit_log({
        "proyecto_id": project_id,
        "accion": AccionAuditLog.PROYECTO_ACTUALIZADO.value,
        "entidad_tipo": "Project",
        "entidad_id": project_id,
        "descripcion": "Proyecto actualizado",
        "datos_antes": old_project,
        "datos_despues": update_data
    })
    
    return {"status": "updated"}


@router.get("/projects/{project_id}/phases")
async def get_project_phases(project_id: str):
    return await durezza_db.get_project_phases(project_id)


@router.get("/projects/{project_id}/phases/{fase}")
async def get_project_phase(project_id: str, fase: str):
    phase = await durezza_db.get_project_phase(project_id, fase)
    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    return phase


@router.put("/projects/{project_id}/phases/{phase_id}")
async def update_project_phase(project_id: str, phase_id: str, update_data: dict):
    success = await durezza_db.update_project_phase(phase_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Phase not found")
    return {"status": "updated"}


@router.post("/projects/{project_id}/deliberations")
async def create_deliberation(project_id: str, deliberation_data: dict):
    try:
        deliberation_data["proyecto_id"] = project_id
        
        existing = await durezza_db.get_latest_deliberation(
            project_id,
            deliberation_data.get("agente"),
            deliberation_data.get("fase")
        )
        if existing:
            deliberation_data["version"] = existing.get("version", 0) + 1
        
        deliberation = await durezza_db.create_deliberation(deliberation_data)
        
        await durezza_db.create_audit_log({
            "proyecto_id": project_id,
            "accion": AccionAuditLog.AGENTE_DELIBERACION.value,
            "entidad_tipo": "AgentDeliberation",
            "entidad_id": deliberation["id"],
            "descripcion": f"Deliberación de {deliberation.get('agente', 'N/A')} en fase {deliberation.get('fase', 'N/A')}"
        })
        
        return deliberation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/deliberations")
async def get_deliberations(project_id: str, fase: Optional[str] = None):
    return await durezza_db.get_deliberations(project_id, fase=fase)


@router.get("/projects/{project_id}/defense-file")
async def get_defense_file(project_id: str):
    defense_file = await durezza_db.get_defense_file(project_id)
    if not defense_file:
        raise HTTPException(status_code=404, detail="Defense file not found")
    return defense_file


@router.put("/projects/{project_id}/defense-file/{defense_file_id}")
async def update_defense_file(project_id: str, defense_file_id: str, update_data: dict):
    success = await durezza_db.update_defense_file(defense_file_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Defense file not found")
    return {"status": "updated"}


@router.post("/projects/{project_id}/documents")
async def create_document(project_id: str, document_data: dict):
    try:
        document_data["proyecto_id"] = project_id
        document = await durezza_db.create_document(document_data)
        
        await durezza_db.create_audit_log({
            "proyecto_id": project_id,
            "accion": AccionAuditLog.DOCUMENTO_CARGADO.value,
            "entidad_tipo": "Document",
            "entidad_id": document["id"],
            "descripcion": f"Documento cargado: {document.get('nombre', 'N/A')}"
        })
        
        return document
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/documents")
async def get_documents(project_id: str, tipo: Optional[str] = None):
    return await durezza_db.get_documents(project_id, tipo=tipo)


@router.get("/checklist-templates")
async def get_checklist_templates(tipologia: Optional[str] = None):
    return await durezza_db.get_checklist_templates(tipologia=tipologia)


@router.get("/checklist-templates/{tipologia}/{fase}")
async def get_checklist_template(tipologia: str, fase: str):
    template = await durezza_db.get_checklist_template(tipologia, fase)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/agent-configs")
async def get_agent_configs():
    return await durezza_db.get_agent_configs()


@router.get("/agent-configs/{agente}")
async def get_agent_config(agente: str):
    config = await durezza_db.get_agent_config(agente)
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    return config


@router.get("/audit-logs")
async def get_audit_logs(
    proyecto_id: Optional[str] = None,
    accion: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    return await durezza_db.get_audit_logs(proyecto_id=proyecto_id, accion=accion, limit=limit)


@router.get("/stats")
async def get_durezza_stats():
    projects = await durezza_db.get_projects(limit=1000)
    suppliers = await durezza_db.get_suppliers()
    
    by_estado = {}
    by_fase = {}
    by_tipologia = {}
    total_monto = 0.0
    
    for p in projects:
        estado = p.get("estado_global", "PENDIENTE")
        by_estado[estado] = by_estado.get(estado, 0) + 1
        
        fase = p.get("fase_actual", "F0")
        by_fase[fase] = by_fase.get(fase, 0) + 1
        
        tipologia = p.get("tipologia", "OTROS")
        by_tipologia[tipologia] = by_tipologia.get(tipologia, 0) + 1
        
        total_monto += p.get("monto", 0)
    
    return {
        "total_projects": len(projects),
        "total_suppliers": len(suppliers),
        "total_monto": total_monto,
        "by_estado": by_estado,
        "by_fase": by_fase,
        "by_tipologia": by_tipologia
    }


@router.get("/estadisticas")
async def get_estadisticas_dashboard():
    """
    Endpoint para obtener estadísticas reales del dashboard.
    Cuenta plantillas, agentes, proyectos y proveedores desde fuentes reales.
    """
    import os
    from pathlib import Path
    
    backend_root = Path(__file__).parent.parent
    templates_path = backend_root / "templates"
    
    agentes_list = []
    plantillas_por_agente = {}
    total_plantillas = 0
    docs_universales = 0
    
    if templates_path.exists():
        for dir_name in sorted(os.listdir(templates_path)):
            dir_path = templates_path / dir_name
            if dir_path.is_dir():
                agentes_list.append(dir_name)
                docx_files = list(dir_path.glob("*.docx"))
                count = len(docx_files)
                plantillas_por_agente[dir_name] = count
                total_plantillas += count
                if dir_name == "KNOWLEDGE_BASE":
                    docs_universales = count
    
    projects = await durezza_db.get_projects(limit=1000)
    suppliers = await durezza_db.get_suppliers()
    
    proyectos_activos = [p for p in projects if p.get("estado_global") in ["EN_PROGRESO", "EN_REVISION", "PENDIENTE"]]
    
    fase_actual = None
    fases_completadas = []
    proyecto_activo = None
    
    if proyectos_activos:
        proyecto_activo = proyectos_activos[0]
        fase_actual = proyecto_activo.get("fase_actual", "F0")
        fases_list = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
        if fase_actual in fases_list:
            idx = fases_list.index(fase_actual)
            fases_completadas = fases_list[:idx]
    
    proveedores_en_riesgo = 0
    for s in suppliers:
        riesgo = s.get("riesgo", {})
        if isinstance(riesgo, dict):
            nivel = riesgo.get("nivel_riesgo", "")
            if nivel in ["ALTO", "CRITICO"]:
                proveedores_en_riesgo += 1
        elif s.get("alerta_efos"):
            proveedores_en_riesgo += 1
    
    candados_fases = ["F2", "F6", "F8"]
    puntos_control_configurados = len(candados_fases)
    puntos_aprobados = 0
    puntos_pendientes = puntos_control_configurados
    
    if proyecto_activo and fase_actual:
        fases_list = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"]
        idx_actual = fases_list.index(fase_actual) if fase_actual in fases_list else 0
        for candado in candados_fases:
            idx_candado = fases_list.index(candado) if candado in fases_list else 10
            if idx_candado < idx_actual:
                puntos_aprobados += 1
                puntos_pendientes -= 1
    
    score_riesgo = None
    if proyecto_activo:
        score_riesgo = proyecto_activo.get("score_riesgo", {
            "razon_negocios": 0,
            "beneficio_economico": 0,
            "materialidad": 0,
            "trazabilidad": 0,
            "total": 0
        })
    
    hay_datos = len(projects) > 0
    
    return {
        "proyectos": {
            "total": len(projects),
            "activos": len(proyectos_activos),
            "fase_actual": fase_actual,
            "fases_completadas": fases_completadas
        },
        "agentes": {
            "total": len(agentes_list),
            "activos": len([a for a in agentes_list if a != "KNOWLEDGE_BASE"]),
            "lista": agentes_list
        },
        "plantillas_rag": {
            "total": total_plantillas,
            "por_agente": plantillas_por_agente,
            "docs_universales": docs_universales
        },
        "proveedores": {
            "total": len(suppliers),
            "en_riesgo": proveedores_en_riesgo
        },
        "puntos_control": {
            "configurados": puntos_control_configurados,
            "aprobados": puntos_aprobados,
            "pendientes": puntos_pendientes
        },
        "score_riesgo": score_riesgo,
        "hay_datos": hay_datos,
        "etapas_proceso": 10
    }
