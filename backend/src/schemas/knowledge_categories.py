"""
Knowledge Categories Schema
18-category knowledge base structure with validation and extraction rules
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


# 18 Standard Knowledge Categories for Voice Agents
KNOWLEDGE_CATEGORIES = [
    'company_overview',      # About the company, mission, values
    'products_services',     # Products and services offered
    'pricing_packages',      # Pricing information and packages
    'contact_information',   # Contact details, addresses, emails
    'business_hours',        # Operating hours, availability
    'location_directions',   # Physical locations and directions
    'team_staff',           # Team members, staff information
    'testimonials_reviews',  # Customer testimonials and reviews
    'faq_support',          # Frequently asked questions and support
    'policies_terms',       # Terms of service, privacy policy
    'appointment_booking',   # Booking procedures and availability
    'payment_methods',      # Accepted payment methods
    'shipping_delivery',    # Shipping and delivery information
    'warranty_returns',     # Warranty and return policies
    'technical_specs',      # Technical specifications
    'news_updates',         # Company news and updates
    'social_media',         # Social media links and presence
    'special_offers'        # Promotions and special offers
]


class KnowledgeCategoryData(BaseModel):
    """Individual knowledge category data structure"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    keywords: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_url: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    
    @validator('keywords')
    def validate_keywords(cls, v):
        """Ensure keywords are non-empty strings"""
        return [keyword.strip() for keyword in v if keyword and keyword.strip()]


class KnowledgeCategoriesSchema(BaseModel):
    """Complete 18-category knowledge base schema"""
    company_overview: Optional[KnowledgeCategoryData] = None
    products_services: Optional[KnowledgeCategoryData] = None
    pricing_packages: Optional[KnowledgeCategoryData] = None
    contact_information: Optional[KnowledgeCategoryData] = None
    business_hours: Optional[KnowledgeCategoryData] = None
    location_directions: Optional[KnowledgeCategoryData] = None
    team_staff: Optional[KnowledgeCategoryData] = None
    testimonials_reviews: Optional[KnowledgeCategoryData] = None
    faq_support: Optional[KnowledgeCategoryData] = None
    policies_terms: Optional[KnowledgeCategoryData] = None
    appointment_booking: Optional[KnowledgeCategoryData] = None
    payment_methods: Optional[KnowledgeCategoryData] = None
    shipping_delivery: Optional[KnowledgeCategoryData] = None
    warranty_returns: Optional[KnowledgeCategoryData] = None
    technical_specs: Optional[KnowledgeCategoryData] = None
    news_updates: Optional[KnowledgeCategoryData] = None
    social_media: Optional[KnowledgeCategoryData] = None
    special_offers: Optional[KnowledgeCategoryData] = None
    
    def get_populated_categories(self) -> List[str]:
        """Get list of categories that have data"""
        populated = []
        for category in KNOWLEDGE_CATEGORIES:
            if getattr(self, category) is not None:
                populated.append(category)
        return populated


def validate_knowledge_category(category_name: str, data: Dict[str, Any]) -> KnowledgeCategoryData:
    """
    Validate individual knowledge category data
    """
    if category_name not in KNOWLEDGE_CATEGORIES:
        raise ValueError(f"Invalid category: {category_name}. Must be one of {KNOWLEDGE_CATEGORIES}")
    
    return KnowledgeCategoryData(**data)


def validate_category_data(category_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and return category data as dictionary
    Enhanced validation with structured data support
    """
    if category_name not in KNOWLEDGE_CATEGORIES:
        raise ValueError(f"Invalid category: {category_name}. Must be one of {KNOWLEDGE_CATEGORIES}")
    
    # Validate required fields
    if 'title' not in data or not data['title']:
        raise ValueError("Title is required for knowledge category")
    
    if 'content' not in data or not data['content']:
        raise ValueError("Content is required for knowledge category")
    
    # Validate field types
    if 'confidence_score' in data:
        if not isinstance(data['confidence_score'], (int, float)):
            raise ValueError("confidence_score must be a number")
        if not (0.0 <= data['confidence_score'] <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
    
    if 'keywords' in data:
        if not isinstance(data['keywords'], list):
            raise ValueError("keywords must be a list")
    
    # Create validated category data
    validated_data = {
        'title': str(data['title']),
        'content': str(data['content']),
        'keywords': data.get('keywords', []),
        'confidence_score': data.get('confidence_score', 1.0),
        'source_url': data.get('source_url'),
        'last_updated': data.get('last_updated', datetime.now().isoformat()),
        'structured_data': data.get('structured_data', {})
    }
    
    return validated_data


def get_extraction_rules(category_name: str) -> Dict[str, Any]:
    """
    Get web crawling extraction rules for each knowledge category
    """
    if category_name not in KNOWLEDGE_CATEGORIES:
        raise ValueError(f"Invalid category: {category_name}")
    
    # Define extraction rules for each category
    extraction_rules = {
        'company_overview': {
            'selectors': [
                'section[id*="about"]',
                '.about-section',
                'div[class*="company"]',
                'main .hero-section',
                '[data-section="about"]'
            ],
            'keywords': ['about', 'company', 'mission', 'vision', 'values', 'story', 'history'],
            'priority_text': ['h1', 'h2', '.hero-title', '.main-heading']
        },
        'products_services': {
            'selectors': [
                '.products-section',
                '.services-section',
                '[id*="product"]',
                '[id*="service"]',
                '.catalog'
            ],
            'keywords': ['products', 'services', 'offerings', 'solutions', 'catalog'],
            'priority_text': ['h2', 'h3', '.product-title', '.service-name']
        },
        'pricing_packages': {
            'selectors': [
                '.pricing-section',
                '.packages',
                '[id*="pricing"]',
                '.price-table',
                '.subscription'
            ],
            'keywords': ['pricing', 'price', 'cost', 'packages', 'plans', 'subscription'],
            'priority_text': ['.price', '.cost', 'h3']
        },
        'contact_information': {
            'selectors': [
                '.contact-section',
                'footer',
                '[id*="contact"]',
                '.contact-info',
                '.footer-contact'
            ],
            'keywords': ['contact', 'phone', 'email', 'address', 'location'],
            'priority_text': ['.phone', '.email', '.address']
        },
        'business_hours': {
            'selectors': [
                '.hours',
                '.business-hours',
                '[id*="hours"]',
                '.schedule',
                '.opening-hours'
            ],
            'keywords': ['hours', 'open', 'closed', 'schedule', 'availability'],
            'priority_text': ['.hours', '.schedule']
        }
        # Additional categories would follow the same pattern...
    }
    
    # Return extraction rules for the specified category, or default rules if not found
    return extraction_rules.get(category_name, {
        'selectors': ['main', '.main-content', 'article'],
        'keywords': [category_name.replace('_', ' ')],
        'priority_text': ['h1', 'h2', 'h3']
    })


def get_empty_knowledge_base() -> Dict[str, Optional[Dict]]:
    """
    Get empty knowledge base structure with all 18 categories
    """
    return {category: None for category in KNOWLEDGE_CATEGORIES}


def merge_knowledge_categories(
    existing: Dict[str, Any], 
    new_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge new knowledge category data with existing data
    """
    merged = existing.copy()
    
    for category in KNOWLEDGE_CATEGORIES:
        if category in new_data and new_data[category] is not None:
            merged[category] = new_data[category]
    
    return merged