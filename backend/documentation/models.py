from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class AgentType(str, Enum):
    PRINCIPAL = "principal"
    SUBAGENT = "subagent"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class CapabilityModel(BaseModel):
    id: str
    name: str
    description: str
    can_block: bool = False


class ControlModel(BaseModel):
    id: str
    name: str
    phase: str
    condition: str


class AgentInventoryItem(BaseModel):
    agent_id: str
    name: str
    persona: Optional[str] = None
    type: AgentType
    role: str
    description: str
    version: str = "1.0.0"
    status: AgentStatus = AgentStatus.ACTIVE
    capabilities: List[CapabilityModel] = []
    controls: List[ControlModel] = []
    phases: List[str] = []
    parent_id: Optional[str] = None
    can_block: bool = False
    doc_url: Optional[str] = None
    source_refs: List[Dict[str, str]] = []
    last_documented_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PhaseModel(BaseModel):
    phase_id: str
    name: str
    description: str
    is_hard_lock: bool = False
    lock_condition: Optional[str] = None
    required_agents: List[str] = []
    order: int


class PillarModel(BaseModel):
    pillar_id: str
    name: str
    max_points: int = 25
    description: str
    evaluation_criteria: List[str] = []


class DocumentationSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"
    agents: List[AgentInventoryItem] = []
    phases: List[PhaseModel] = []
    pillars: List[PillarModel] = []
    changelog: str = ""
