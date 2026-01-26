from fastapi import APIRouter
from jobs.export_sheets_to_sql import EXPORTER
from services.agent_service import AGENT_CONFIGURATIONS

router = APIRouter(prefix="/sql", tags=["SQL Tools"])

@router.get('/export/{agent_id}')
def export_sql(agent_id: str):
    """Exporta Google Sheets del agente a CSV para SQL"""
    
    agent_config = AGENT_CONFIGURATIONS.get(agent_id)
    if not agent_config:
        return {"ok": False, "error": "Agent not found"}
    
    folder_id = agent_config.get('drive_folder_id')
    if not folder_id:
        return {"ok": False, "error": "folder_id not configured"}
    
    try:
        res = EXPORTER.run(agent_id, folder_id)
        return {"ok": True, **res}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get('/export-all')
def export_all_agents():
    """Exporta Sheets de todos los agentes"""
    
    results = {}
    total = 0
    
    for agent_id, config in AGENT_CONFIGURATIONS.items():
        if agent_id == "PROVEEDOR_IA":
            continue
        
        folder_id = config.get('drive_folder_id')
        if folder_id:
            try:
                res = EXPORTER.run(agent_id, folder_id)
                results[agent_id] = res
                total += res.get('exported_csv', 0)
            except Exception as e:
                results[agent_id] = {"error": str(e)}
    
    return {
        "ok": True,
        "total_exported": total,
        "by_agent": results
    }
