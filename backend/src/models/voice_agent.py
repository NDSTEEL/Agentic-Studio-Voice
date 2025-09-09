"""
Voice Agent Model
SQLAlchemy model for voice agents with 18-category knowledge structure and tenant isolation
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from src.database.connection import Base


class VoiceAgent(Base):
    """
    Voice Agent model with tenant isolation and structured knowledge base
    """
    __tablename__ = 'voice_agents'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation (foreign key)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    # Basic agent information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='inactive', nullable=False)  # active, inactive, training
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Knowledge base (18-category structure stored as JSONB)
    knowledge_base = Column(JSONB, nullable=False, default=dict)
    
    # Voice configuration (ElevenLabs settings)
    voice_config = Column(JSONB, nullable=True, default=dict)
    
    # Phone number integration (Twilio)
    phone_number = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="voice_agents")
    
    def __repr__(self):
        return f"<VoiceAgent(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
    
    def to_dict(self):
        """Convert voice agent to dictionary for API responses"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'is_active': self.is_active,
            'knowledge_base': self.knowledge_base,
            'voice_config': self.voice_config,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }