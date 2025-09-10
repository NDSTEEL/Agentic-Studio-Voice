"""
Agent configuration model.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class AgentConfig:
    """Agent configuration data model."""
    agent_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    voice_config: Optional[Dict[str, Any]] = None
    knowledge_base_config: Optional[Dict[str, Any]] = None
    phone_config: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.voice_config is None:
            self.voice_config = {}
        if self.knowledge_base_config is None:
            self.knowledge_base_config = {}
        if self.phone_config is None:
            self.phone_config = {}
        if self.settings is None:
            self.settings = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "voice_config": self.voice_config,
            "knowledge_base_config": self.knowledge_base_config,
            "phone_config": self.phone_config,
            "settings": self.settings,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }