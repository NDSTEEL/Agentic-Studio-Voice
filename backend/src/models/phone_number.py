"""
PhoneNumber Model
SQLAlchemy model for managing phone numbers with tenant isolation
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Use the same Base as other models
from .tenant import Base


class PhoneNumber(Base):
    """
    PhoneNumber model for tenant-isolated phone number management
    
    Stores provisioned phone numbers with their configuration and status.
    Each phone number belongs to a specific tenant for multi-tenant isolation.
    """
    __tablename__ = 'phone_numbers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant relationship for multi-tenant isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, comment="Tenant owner of this phone number")
    
    # Phone number details
    phone_number = Column(String(20), nullable=False, comment="Phone number in E.164 format")
    phone_sid = Column(String(255), nullable=True, comment="Twilio SID for this phone number")
    friendly_name = Column(String(255), nullable=True, comment="Human-readable name for the number")
    
    # Status and configuration
    status = Column(String(20), default='active', nullable=False, comment="Phone number status (active/inactive/provisioning/error)")
    capabilities = Column(JSON, nullable=True, comment="Voice/SMS/MMS capabilities")
    configuration = Column(JSON, nullable=True, comment="Webhook URLs and other configuration")
    
    # Assignment
    agent_id = Column(UUID(as_uuid=True), nullable=True, comment="Assigned voice agent ID (if any)")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, nullable=True, comment="Last call or message activity")
    
    # Relationships
    tenant = relationship("Tenant", back_populates="phone_numbers")
    
    def __repr__(self):
        return f"<PhoneNumber(id={self.id}, phone_number='{self.phone_number}', tenant_id={self.tenant_id})>"
    
    def __str__(self):
        return f"{self.phone_number} ({self.friendly_name or 'No name'})"
    
    def to_dict(self):
        """Convert phone number to dictionary representation"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'phone_number': self.phone_number,
            'phone_sid': self.phone_sid,
            'friendly_name': self.friendly_name,
            'status': self.status,
            'capabilities': self.capabilities or {},
            'configuration': self.configuration or {},
            'agent_id': str(self.agent_id) if self.agent_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }