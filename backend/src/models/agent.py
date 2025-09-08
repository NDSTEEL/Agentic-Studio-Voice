"""
VoiceAgent model with tenant isolation for multi-tenant voice agent platform
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from ..database.connection import Base

class AgentStatus(enum.Enum):
    """Agent status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

class VoiceAgent(Base):
    """
    VoiceAgent model for multi-tenant voice agent platform
    Each agent belongs to a tenant and handles voice interactions
    """
    __tablename__ = 'voice_agents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    elevenlabs_voice_id = Column(String(255), nullable=False)
    
    # JSONB field for 18 knowledge categories
    knowledge_categories = Column(JSON, default=dict)
    
    # Agent configuration (prompts, settings, etc.)
    configuration = Column(JSON, default=dict)
    
    # Agent status
    status = Column(Enum(AgentStatus), default=AgentStatus.DRAFT, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="voice_agents")
    knowledge_bases = relationship("KnowledgeBase", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VoiceAgent(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"