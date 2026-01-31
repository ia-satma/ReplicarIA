from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pcloud", tags=["pCloud"])

from services.pcloud_service import pcloud_service

@router.get("/test")
async def test_pcloud_connection():
    """Test pCloud connection with current credentials"""
    result = pcloud_service.login()
    return result

@router.post("/initialize")
async def initialize_pcloud_structure():
    """Initialize REVISAR.ia folder structure - creates all required subfolders"""
    result = pcloud_service.initialize_folder_structure()
    return result

@router.get("/folders")
async def list_agent_folders():
    """List all agent folders discovered in REVISAR.ia"""
    result = pcloud_service.find_agent_folders()
    return result

@router.get("/documents/{agent_id}")
async def list_agent_documents(agent_id: str):
    result = pcloud_service.list_agent_documents(agent_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result

@router.post("/sync/{agent_id}")
async def sync_agent_to_rag(agent_id: str):
    try:
        from services.rag_service import rag_service
        result = pcloud_service.sync_agent_documents_to_rag(agent_id, rag_service)
        return result
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-all")
async def sync_all_agents_to_rag():
    try:
        from services.rag_service import rag_service
        
        agents = ["A1_ESTRATEGIA", "A2_PMO", "A3_FISCAL", "A4_LEGAL", "A5_FINANZAS", "A6_PROVEEDOR", "A7_DEFENSA", "KNOWLEDGE_BASE"]
        results = {}
        
        for agent_id in agents:
            result = pcloud_service.sync_agent_documents_to_rag(agent_id, rag_service)
            results[agent_id] = {
                "success": result.get("success"),
                "synced_count": result.get("synced_count", 0),
                "error_count": result.get("error_count", 0)
            }
            
        total_synced = sum(r.get("synced_count", 0) for r in results.values())
        
        return {
            "success": True,
            "total_synced": total_synced,
            "by_agent": results
        }
    except Exception as e:
        logger.error(f"Sync all error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{file_id}/link")
async def get_file_download_link(file_id: int):
    if not pcloud_service.auth_token:
        pcloud_service.login()
    result = pcloud_service.get_file_link(file_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/list-root")
async def list_root_folder():
    """List contents of the pCloud root folder"""
    if not pcloud_service.auth_token:
        pcloud_service.login()
    result = pcloud_service.list_folder(folder_id=0)
    return result


@router.post("/create-root-folder")
async def create_root_folder():
    """Create the REVISAR.IA folder in the root directory if it doesn't exist"""
    if not pcloud_service.auth_token:
        login_result = pcloud_service.login()
        if not login_result.get("success"):
            return login_result

    # First check if folder already exists
    root_contents = pcloud_service.list_folder(folder_id=0)
    if root_contents.get("success"):
        for item in root_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "").upper() == "REVISAR.IA":
                return {
                    "success": True,
                    "already_exists": True,
                    "folder_id": item.get("id"),
                    "name": item.get("name"),
                    "message": "Folder REVISAR.IA already exists"
                }

    # Create the folder
    result = pcloud_service.create_folder(parent_folder_id=0, folder_name="REVISAR.IA")
    return result


@router.post("/setup-complete")
async def setup_complete_structure():
    """
    Complete setup: creates REVISAR.IA folder if needed, then initializes all subfolders.
    This is the recommended endpoint for initial setup.
    """
    if not pcloud_service.auth_token:
        login_result = pcloud_service.login()
        if not login_result.get("success"):
            return login_result

    # Step 1: Check if REVISAR.IA exists
    root_contents = pcloud_service.list_folder(folder_id=0)
    revisar_ia_folder_id = None

    if root_contents.get("success"):
        for item in root_contents.get("items", []):
            if item.get("is_folder") and item.get("name", "").upper() == "REVISAR.IA":
                revisar_ia_folder_id = item.get("id")
                logger.info(f"Found existing REVISAR.IA folder: {revisar_ia_folder_id}")
                break

    # Step 2: Create REVISAR.IA if it doesn't exist
    if not revisar_ia_folder_id:
        create_result = pcloud_service.create_folder(parent_folder_id=0, folder_name="REVISAR.IA")
        if create_result.get("success"):
            revisar_ia_folder_id = create_result.get("folder_id")
            logger.info(f"Created REVISAR.IA folder: {revisar_ia_folder_id}")
        else:
            return {
                "success": False,
                "error": f"Could not create REVISAR.IA folder: {create_result.get('error')}"
            }

    # Step 3: Set the folder ID and initialize subfolders
    pcloud_service.revisar_ia_folder_id = revisar_ia_folder_id

    # Create all required subfolders
    from services.pcloud_service import REQUIRED_SUBFOLDERS
    created_folders = []
    existing_folders = []

    # Get current contents
    revisar_contents = pcloud_service.list_folder(folder_id=revisar_ia_folder_id)
    existing_names = []
    if revisar_contents.get("success"):
        existing_names = [item.get("name", "").upper() for item in revisar_contents.get("items", []) if item.get("is_folder")]

    for subfolder in REQUIRED_SUBFOLDERS:
        if subfolder.upper() in [n.upper() for n in existing_names]:
            existing_folders.append(subfolder)
        else:
            result = pcloud_service.create_folder(revisar_ia_folder_id, subfolder)
            if result.get("success") or result.get("already_exists"):
                created_folders.append(subfolder)
                if result.get("folder_id"):
                    pcloud_service.agent_folders[subfolder] = result.get("folder_id")

    pcloud_service.initialized = True

    return {
        "success": True,
        "revisar_ia_folder_id": revisar_ia_folder_id,
        "created_folders": created_folders,
        "existing_folders": existing_folders,
        "total_created": len(created_folders),
        "total_existing": len(existing_folders),
        "message": f"Setup complete! Created {len(created_folders)} folders, {len(existing_folders)} already existed"
    }
