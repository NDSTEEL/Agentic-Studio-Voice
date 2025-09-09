"""
Tenant model with Row-Level Security for multi-tenant isolation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from typing import Optional, List
from src.database.connection import Base


class TenantStatus(str, Enum):
    """Valid tenant status values"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Tenant(Base):
    """
    Tenant model for multi-tenant SaaS architecture
    Each tenant represents a separate business using the voice agent platform
    """
    __tablename__ = 'tenants'

    id = Column(String, primary_key=True, default=lambda: f"tenant-{uuid.uuid4().hex[:8]}")
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    status = Column(String, nullable=False, default=TenantStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (disabled for now to avoid circular imports)
    # voice_agents = relationship("VoiceAgent", back_populates="tenant", cascade="all, delete-orphan")
    # knowledge_bases = relationship("KnowledgeBase", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}', status='{self.status}')>"


class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant"""
    name: str = Field(..., min_length=1, max_length=255)
    subdomain: Optional[str] = Field(None, max_length=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Tenant name cannot be empty')
        return v.strip()


class TenantUpdateRequest(BaseModel):
    """Request model for updating tenant data"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[TenantStatus] = None
    subdomain: Optional[str] = Field(None, max_length=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Tenant name cannot be empty')
        return v.strip() if v else v


class TenantResponse(BaseModel):
    """Response model for tenant data"""
    id: str
    name: str
    status: str
    subdomain: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Response model for tenant list with pagination"""
    tenants: List[TenantResponse]
    total: int
    page: int
    limit: int
    
    model_config = ConfigDict(from_attributes=True)