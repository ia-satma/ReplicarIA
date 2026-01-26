from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class AgentRole(str, Enum):
    """Roles de los agentes en el sistema"""
    SPONSOR = "sponsor"
    PMO = "pmo"
    FISCAL = "fiscal"
    LEGAL = "legal"
    FINANZAS = "finanzas"
    PROVEEDOR = "proveedor"

class AgentProvider(str, Enum):
    """Proveedores de modelos LLM"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class AgentPersonality(BaseModel):
    """Personalidad de un agente"""
    tone: str  # Formal, casual, técnico, etc.
    communication_style: str  # Directo, detallado, conciso
    expertise_areas: List[str]  # Áreas de especialización
    language_preference: str = "es"  # Español por defecto

class AgentConfig(BaseModel):
    """Configuración de un agente IA"""
    agent_id: str
    name: str  # Nombre ficticio del agente
    role: AgentRole
    department: str  # Proveedor o Cliente (Constructora)
    
    # Configuración LLM
    llm_provider: AgentProvider
    llm_model: str  # gpt-5, claude-3-7-sonnet-20250219, etc.
    system_prompt: str
    
    # Personalidad
    personality: AgentPersonality
    
    # Comunicación
    email_address: str
    gmail_token_path: Optional[str] = None
    
    # Base de conocimiento
    drive_folder_id: str
    drive_folder_name: str
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        use_enum_values = True

class AgentMessage(BaseModel):
    """Mensaje enviado por un agente"""
    message_id: str
    from_agent_id: str
    to_agent_id: str
    subject: str
    body: str
    attachments: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    thread_id: Optional[str] = None
    project_id: Optional[str] = None

class AgentInteraction(BaseModel):
    """Interacción entre agentes registrada"""
    interaction_id: str
    project_id: str
    phase: str  # Fase del proyecto (0-9)
    from_agent: str
    to_agent: str
    interaction_type: str  # email, analysis, validation, etc.
    content: str
    llm_response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = {}
