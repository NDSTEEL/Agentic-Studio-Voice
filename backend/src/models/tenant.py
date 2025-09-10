"""
Tenant Model
SQLAlchemy model for multi-tenant isolation
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class Tenant(Base):
    """
    Tenant model for multi-tenant SaaS architecture
    
    Each tenant represents a separate customer/organization with complete data isolation.
    All other models should reference tenant_id for Row Level Security (RLS).
    """
    __tablename__ = 'tenants'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant identification
    name = Column(String(255), nullable=False, comment="Tenant organization name")
    subdomain = Column(String(63), unique=True, nullable=False, comment="Unique subdomain for tenant")
    
    # Tenant metadata
    description = Column(Text, nullable=True, comment="Optional tenant description")
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether tenant is active")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    voice_agents = relationship("VoiceAgent", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant", cascade="all, delete-orphan")
    phone_numbers = relationship("PhoneNumber", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}')>"
    
    def __str__(self):
        return f"{self.name} ({self.subdomain})"
    
    @property
    def agent_count(self):
        """Get the number of voice agents for this tenant"""
        return len(self.voice_agents) if self.voice_agents else 0
    
    def to_dict(self):
        """Convert tenant to dictionary representation"""
        return {
            'id': str(self.id),
            'name': self.name,
            'subdomain': self.subdomain,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'agent_count': self.agent_count
        }