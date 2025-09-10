"""
Temporary fix for models import until the I/O issues are resolved.
This creates the missing model classes for imports.
"""

# Import the actual model classes
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from tenant_model import Tenant
    from knowledge_model import KnowledgeBase
    from agent_config_model import AgentConfig
    from call_record_model import CallRecord
except ImportError as e:
    # If files don't exist, create minimal model classes
    from dataclasses import dataclass
    from typing import Dict, Any, Optional
    from datetime import datetime
    
    @dataclass
    class Tenant:
        tenant_id: str
        name: str
        description: Optional[str] = None
        
        def to_dict(self) -> Dict[str, Any]:
            return {"tenant_id": self.tenant_id, "name": self.name, "description": self.description}
    
    @dataclass 
    class KnowledgeBase:
        kb_id: str
        name: str
        tenant_id: str
        
        def to_dict(self) -> Dict[str, Any]:
            return {"kb_id": self.kb_id, "name": self.name, "tenant_id": self.tenant_id}
    
    @dataclass
    class AgentConfig:
        agent_id: str
        tenant_id: str
        name: str
        
        def to_dict(self) -> Dict[str, Any]:
            return {"agent_id": self.agent_id, "tenant_id": self.tenant_id, "name": self.name}
    
    @dataclass
    class CallRecord:
        call_id: str
        agent_id: str
        tenant_id: str
        
        def to_dict(self) -> Dict[str, Any]:
            return {"call_id": self.call_id, "agent_id": self.agent_id, "tenant_id": self.tenant_id}

# Make available for import
__all__ = ['Tenant', 'KnowledgeBase', 'AgentConfig', 'CallRecord']