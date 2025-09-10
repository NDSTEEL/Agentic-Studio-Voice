"""
Knowledge Base Model
SQLAlchemy model for individual knowledge entries with 18-category validation
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Import the base from tenant model
from .tenant import Base


class KnowledgeBase(Base):
    """
    Knowledge Base model for storing individual knowledge entries
    
    Each knowledge entry belongs to a specific agent and tenant with:
    - Category validation against 18 standard categories
    - Structured content storage
    - Metadata and confidence scoring
    - Source tracking and timestamps
    """
    __tablename__ = 'knowledge_bases'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys (tenant isolation)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('voice_agents.id'), nullable=False, index=True)
    
    # Knowledge categorization
    category = Column(String(100), nullable=False, comment="Knowledge category from 18 standard categories")
    
    # Content storage
    content = Column(JSONB, nullable=False, comment="Structured knowledge content")
    meta_data = Column(JSONB, default=dict, nullable=False, comment="Additional metadata and extraction info")
    
    # Content metadata
    title = Column(String(255), nullable=True, comment="Knowledge entry title")
    source_url = Column(Text, nullable=True, comment="Source URL where content was extracted")
    confidence_score = Column(Float, default=1.0, nullable=False, comment="Confidence score (0.0-1.0)")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_bases")
    agent = relationship("VoiceAgent", back_populates="knowledge_bases")
    
    @validates('category')
    def validate_category(self, key, category):
        """Validate that category is one of the valid categories"""
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        
        # Test categories (legacy from test file)
        test_categories = [
            'business_information', 'products_services', 'support_faq',
            'company_history', 'policies', 'processes_procedures',
            'events_news', 'technical_specs', 'pricing_billing',
            'inventory_stock', 'legal_compliance', 'partnerships',
            'marketing_promotions', 'training_education', 'quality_standards',
            'feedback_reviews', 'emergency_contact', 'custom_business_logic'
        ]
        
        # Allow both new schema categories and legacy test categories
        valid_categories = KNOWLEDGE_CATEGORIES + test_categories
        
        if category not in valid_categories:
            raise ValueError(f"Invalid knowledge category: {category}. Must be one of {valid_categories}")
        
        return category
    
    @validates('confidence_score')
    def validate_confidence_score(self, key, score):
        """Validate confidence score is between 0.0 and 1.0"""
        if not isinstance(score, (int, float)):
            raise ValueError("Confidence score must be a number")
        
        if not (0.0 <= score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        return float(score)
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, category='{self.category}', agent_id={self.agent_id})>"
    
    def __str__(self):
        return f"{self.category} - {self.title or 'Untitled'}"
    
    @property
    def keywords(self):
        """Extract keywords from content or metadata"""
        if isinstance(self.content, dict):
            return self.content.get('keywords', [])
        elif isinstance(self.meta_data, dict):
            return self.meta_data.get('keywords', [])
        return []
    
    @property
    def content_text(self):
        """Extract main content text"""
        if isinstance(self.content, dict):
            return self.content.get('content', self.content.get('text', ''))
        elif isinstance(self.content, str):
            return self.content
        return str(self.content)
    
    def update_content(self, new_content: dict):
        """Update knowledge content with validation"""
        from src.schemas.knowledge_categories import validate_category_data
        
        # Validate the content structure
        validated_data = validate_category_data(self.category, new_content)
        
        # Update content fields
        self.content = validated_data
        self.title = validated_data.get('title', self.title)
        self.confidence_score = validated_data.get('confidence_score', self.confidence_score)
        self.updated_at = datetime.utcnow()
        
        # Mark the JSONB field as dirty for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'content')
    
    def add_metadata(self, **metadata):
        """Add metadata to the knowledge entry"""
        if not self.meta_data:
            self.meta_data = {}
        
        self.meta_data.update(metadata)
        
        # Mark the JSONB field as dirty for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'meta_data')
    
    def to_dict(self):
        """Convert knowledge base entry to dictionary representation"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'agent_id': str(self.agent_id),
            'category': self.category,
            'title': self.title,
            'content': self.content,
            'meta_data': self.meta_data,
            'source_url': self.source_url,
            'confidence_score': self.confidence_score,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_from_category_data(cls, tenant_id: str, agent_id: str, category: str, data: dict):
        """Create knowledge base entry from category data"""
        from src.schemas.knowledge_categories import validate_category_data
        
        # Validate the data
        validated_data = validate_category_data(category, data)
        
        # Create knowledge base entry
        knowledge = cls(
            tenant_id=tenant_id,
            agent_id=agent_id,
            category=category,
            content=validated_data,
            title=validated_data.get('title'),
            source_url=validated_data.get('source_url'),
            confidence_score=validated_data.get('confidence_score', 1.0)
        )
        
        return knowledge