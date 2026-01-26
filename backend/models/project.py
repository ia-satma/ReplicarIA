"""
MongoDB Models for Revisar.ia System
Based on the architectural export schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_REVIEW = "IN_REVIEW"

class AgentDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"

class Project(BaseModel):
    project_id: str
    project_name: str
    sponsor_name: str
    sponsor_email: str
    budget_estimate: float = 0.0
    expected_economic_benefit: float = 0.0
    description: str = ""
    status: ProjectStatus = ProjectStatus.IN_REVIEW
    current_status: str = "intake"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    participants: List[str] = Field(default_factory=lambda: ["A1_SPONSOR", "A2_PMO", "A3_FISCAL", "A5_FINANZAS"])
    po_path: Optional[str] = None
    po_pcloud_link: Optional[str] = None
    defense_file_path: Optional[str] = None
    defense_file_pcloud_link: Optional[str] = None
    workflow_state: str = "intake"
    version: int = 1
    parent_project_id: Optional[str] = None
    is_adjustment: bool = False
    adjustment_notes: Optional[str] = None
    
    class Config:
        use_enum_values = True

class AgentInteraction(BaseModel):
    interaction_id: str
    project_id: str
    agent_id: str
    analysis: str
    decision: AgentDecision
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rag_sources_used: List[str] = Field(default_factory=list)
    confidence_level: str = "high"
    
    class Config:
        use_enum_values = True

class DiscussionRound(BaseModel):
    round: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    participants: List[str]
    type: str = "review"

class AgentDiscussion(BaseModel):
    discussion_id: str
    project_id: str
    status: str = "in_progress"
    current_round: int = 1
    max_rounds: int = 3
    participants: List[str] = Field(default_factory=list)
    moderator: str = "A2_PMO"
    rounds: List[DiscussionRound] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class PurchaseOrder(BaseModel):
    po_number: str
    project_id: str
    amount: float
    status: str = "issued"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "A2_PMO"
    approved_by: List[str] = Field(default_factory=list)
    pdf_path: Optional[str] = None
    pcloud_link: Optional[str] = None

class ProjectCreate(BaseModel):
    project_name: str
    sponsor_name: str
    sponsor_email: str
    budget_estimate: float = 0.0
    expected_economic_benefit: float = 0.0
    description: str = ""

class ProjectUpdate(BaseModel):
    status: Optional[ProjectStatus] = None
    workflow_state: Optional[str] = None
    po_path: Optional[str] = None
    po_pcloud_link: Optional[str] = None
    defense_file_path: Optional[str] = None
    defense_file_pcloud_link: Optional[str] = None
