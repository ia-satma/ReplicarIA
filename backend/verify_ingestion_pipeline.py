import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import UploadFile, Request
from routes.projects_pg import upload_file
from services.knowledge_service import KnowledgeService, get_db_connection

class MockRequest:
    headers = {}

async def mock_upload_file(filename, content):
    from io import BytesIO
    return UploadFile(filename=filename, file=BytesIO(content), size=len(content), headers={"content-type": "text/plain"})

async def verify():
    print("Verifying Ingestion Pipeline...")
    
    conn = await get_db_connection()
    if not conn:
        print("Critcal: Database connection failed. Check DATABASE_URL.")
        return

    # 1. Setup Mock User with valid Empresa
    import uuid
    mock_user_uuid = str(uuid.uuid4())
    mock_user = {"id": mock_user_uuid, "user_id": mock_user_uuid, "empresa_id": None}
    
    try:
        # Hybrid Architecture: Empresas might be in Mongo.
        # Check if we can find an existing empresa_id in the Knowledge DB to use.
        # Or just use a random UUID if no foreign key exists or if table is empty.
        import uuid
        existing_folder = await conn.fetchrow("SELECT empresa_id FROM knowledge_folders LIMIT 1")
        if existing_folder:
            mock_user["empresa_id"] = str(existing_folder["empresa_id"])
            print(f"Using existing company context from Knowledge DB: {mock_user['empresa_id']}")
        else:
            # Fallback to a random UUID - assuming no strict FK to a missing 'empresas' table in PG
            mock_user["empresa_id"] = str(uuid.uuid4())
            print(f"No existing company found. Using random UUID: {mock_user['empresa_id']}")
    except Exception as e:
        print(f"Could not resolve empresa_id: {e}")
        # Fallback
        import uuid
        mock_user["empresa_id"] = str(uuid.uuid4())
    finally:
        await conn.close()

    # 2. Call the Endpoint Function directly
    test_content = b"Content for verification ingestion pipeline."
    test_filename = "verify_ingestion_dual_write.txt"
    
    file_obj = await mock_upload_file(test_filename, test_content)
    
    print(f"Uploading file: {test_filename}")
    try:
        response = await upload_file(
            file=file_obj,
            request=MockRequest(),
            current_user=mock_user
        )
        print("Upload endpoint returned success:", response.get("success"))
        print("Saved as:", response.get("rag_ingested"))
    except Exception as e:
        print(f"Upload endpoint failed: {e}")
        return

    # 3. Verify Knowledge Service Ingestion
    print("Checking Knowledge Repository...")
    ks = KnowledgeService()
    
    # Search for the file
    docs = await ks.search(mock_user["empresa_id"], "verify_ingestion_dual_write")
    found = False
    for doc in docs:
        if doc['filename'] == test_filename:
            print(f"✅ SUCCESS: Document found in KnowledgeService! ID: {doc['id']}")
            print(f"   Path: {doc['path']}")
            print(f"   Status: {doc['status']}")
            found = True
            
            # 4. Cleanup
            deleted = await ks.delete_document(doc['id'], mock_user["empresa_id"], hard_delete=True)
            if deleted:
                print("   Cleanup: Document deleted.")
            break
            
    if not found:
        print("❌ FAILURE: Document NOT found in KnowledgeService after upload.")
        # Check if local file exists
        local_path = Path("uploads") / response.get("saved_as")
        if local_path.exists():
            print(f"   Local file WAS created at {local_path}, but RAG ingestion failed.")
            # Cleanup local
            os.remove(local_path)

if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except KeyboardInterrupt:
        pass
