"""
Local Persistence Database - JSON-backed database for demo/development mode
Provides the same interface as MongoDB Motor but stores data in a local JSON file
Data persists across server restarts without requiring external MongoDB
"""
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import threading

logger = logging.getLogger(__name__)

STORAGE_FILE = Path(__file__).parent.parent / "revisar_storage.json"
LOCAL_PERSISTENCE_MODE = True

_save_lock = threading.Lock()


class MockCursor:
    def __init__(self, data: List[Dict], projection: Optional[Dict] = None):
        self.data = data
        self.projection = projection
        self._sort_field = None
        self._sort_order = 1
        self._limit_count = None
    
    def sort(self, field: str, order: int = 1):
        self._sort_field = field
        self._sort_order = order
        return self
    
    def limit(self, count: int):
        self._limit_count = count
        return self
    
    async def to_list(self, length: int = 1000) -> List[Dict]:
        result = self.data.copy()
        
        if self._sort_field:
            result.sort(
                key=lambda x: x.get(self._sort_field, ''),
                reverse=(self._sort_order == -1)
            )
        
        limit = self._limit_count or length
        result = result[:limit]
        
        if self.projection:
            filtered = []
            for item in result:
                new_item = {}
                for key in item:
                    if key == '_id' and self.projection.get('_id') == 0:
                        continue
                    if key in self.projection or self.projection.get('_id') == 0:
                        new_item[key] = item[key]
                    elif not any(v == 1 for v in self.projection.values() if v != 0):
                        new_item[key] = item[key]
                filtered.append(new_item)
            result = filtered
        
        return result


class MockCollection:
    def __init__(self, name: str, data: List[Dict] = None, db_ref: 'DemoDatabase' = None):
        self.name = name
        self._data = data or []
        self._db_ref = db_ref
    
    def _trigger_save(self):
        if self._db_ref:
            self._db_ref.save_to_disk()
    
    def find(self, query: Dict = None, projection: Dict = None) -> MockCursor:
        if query is None:
            query = {}
        
        result = []
        for item in self._data:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result.append(item.copy())
        
        return MockCursor(result, projection)
    
    async def find_one(self, query: Dict, projection: Dict = None) -> Optional[Dict]:
        for item in self._data:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result = item.copy()
                if projection and projection.get('_id') == 0:
                    result.pop('_id', None)
                return result
        return None
    
    async def insert_one(self, document: Dict):
        doc = document.copy()
        if '_id' not in doc:
            doc['_id'] = f"local_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._data) + 1}"
        self._data.append(doc)
        self._trigger_save()
        
        class InsertResult:
            def __init__(self, id):
                self.inserted_id = id
        
        return InsertResult(doc['_id'])
    
    async def update_one(self, query: Dict, update: Dict, upsert: bool = False):
        for i, item in enumerate(self._data):
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                if '$set' in update:
                    for key, value in update['$set'].items():
                        self._data[i][key] = value
                if '$push' in update:
                    for key, value in update['$push'].items():
                        if key not in self._data[i]:
                            self._data[i][key] = []
                        self._data[i][key].append(value)
                
                self._trigger_save()
                
                class UpdateResult:
                    modified_count = 1
                    matched_count = 1
                
                return UpdateResult()
        
        if upsert:
            doc = query.copy()
            if '$set' in update:
                doc.update(update['$set'])
            await self.insert_one(doc)
        
        class UpdateResult:
            modified_count = 0
            matched_count = 0
        
        return UpdateResult()
    
    async def delete_one(self, query: Dict):
        for i, item in enumerate(self._data):
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                self._data.pop(i)
                self._trigger_save()
                
                class DeleteResult:
                    deleted_count = 1
                
                return DeleteResult()
        
        class DeleteResult:
            deleted_count = 0
        
        return DeleteResult()
    
    async def count_documents(self, query: Dict = None) -> int:
        if query is None:
            return len(self._data)
        
        count = 0
        for item in self._data:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                count += 1
        return count


class DemoDatabase:
    def __init__(self):
        self._collections: Dict[str, MockCollection] = {}
        self._storage_file = STORAGE_FILE
        self._loaded_from_disk = False
        self._initialize_database()
    
    def __getattr__(self, name: str) -> MockCollection:
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._collections:
            self._collections[name] = MockCollection(name, db_ref=self)
        return self._collections[name]
    
    def __getitem__(self, name: str) -> MockCollection:
        return self.__getattr__(name)
    
    def _initialize_database(self):
        if self.load_from_disk():
            logger.info(f"✅ Local persistence database loaded from {self._storage_file}")
            self._loaded_from_disk = True
        else:
            self._initialize_default_data()
            logger.info("📦 Local persistence database initialized with default data")
    
    def _initialize_default_data(self):
        now = datetime.now(timezone.utc).isoformat()
        
        demo_agents = [
            {
                "_id": "A1_ESTRATEGIA",
                "id": "A1_ESTRATEGIA",
                "name": "Agente Estrategia",
                "type": "strategy",
                "status": "active",
                "description": "Agente especializado en análisis estratégico y validación de propuestas",
                "capabilities": ["strategy_analysis", "proposal_validation", "risk_assessment"],
                "created_at": now
            },
            {
                "_id": "A2_PMO",
                "id": "A2_PMO",
                "name": "Agente PMO",
                "type": "pmo",
                "status": "active",
                "description": "Agente de gestión de proyectos y seguimiento de entregables",
                "capabilities": ["project_management", "timeline_tracking", "resource_allocation"],
                "created_at": now
            },
            {
                "_id": "A3_FISCAL",
                "id": "A3_FISCAL",
                "name": "Agente Fiscal",
                "type": "fiscal",
                "status": "active",
                "description": "Agente especializado en aspectos fiscales y tributarios",
                "capabilities": ["tax_analysis", "compliance_check", "fiscal_optimization"],
                "created_at": now
            },
            {
                "_id": "A4_LEGAL",
                "id": "A4_LEGAL",
                "name": "Agente Legal",
                "type": "legal",
                "status": "active",
                "description": "Agente de revisión legal y cumplimiento normativo",
                "capabilities": ["legal_review", "contract_analysis", "regulatory_compliance"],
                "created_at": now
            },
            {
                "_id": "A5_FINANZAS",
                "id": "A5_FINANZAS",
                "name": "Agente Finanzas",
                "type": "finance",
                "status": "active",
                "description": "Agente de análisis financiero y valoración económica",
                "capabilities": ["financial_analysis", "valuation", "cost_benefit_analysis"],
                "created_at": now
            }
        ]
        
        self._collections['agents'] = MockCollection('agents', demo_agents, db_ref=self)
        self._collections['projects'] = MockCollection('projects', [], db_ref=self)
        self._collections['agent_interactions'] = MockCollection('agent_interactions', [], db_ref=self)
        self._collections['status_checks'] = MockCollection('status_checks', [], db_ref=self)
        self._collections['validation_reports'] = MockCollection('validation_reports', [], db_ref=self)
        self._collections['users'] = MockCollection('users', [], db_ref=self)
        self._collections['agent_discussions'] = MockCollection('agent_discussions', [], db_ref=self)
        self._collections['purchase_orders'] = MockCollection('purchase_orders', [], db_ref=self)
        
        self.save_to_disk()
    
    def load_from_disk(self) -> bool:
        try:
            if not self._storage_file.exists():
                return False
            
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for collection_name, documents in data.get('collections', {}).items():
                self._collections[collection_name] = MockCollection(
                    collection_name, 
                    documents, 
                    db_ref=self
                )
            
            loaded_count = sum(len(c._data) for c in self._collections.values())
            logger.info(f"📂 Loaded {loaded_count} documents from {len(self._collections)} collections")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse storage file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load from disk: {e}")
            return False
    
    def save_to_disk(self) -> bool:
        with _save_lock:
            try:
                data = {
                    "version": "1.0",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "collections": {}
                }
                
                for name, collection in self._collections.items():
                    data["collections"][name] = collection._data
                
                with open(self._storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to save to disk: {e}")
                return False


class DemoClient:
    def __init__(self):
        self._db = None
    
    def __getitem__(self, name: str) -> DemoDatabase:
        if self._db is None:
            self._db = DemoDatabase()
        return self._db
    
    def close(self):
        if self._db:
            self._db.save_to_disk()


def get_demo_database():
    client = DemoClient()
    db = client['demo']
    return client, db


def is_local_persistence() -> bool:
    return LOCAL_PERSISTENCE_MODE and STORAGE_FILE.exists()
