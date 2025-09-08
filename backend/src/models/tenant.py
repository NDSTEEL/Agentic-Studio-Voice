"""
Tenant model with Row-Level Security for multi-tenant isolation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import relationship
from ..database.connection import Base

class Tenant(Base):
    """
    Tenant model for multi-tenant SaaS architecture
    Each tenant represents a separate business using the voice agent platform
    """
    __tablename__ = 'tenants'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    voice_agents = relationship("VoiceAgent", back_populates="tenant", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', subdomain='{self.subdomain}')>"