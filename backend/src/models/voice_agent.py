"""
Voice Agent Model
SQLAlchemy model for voice agents with 18-category knowledge base structure
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Import the base from tenant model
from .tenant import Base


class VoiceAgent(Base):
    """
    Voice Agent model with tenant isolation and 18-category knowledge structure
    
    Each voice agent belongs to a tenant and contains:
    - Basic agent configuration (name, phone, voice settings)
    - 18-category knowledge base structure
    - Status and activation state
    - ElevenLabs voice integration
    """
    __tablename__ = 'voice_agents'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant isolation (required for RLS)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Basic agent information
    name = Column(String(255), nullable=False, comment="Display name for the voice agent")
    description = Column(Text, nullable=True, comment="Optional description of agent purpose")
    
    # Voice configuration
    phone_number = Column(String(20), nullable=True, comment="Assigned phone number for voice calls")
    elevenlabs_voice_id = Column(String(255), nullable=True, comment="ElevenLabs voice ID for TTS")
    
    # Agent status and configuration
    status = Column(String(50), default='inactive', nullable=False, comment="Agent status: active, inactive, training")
    is_active = Column(Boolean, default=False, nullable=False, comment="Whether agent is currently active")
    
    # 18-category knowledge base (JSONB for PostgreSQL, JSON for other databases)
    knowledge_categories = Column(JSONB, default=dict, nullable=False, comment="18-category knowledge structure")
    
    # Additional configuration (voice settings, behavior config, etc.)
    configuration = Column(JSONB, default=dict, nullable=False, comment="Agent configuration and voice settings")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="voice_agents")
    knowledge_bases = relationship("KnowledgeBase", back_populates="agent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VoiceAgent(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    @property
    def agent_id(self):
        """Alias for id to match API response schema"""
        return str(self.id)
    
    @property
    def knowledge_base(self):
        """Get knowledge_categories as knowledge_base for API compatibility"""
        return self.knowledge_categories or {}
    
    @knowledge_base.setter
    def knowledge_base(self, value):
        """Set knowledge_categories via knowledge_base property"""
        self.knowledge_categories = value or {}
    
    @property
    def voice_config(self):
        """Get voice configuration from configuration field"""
        config = self.configuration or {}
        return config.get('voice_config', {})
    
    @voice_config.setter
    def voice_config(self, value):
        """Set voice configuration in configuration field"""
        if not self.configuration:
            self.configuration = {}
        self.configuration['voice_config'] = value or {}
    
    def get_knowledge_categories(self):
        """Get the 18-category knowledge structure"""
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        
        categories = self.knowledge_categories or {}
        
        # Ensure all 18 categories are present (with None for empty categories)
        complete_categories = {}
        for category in KNOWLEDGE_CATEGORIES:
            complete_categories[category] = categories.get(category, None)
        
        return complete_categories
    
    def update_knowledge_category(self, category_name: str, data: dict):
        """Update a specific knowledge category"""
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES, validate_category_data
        
        if category_name not in KNOWLEDGE_CATEGORIES:
            raise ValueError(f"Invalid knowledge category: {category_name}")
        
        # Validate the category data
        validated_data = validate_category_data(category_name, data)
        
        # Update the knowledge categories
        if not self.knowledge_categories:
            self.knowledge_categories = {}
        
        self.knowledge_categories[category_name] = validated_data
        
        # Mark the field as dirty for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'knowledge_categories')
    
    def activate(self):
        """Activate the voice agent"""
        self.status = 'active'
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the voice agent"""
        self.status = 'inactive'
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert voice agent to dictionary representation"""
        return {
            'id': str(self.id),
            'agent_id': str(self.id),  # API compatibility
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'description': self.description,
            'phone_number': self.phone_number,
            'status': self.status,
            'is_active': self.is_active,
            'knowledge_base': self.knowledge_base,
            'voice_config': self.voice_config,
            'elevenlabs_voice_id': self.elevenlabs_voice_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }