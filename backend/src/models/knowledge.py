"""
KnowledgeBase model with 18-category validation for business data extraction
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from ..database.connection import Base

# 18 knowledge categories as defined in spec
VALID_CATEGORIES = [
    'business_information', 'products_services', 'support_faq',
    'company_history', 'policies', 'processes_procedures',
    'events_news', 'technical_specs', 'pricing_billing',
    'inventory_stock', 'legal_compliance', 'partnerships',
    'marketing_promotions', 'training_education', 'quality_standards',
    'feedback_reviews', 'emergency_contact', 'custom_business_logic'
]

class KnowledgeBase(Base):
    """
    KnowledgeBase model for storing categorized business knowledge
    Each knowledge entry belongs to a specific agent and tenant
    """
    __tablename__ = 'knowledge_bases'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('voice_agents.id'), nullable=False)
    
    # Category must be one of the 18 valid categories
    category = Column(String(50), nullable=False)
    
    # JSON content for flexible knowledge storage
    content = Column(JSON, nullable=False)
    
    # Additional metadata for knowledge management
    meta_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    agent = relationship("VoiceAgent", back_populates="knowledge_bases")

    # Add constraint to validate category
    __table_args__ = (
        CheckConstraint(
            category.in_(VALID_CATEGORIES),
            name='valid_knowledge_category'
        ),
    )

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, category='{self.category}', agent_id={self.agent_id})>"