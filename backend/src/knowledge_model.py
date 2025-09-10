"""
Knowledge base model.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class KnowledgeBase:
    """Knowledge base data model."""
    kb_id: str
    name: str
    description: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "kb_id": self.kb_id,
            "name": self.name,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }