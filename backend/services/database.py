"""
MongoDB Database Service for Revisar.ia System
Handles all database operations with async motor driver
Multi-tenant support with empresa_id as mandatory field
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', '')
DB_NAME = os.environ.get('DB_NAME', 'revisar_agent_network')

DEMO_MODE = not MONGO_URL

db = None
client = None

if not DEMO_MODE:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        logger.info(f"Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}, using demo mode")
        DEMO_MODE = True
        db = None

DEMO_PROJECTS: List[Dict[str, Any]] = []
DEMO_INTERACTIONS: List[Dict[str, Any]] = []


def serialize_mongo_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Convert MongoDB document to JSON-serializable dict by handling ObjectId and datetime."""
    if doc is None:
        return None
    
    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["_id"] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif hasattr(value, '__str__') and type(value).__name__ == 'ObjectId':
            result[key] = str(value)
        else:
            result[key] = value
    return result


def serialize_mongo_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert list of MongoDB documents to JSON-serializable dicts."""
    return [serialize_mongo_doc(doc) for doc in docs if doc is not None]


class ProjectRepository:
    """
    MongoDB repository for projects with multi-tenant support.
    All projects require empresa_id as mandatory field.
    All read/update/delete operations validate empresa_id ownership.
    """
    
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.collection_name = "projects"
    
    def _get_collection(self):
        if self.demo_mode or db is None:
            return None
        return db[self.collection_name]
    
    async def create_project(
        self, 
        project_data: Dict[str, Any], 
        empresa_id: str,
        created_by: Optional[str] = None
    ) -> str:
        """
        Create a new project with mandatory empresa_id.
        
        Args:
            project_data: Project data dictionary
            empresa_id: Company ID (required)
            created_by: User ID who created the project
            
        Returns:
            project_id: The created project ID
        """
        if not empresa_id:
            raise ValueError("empresa_id is required for all projects")
        
        project_id = project_data.get("project_id") or str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        project = {
            **project_data,
            "project_id": project_id,
            "empresa_id": empresa_id,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now,
            "status": project_data.get("status", "IN_REVIEW"),
            "workflow_state": project_data.get("workflow_state", "intake"),
            "participants": project_data.get("participants", [
                "A1_SPONSOR", "A2_PMO", "A3_FISCAL", "A5_FINANZAS"
            ])
        }
        
        if self.demo_mode:
            DEMO_PROJECTS.append(project)
            logger.info(f"[DEMO] Created project {project_id} for empresa {empresa_id}")
            return project_id
        
        collection = self._get_collection()
        await collection.insert_one(project)
        logger.info(f"Created project {project_id} for empresa {empresa_id}")
        return project_id
    
    async def get_project(
        self, 
        project_id: str, 
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a project by its ID, optionally validating empresa ownership.
        
        Args:
            project_id: The project ID
            empresa_id: If provided, validates project belongs to this empresa
            
        Returns:
            Project data or None if not found (or not authorized)
        """
        if self.demo_mode:
            for p in DEMO_PROJECTS:
                if p.get("project_id") == project_id:
                    if empresa_id and p.get("empresa_id") != empresa_id:
                        return None
                    return p
            return None
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        project = await collection.find_one(query)
        return serialize_mongo_doc(project)
    
    async def get_projects_by_empresa(
        self, 
        empresa_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all projects for a specific company.
        
        Args:
            empresa_id: Company ID (required)
            status: Optional status filter
            limit: Max number of results
            
        Returns:
            List of projects for the company
        """
        if not empresa_id:
            raise ValueError("empresa_id is required")
        
        if self.demo_mode:
            projects = [p for p in DEMO_PROJECTS if p.get("empresa_id") == empresa_id]
            if status:
                projects = [p for p in projects if p.get("status") == status]
            return projects[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"empresa_id": empresa_id}
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)
    
    async def update_project(
        self, 
        project_id: str, 
        updates: Dict[str, Any],
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a project and return the updated document.
        If empresa_id is provided, validates ownership before updating.
        
        Args:
            project_id: The project ID
            updates: Fields to update
            empresa_id: If provided, validates project belongs to this empresa
            
        Returns:
            Updated project or None if not found/not authorized
        """
        updates["updated_at"] = datetime.now(timezone.utc)
        
        if self.demo_mode:
            for i, p in enumerate(DEMO_PROJECTS):
                if p.get("project_id") == project_id:
                    if empresa_id and p.get("empresa_id") != empresa_id:
                        return None
                    DEMO_PROJECTS[i].update(updates)
                    logger.info(f"[DEMO] Updated project {project_id}")
                    return DEMO_PROJECTS[i]
            return None
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        result = await collection.find_one_and_update(
            query,
            {"$set": updates},
            return_document=ReturnDocument.AFTER
        )
        if result:
            logger.info(f"Updated project {project_id}")
        return serialize_mongo_doc(result)
    
    async def delete_project(
        self, 
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> bool:
        """
        Delete a project by its ID.
        If empresa_id is provided, validates ownership before deleting.
        
        Args:
            project_id: The project ID
            empresa_id: If provided, validates project belongs to this empresa
            
        Returns:
            True if deleted, False if not found/not authorized
        """
        if self.demo_mode:
            for i, p in enumerate(DEMO_PROJECTS):
                if p.get("project_id") == project_id:
                    if empresa_id and p.get("empresa_id") != empresa_id:
                        return False
                    DEMO_PROJECTS.pop(i)
                    logger.info(f"[DEMO] Deleted project {project_id}")
                    return True
            return False
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        result = await collection.delete_one(query)
        deleted = result.deleted_count > 0
        if deleted:
            logger.info(f"Deleted project {project_id}")
        return deleted
    
    async def get_all_projects(
        self, 
        empresa_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all projects for an empresa, or all if admin (empresa_id=None).
        
        Args:
            empresa_id: Company ID filter (None = admin access to all)
            status: Optional status filter
            limit: Max number of results
            
        Returns:
            List of projects
        """
        if self.demo_mode:
            projects = DEMO_PROJECTS.copy()
            if empresa_id:
                projects = [p for p in projects if p.get("empresa_id") == empresa_id]
            if status:
                projects = [p for p in projects if p.get("status") == status]
            return projects[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {}
        if empresa_id:
            query["empresa_id"] = empresa_id
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)
    
    async def search_projects(
        self,
        empresa_id: str,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search projects within an empresa by name or description.
        
        Args:
            empresa_id: Company ID (required)
            search_term: Text to search in name/description
            status: Optional status filter
            limit: Max number of results
            
        Returns:
            List of matching projects
        """
        if not empresa_id:
            raise ValueError("empresa_id is required for search")
        
        if self.demo_mode:
            projects = [p for p in DEMO_PROJECTS if p.get("empresa_id") == empresa_id]
            if search_term:
                term_lower = search_term.lower()
                projects = [
                    p for p in projects 
                    if term_lower in (p.get("name", "") or "").lower() 
                    or term_lower in (p.get("description", "") or "").lower()
                ]
            if status:
                projects = [p for p in projects if p.get("status") == status]
            return projects[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"empresa_id": empresa_id}
        
        if search_term:
            query["$or"] = [
                {"name": {"$regex": search_term, "$options": "i"}},
                {"description": {"$regex": search_term, "$options": "i"}},
                {"project_name": {"$regex": search_term, "$options": "i"}}
            ]
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)


class InteractionRepository:
    """Repository for agent interactions/deliberations."""
    
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.collection_name = "agent_interactions"
    
    def _get_collection(self):
        if self.demo_mode or db is None:
            return None
        return db[self.collection_name]
    
    async def create_interaction(
        self, 
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new interaction record."""
        interaction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        interaction = {
            **interaction_data,
            "interaction_id": interaction_id,
            "timestamp": now,
            "created_at": now
        }
        
        if self.demo_mode:
            DEMO_INTERACTIONS.append(interaction)
            return interaction
        
        collection = self._get_collection()
        await collection.insert_one(interaction)
        return interaction
    
    async def get_interactions(
        self, 
        project_id: Optional[str] = None,
        empresa_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get interactions, optionally filtered by project and empresa."""
        if self.demo_mode:
            interactions = DEMO_INTERACTIONS.copy()
            if project_id:
                interactions = [i for i in interactions if i.get("project_id") == project_id]
            if empresa_id:
                interactions = [i for i in interactions if i.get("empresa_id") == empresa_id]
            return interactions[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {}
        if project_id:
            query["project_id"] = project_id
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)


class DatabaseService:
    """
    Legacy DatabaseService for backward compatibility.
    Wraps the new repository classes.
    """
    
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.project_repo = ProjectRepository()
        self.interaction_repo = InteractionRepository()
    
    async def get_projects(
        self, 
        empresa_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get projects, filtered by empresa if provided."""
        return await self.project_repo.get_all_projects(empresa_id=empresa_id, status=status)
    
    async def get_project(
        self, 
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a project by ID, optionally validating empresa ownership."""
        return await self.project_repo.get_project(project_id, empresa_id=empresa_id)
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project - requires empresa_id for multi-tenant isolation."""
        empresa_id = project_data.get("empresa_id")
        if not empresa_id:
            raise ValueError("empresa_id is required for all projects (multi-tenant)")
        
        created_by = project_data.get("created_by")
        
        project_id = await self.project_repo.create_project(
            project_data=project_data,
            empresa_id=empresa_id,
            created_by=created_by
        )
        
        return await self.project_repo.get_project(project_id) or project_data
    
    async def update_project(
        self, 
        project_id: str, 
        update_data: Dict[str, Any],
        empresa_id: Optional[str] = None
    ) -> bool:
        """Update project and return success status."""
        result = await self.project_repo.update_project(project_id, update_data, empresa_id=empresa_id)
        return result is not None
    
    async def get_interactions(
        self, 
        project_id: Optional[str] = None,
        empresa_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get interactions."""
        return await self.interaction_repo.get_interactions(project_id, empresa_id=empresa_id)
    
    async def create_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create interaction."""
        return await self.interaction_repo.create_interaction(interaction_data)
    
    async def get_project_stats(self, empresa_id: Optional[str] = None) -> Dict[str, Any]:
        """Get project statistics, optionally filtered by empresa."""
        projects = await self.get_projects(empresa_id=empresa_id)
        
        approved = len([p for p in projects if p.get("status") == "APPROVED"])
        rejected = len([p for p in projects if p.get("status") == "REJECTED"])
        in_review = len([p for p in projects if p.get("status") == "IN_REVIEW"])
        
        total_amount = sum(
            p.get("budget_estimate", 0) or p.get("amount", 0) 
            for p in projects 
            if p.get("status") == "APPROVED"
        )
        
        return {
            "approved": approved,
            "rejected": rejected,
            "in_review": in_review,
            "total": len(projects),
            "total_amount": total_amount
        }


DEMO_DELIBERATION_STATES: List[Dict[str, Any]] = []


class DeliberationStateRepository:
    """
    Repository for persisting deliberation workflow state.
    Allows resuming deliberations after server restart.
    All operations validate empresa_id for multi-tenant isolation.
    """
    
    def __init__(self):
        self.demo_mode = DEMO_MODE
        self.collection_name = "deliberation_states"
    
    def _get_collection(self):
        if self.demo_mode or db is None:
            return None
        return db[self.collection_name]
    
    async def save_state(
        self,
        project_id: str,
        empresa_id: str,
        current_stage: str,
        stage_results: Dict[str, Any],
        status: str = "in_progress",
        project_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save or update deliberation state.
        
        Args:
            project_id: Project identifier
            empresa_id: Company identifier (multi-tenant)
            current_stage: Current workflow stage (E1-E5)
            stage_results: Outputs from each completed stage
            status: in_progress, completed, paused, failed
            project_data: Original project data for resume
        """
        if not empresa_id:
            raise ValueError("empresa_id is required for deliberation state")
        
        now = datetime.now(timezone.utc)
        
        state = {
            "project_id": project_id,
            "empresa_id": empresa_id,
            "current_stage": current_stage,
            "stage_results": stage_results,
            "status": status,
            "project_data": project_data,
            "updated_at": now
        }
        
        if self.demo_mode:
            for i, s in enumerate(DEMO_DELIBERATION_STATES):
                if s.get("project_id") == project_id:
                    DEMO_DELIBERATION_STATES[i].update(state)
                    logger.info(f"[DEMO] Updated deliberation state for {project_id}")
                    return DEMO_DELIBERATION_STATES[i]
            
            state["created_at"] = now
            DEMO_DELIBERATION_STATES.append(state)
            logger.info(f"[DEMO] Created deliberation state for {project_id}")
            return state
        
        collection = self._get_collection()
        result = await collection.find_one_and_update(
            {"project_id": project_id},
            {
                "$set": state,
                "$setOnInsert": {"created_at": now}
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        logger.info(f"Saved deliberation state for {project_id}: stage={current_stage}, status={status}")
        return serialize_mongo_doc(result)
    
    async def get_state(
        self, 
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get deliberation state for a project, optionally validating empresa."""
        if self.demo_mode:
            for s in DEMO_DELIBERATION_STATES:
                if s.get("project_id") == project_id:
                    if empresa_id and s.get("empresa_id") != empresa_id:
                        return None
                    return s
            return None
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        state = await collection.find_one(query)
        return serialize_mongo_doc(state)
    
    async def get_states_by_empresa(
        self,
        empresa_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all deliberation states for a company."""
        if not empresa_id:
            raise ValueError("empresa_id is required")
        
        if self.demo_mode:
            states = [s for s in DEMO_DELIBERATION_STATES if s.get("empresa_id") == empresa_id]
            if status:
                states = [s for s in states if s.get("status") == status]
            return states[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"empresa_id": empresa_id}
        if status:
            query["status"] = status
        
        cursor = collection.find(query).sort("updated_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)
    
    async def get_resumable_states(
        self, 
        empresa_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get in_progress or paused deliberations that can be resumed."""
        if self.demo_mode:
            states = [s for s in DEMO_DELIBERATION_STATES if s.get("status") in ("in_progress", "paused")]
            if empresa_id:
                states = [s for s in states if s.get("empresa_id") == empresa_id]
            return states[:limit]
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"status": {"$in": ["in_progress", "paused"]}}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        cursor = collection.find(query).sort("updated_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return serialize_mongo_docs(docs)
    
    async def update_status(
        self, 
        project_id: str, 
        status: str,
        empresa_id: Optional[str] = None
    ) -> bool:
        """Update only the status of a deliberation, optionally validating empresa."""
        now = datetime.now(timezone.utc)
        
        if self.demo_mode:
            for i, s in enumerate(DEMO_DELIBERATION_STATES):
                if s.get("project_id") == project_id:
                    if empresa_id and s.get("empresa_id") != empresa_id:
                        return False
                    DEMO_DELIBERATION_STATES[i]["status"] = status
                    DEMO_DELIBERATION_STATES[i]["updated_at"] = now
                    return True
            return False
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        result = await collection.update_one(
            query,
            {"$set": {"status": status, "updated_at": now}}
        )
        return result.modified_count > 0
    
    async def delete_state(
        self, 
        project_id: str,
        empresa_id: Optional[str] = None
    ) -> bool:
        """Delete deliberation state for a project, optionally validating empresa."""
        if self.demo_mode:
            for i, s in enumerate(DEMO_DELIBERATION_STATES):
                if s.get("project_id") == project_id:
                    if empresa_id and s.get("empresa_id") != empresa_id:
                        return False
                    DEMO_DELIBERATION_STATES.pop(i)
                    return True
            return False
        
        collection = self._get_collection()
        query: Dict[str, Any] = {"project_id": project_id}
        if empresa_id:
            query["empresa_id"] = empresa_id
        
        result = await collection.delete_one(query)
        return result.deleted_count > 0


project_repository = ProjectRepository()
interaction_repository = InteractionRepository()
deliberation_state_repository = DeliberationStateRepository()
db_service = DatabaseService()


async def create_multi_tenant_indexes():
    """Create MongoDB indexes for multi-tenant isolation and performance."""
    if DEMO_MODE or db is None:
        logger.info("[DEMO] Skipping index creation in demo mode")
        return
    
    try:
        await db.projects.create_index("empresa_id")
        await db.projects.create_index([("empresa_id", 1), ("status", 1)])
        await db.projects.create_index([("empresa_id", 1), ("created_at", -1)])
        await db.projects.create_index([("empresa_id", 1), ("project_id", 1)], unique=True)
        
        await db.agent_interactions.create_index("empresa_id")
        await db.agent_interactions.create_index([("empresa_id", 1), ("project_id", 1)])
        await db.agent_interactions.create_index([("empresa_id", 1), ("timestamp", -1)])
        
        await db.deliberation_states.create_index("empresa_id")
        await db.deliberation_states.create_index([("empresa_id", 1), ("status", 1)])
        await db.deliberation_states.create_index([("empresa_id", 1), ("project_id", 1)], unique=True)
        
        logger.info("Multi-tenant MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating multi-tenant indexes: {e}")


def get_db():
    """Get MongoDB database instance."""
    return db
