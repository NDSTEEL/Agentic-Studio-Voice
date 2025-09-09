"""
Voice Agent API Schemas
Pydantic models for voice agent API requests and responses
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID

from src.schemas.knowledge_categories import KnowledgeCategoriesSchema, KNOWLEDGE_CATEGORIES


class VoiceConfigSchema(BaseModel):
    """Voice configuration schema for ElevenLabs integration"""
    voice_id: Optional[str] = None
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    stability: float = Field(default=0.75, ge=0.0, le=1.0)
    clarity: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @validator('voice_id')
    def validate_voice_id(cls, v):
        if v and not v.strip():
            return None
        return v


class VoiceAgentCreateRequest(BaseModel):
    """Request model for creating a new voice agent"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    knowledge_base: Optional[Dict[str, Any]] = Field(default_factory=dict)
    voice_config: Optional[VoiceConfigSchema] = Field(default_factory=VoiceConfigSchema)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Voice agent name cannot be empty')
        return v.strip()
    
    @validator('knowledge_base')
    def validate_knowledge_base(cls, v):
        if not v:
            return {}
        
        # Validate that all categories are valid
        for category in v.keys():
            if category not in KNOWLEDGE_CATEGORIES:
                raise ValueError(f'Invalid knowledge category: {category}')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Customer Service Agent",
                "description": "AI assistant for customer support inquiries",
                "knowledge_base": {
                    "company_overview": {
                        "title": "About Our Company",
                        "content": "We provide excellent customer service...",
                        "keywords": ["company", "service", "support"]
                    }
                },
                "voice_config": {
                    "voice_id": "elevenlabs_voice_123",
                    "speaking_rate": 1.0,
                    "pitch": 0.0
                }
            }
        }


class VoiceAgentUpdateRequest(BaseModel):
    """Request model for updating a voice agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    knowledge_base: Optional[Dict[str, Any]] = None
    voice_config: Optional[VoiceConfigSchema] = None
    status: Optional[str] = Field(None, pattern='^(active|inactive|training)$')
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Voice agent name cannot be empty')
        return v.strip() if v else v
    
    @validator('knowledge_base')
    def validate_knowledge_base(cls, v):
        if v is None:
            return v
        
        # Validate that all categories are valid
        for category in v.keys():
            if category not in KNOWLEDGE_CATEGORIES:
                raise ValueError(f'Invalid knowledge category: {category}')
        
        return v


class VoiceAgentResponse(BaseModel):
    """Response model for voice agent data"""
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    status: str
    is_active: bool
    knowledge_base: Dict[str, Any] = Field(default_factory=dict)
    voice_config: Dict[str, Any] = Field(default_factory=dict)
    phone_number: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    
    @validator('created_at', 'updated_at')
    def format_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "tenant-12345678",
                "name": "Customer Service Agent",
                "description": "AI assistant for customer support",
                "status": "active",
                "is_active": True,
                "knowledge_base": {
                    "company_overview": {
                        "title": "About Our Company",
                        "content": "We provide excellent customer service...",
                        "keywords": ["company", "service", "support"]
                    }
                },
                "voice_config": {
                    "voice_id": "elevenlabs_voice_123",
                    "speaking_rate": 1.0,
                    "pitch": 0.0
                },
                "phone_number": "+1-555-123-4567",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }


class VoiceAgentListResponse(BaseModel):
    """Response model for voice agent list"""
    agents: List[VoiceAgentResponse]
    total: int
    page: int = Field(default=1)
    limit: int = Field(default=10)
    
    class Config:
        schema_extra = {
            "example": {
                "agents": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "tenant_id": "tenant-12345678",
                        "name": "Customer Service Agent",
                        "status": "active",
                        "is_active": True,
                        "created_at": "2024-01-01T12:00:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 10
            }
        }


class VoiceAgentActivationRequest(BaseModel):
    """Request model for activating/deactivating voice agents"""
    active: bool = Field(..., description="True to activate, False to deactivate")


class VoiceAgentKnowledgeUpdateRequest(BaseModel):
    """Request model for updating voice agent knowledge base"""
    knowledge_base: Dict[str, Any] = Field(..., description="Updated knowledge base data")
    
    @validator('knowledge_base')
    def validate_knowledge_base(cls, v):
        # Validate that all categories are valid
        for category in v.keys():
            if category not in KNOWLEDGE_CATEGORIES:
                raise ValueError(f'Invalid knowledge category: {category}')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "knowledge_base": {
                    "company_overview": {
                        "title": "Updated Company Info",
                        "content": "We are a leading provider...",
                        "keywords": ["company", "leading", "provider"]
                    },
                    "products_services": {
                        "title": "Our Services",
                        "content": "We offer comprehensive solutions...",
                        "keywords": ["services", "solutions", "comprehensive"]
                    }
                }
            }
        }