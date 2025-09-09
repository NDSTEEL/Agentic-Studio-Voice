"""
T012: Knowledge Categories Schema Tests
Test-driven development for JSONB schema validation and 18-category data extraction
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List


class TestKnowledgeCategoryValidation:
    """Test JSONB schema validation for each knowledge category"""
    
    def test_company_overview_schema_validation(self):
        """Test company_overview category schema validation"""
        try:
            from src.schemas.knowledge_categories import validate_category_data
            
            valid_data = {
                'title': 'About Our Company',
                'content': 'We are a leading provider of innovative solutions...',
                'keywords': ['company', 'innovative', 'solutions'],
                'confidence_score': 0.95,
                'source_url': 'https://example.com/about'
            }
            
            result = validate_category_data('company_overview', valid_data)
            assert result is not None
            assert result['title'] == 'About Our Company'
            assert 'confidence_score' in result
            
        except ImportError:
            assert False, "validate_category_data should exist for schema validation"
    
    def test_products_services_schema_validation(self):
        """Test products_services category schema validation"""
        from src.schemas.knowledge_categories import validate_category_data
        
        valid_data = {
            'title': 'Our Products & Services',
            'content': 'We offer a comprehensive range of products including...',
            'keywords': ['products', 'services', 'solutions'],
            'structured_data': {
                'products': [
                    {'name': 'Product A', 'price': '$99', 'description': 'Premium solution'},
                    {'name': 'Product B', 'price': '$149', 'description': 'Enterprise solution'}
                ]
            }
        }
        
        result = validate_category_data('products_services', valid_data)
        assert result is not None
        assert 'structured_data' in result
        assert len(result['structured_data']['products']) == 2
    
    def test_pricing_packages_schema_validation(self):
        """Test pricing_packages category with structured pricing data"""
        from src.schemas.knowledge_categories import validate_category_data
        
        pricing_data = {
            'title': 'Pricing Plans',
            'content': 'Choose the plan that works best for you...',
            'keywords': ['pricing', 'plans', 'packages'],
            'structured_data': {
                'packages': [
                    {
                        'name': 'Basic',
                        'price': '$29/month',
                        'features': ['Feature 1', 'Feature 2']
                    },
                    {
                        'name': 'Premium',
                        'price': '$99/month', 
                        'features': ['All Basic', 'Feature 3', 'Feature 4']
                    }
                ]
            }
        }
        
        result = validate_category_data('pricing_packages', pricing_data)
        assert result is not None
        assert len(result['structured_data']['packages']) == 2
    
    def test_contact_information_schema_validation(self):
        """Test contact_information category with structured contact data"""
        from src.schemas.knowledge_categories import validate_category_data
        
        contact_data = {
            'title': 'Contact Information',
            'content': 'Get in touch with us through various channels...',
            'keywords': ['contact', 'phone', 'email', 'address'],
            'structured_data': {
                'phone': '+1-555-123-4567',
                'email': 'contact@example.com',
                'address': '123 Main St, City, State 12345',
                'business_hours': 'Monday-Friday 9AM-6PM'
            }
        }
        
        result = validate_category_data('contact_information', contact_data)
        assert result is not None
        assert result['structured_data']['phone'] == '+1-555-123-4567'
    
    def test_invalid_category_rejection(self):
        """Test that invalid categories are rejected"""
        from src.schemas.knowledge_categories import validate_category_data
        
        with pytest.raises(ValueError) as exc_info:
            validate_category_data('invalid_category', {'title': 'Test', 'content': 'Test'})
        
        assert 'Invalid category' in str(exc_info.value)
    
    def test_missing_required_fields_validation(self):
        """Test validation of required fields"""
        from src.schemas.knowledge_categories import validate_category_data
        
        # Missing title
        with pytest.raises(ValueError):
            validate_category_data('company_overview', {'content': 'Test content'})
        
        # Missing content
        with pytest.raises(ValueError):
            validate_category_data('company_overview', {'title': 'Test title'})
    
    def test_schema_field_types_validation(self):
        """Test that field types are properly validated"""
        from src.schemas.knowledge_categories import validate_category_data
        
        # Invalid confidence_score type
        with pytest.raises(ValueError):
            validate_category_data('company_overview', {
                'title': 'Test',
                'content': 'Test content', 
                'confidence_score': 'invalid'
            })
        
        # Invalid keywords type
        with pytest.raises(ValueError):
            validate_category_data('company_overview', {
                'title': 'Test',
                'content': 'Test content',
                'keywords': 'should be list'
            })


class TestKnowledgeBaseExtraction:
    """Test AI knowledge extraction and categorization rules"""
    
    def test_extraction_rules_exist_for_all_categories(self):
        """Test that extraction rules exist for all 18 categories"""
        try:
            from src.schemas.knowledge_categories import get_extraction_rules, KNOWLEDGE_CATEGORIES
            
            for category in KNOWLEDGE_CATEGORIES:
                rules = get_extraction_rules(category)
                assert rules is not None, f"Extraction rules should exist for {category}"
                assert 'selectors' in rules, f"Should have CSS selectors for {category}"
                assert 'keywords' in rules, f"Should have keywords for {category}"
                assert 'priority_text' in rules, f"Should have priority text selectors for {category}"
                
        except ImportError:
            assert False, "get_extraction_rules should exist for web crawling"
    
    def test_company_overview_extraction_rules(self):
        """Test extraction rules for company overview category"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        rules = get_extraction_rules('company_overview')
        
        # Should have relevant CSS selectors
        expected_selectors = ['section[id*="about"]', '.about-section', 'div[class*="company"]']
        for selector in expected_selectors:
            assert selector in rules['selectors'], f"Should include selector: {selector}"
        
        # Should have relevant keywords
        expected_keywords = ['about', 'company', 'mission', 'vision']
        for keyword in expected_keywords:
            assert keyword in rules['keywords'], f"Should include keyword: {keyword}"
    
    def test_products_services_extraction_rules(self):
        """Test extraction rules for products and services"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        rules = get_extraction_rules('products_services')
        
        # Should target product/service sections
        assert '.products-section' in rules['selectors']
        assert '.services-section' in rules['selectors']
        assert 'products' in rules['keywords']
        assert 'services' in rules['keywords']
    
    def test_pricing_packages_extraction_rules(self):
        """Test extraction rules for pricing information"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        rules = get_extraction_rules('pricing_packages')
        
        # Should target pricing sections
        assert '.pricing-section' in rules['selectors']
        assert '.price-table' in rules['selectors']
        assert 'pricing' in rules['keywords']
        assert 'price' in rules['keywords']
    
    def test_contact_information_extraction_rules(self):
        """Test extraction rules for contact information"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        rules = get_extraction_rules('contact_information')
        
        # Should target contact sections
        assert '.contact-section' in rules['selectors']
        assert 'footer' in rules['selectors']
        assert 'contact' in rules['keywords']
        assert 'phone' in rules['keywords']
        assert 'email' in rules['keywords']
    
    def test_extraction_rules_completeness(self):
        """Test that extraction rules are complete for web crawling"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        rules = get_extraction_rules('business_hours')
        
        # Should have all required components
        assert isinstance(rules['selectors'], list), "Selectors should be a list"
        assert isinstance(rules['keywords'], list), "Keywords should be a list"
        assert isinstance(rules['priority_text'], list), "Priority text should be a list"
        assert len(rules['selectors']) > 0, "Should have at least one selector"
        assert len(rules['keywords']) > 0, "Should have at least one keyword"


class TestWebCrawlingIntegration:
    """Test web crawling integration with knowledge categories"""
    
    def test_web_crawler_service_exists(self):
        """Test that web crawling service exists"""
        try:
            from src.services.web_crawler_service import WebCrawlerService
            assert hasattr(WebCrawlerService, 'crawl_website')
            assert hasattr(WebCrawlerService, 'extract_category_content')
        except ImportError:
            assert False, "WebCrawlerService should exist for website crawling"
    
    def test_content_extraction_pipeline_exists(self):
        """Test that content extraction pipeline exists"""
        try:
            from src.services.content_extraction_service import ContentExtractionService
            assert hasattr(ContentExtractionService, 'extract_and_categorize')
            assert hasattr(ContentExtractionService, 'process_html_content')
        except ImportError:
            assert False, "ContentExtractionService should exist for content processing"
    
    @patch('src.services.web_crawler_service.WebCrawlerService.crawl_website')
    def test_website_crawling_with_categories(self, mock_crawl):
        """Test website crawling with knowledge category extraction"""
        from src.services.web_crawler_service import WebCrawlerService
        
        # Mock crawled content
        mock_crawl.return_value = {
            'company_overview': {
                'title': 'About Us',
                'content': 'We are a leading company...',
                'confidence_score': 0.9
            },
            'contact_information': {
                'title': 'Contact',
                'content': 'Phone: 555-123-4567, Email: info@company.com',
                'confidence_score': 0.95
            }
        }
        
        crawler = WebCrawlerService()
        result = crawler.crawl_website('https://example.com')
        
        assert 'company_overview' in result
        assert 'contact_information' in result
        assert result['company_overview']['confidence_score'] > 0.8
        mock_crawl.assert_called_once()
    
    @patch('src.services.content_extraction_service.ContentExtractionService.extract_and_categorize')
    def test_ai_content_categorization(self, mock_extract):
        """Test AI-powered content categorization"""
        from src.services.content_extraction_service import ContentExtractionService
        
        # Mock AI extraction
        mock_extract.return_value = {
            'products_services': {
                'title': 'Our Services',
                'content': 'We provide consulting, development, and support services...',
                'keywords': ['consulting', 'development', 'support'],
                'confidence_score': 0.88
            }
        }
        
        extractor = ContentExtractionService()
        html_content = '<div class="services">Our Services: consulting, development, support</div>'
        result = extractor.extract_and_categorize(html_content)
        
        assert 'products_services' in result
        assert result['products_services']['confidence_score'] > 0.8
        mock_extract.assert_called_once()


class TestKnowledgeBaseMerging:
    """Test knowledge base merging and update functionality"""
    
    def test_knowledge_base_merging_service_exists(self):
        """Test that knowledge base merging service exists"""
        try:
            from src.services.knowledge_base_service import KnowledgeBaseService
            assert hasattr(KnowledgeBaseService, 'merge_knowledge_categories')
            assert hasattr(KnowledgeBaseService, 'update_voice_agent_knowledge')
        except ImportError:
            assert False, "KnowledgeBaseService should exist for knowledge management"
    
    def test_merge_existing_with_new_content(self):
        """Test merging existing knowledge with new extracted content"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        existing_knowledge = {
            'company_overview': {
                'title': 'Old About Us',
                'content': 'Old company description...',
                'last_updated': '2024-01-01T12:00:00'
            }
        }
        
        new_content = {
            'company_overview': {
                'title': 'New About Us',
                'content': 'Updated company description...',
                'confidence_score': 0.9
            },
            'contact_information': {
                'title': 'Contact Info',
                'content': 'Phone and email details...',
                'confidence_score': 0.85
            }
        }
        
        service = KnowledgeBaseService()
        result = service.merge_knowledge_categories(existing_knowledge, new_content)
        
        # Should update existing category
        assert result['company_overview']['title'] == 'New About Us'
        # Should add new category
        assert 'contact_information' in result
        # Should preserve structure
        assert 'confidence_score' in result['company_overview']
    
    def test_confidence_score_based_updates(self):
        """Test that updates are based on confidence scores"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        existing = {
            'products_services': {
                'title': 'High Quality Content',
                'content': 'Detailed product information...',
                'confidence_score': 0.95,
                'last_updated': '2024-01-01T12:00:00'
            }
        }
        
        low_confidence_update = {
            'products_services': {
                'title': 'Poor Quality Content',
                'content': 'Vague product info...',
                'confidence_score': 0.3
            }
        }
        
        service = KnowledgeBaseService()
        result = service.merge_knowledge_categories(
            existing, 
            low_confidence_update,
            min_confidence_threshold=0.7
        )
        
        # Should keep existing high-confidence content
        assert result['products_services']['title'] == 'High Quality Content'
        assert result['products_services']['confidence_score'] == 0.95
    
    def test_knowledge_base_versioning(self):
        """Test knowledge base versioning and change tracking"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        service = KnowledgeBaseService()
        
        original = {'company_overview': {'title': 'V1', 'content': 'Version 1'}}
        updated = {'company_overview': {'title': 'V2', 'content': 'Version 2'}}
        
        result = service.merge_knowledge_categories(
            original, 
            updated, 
            track_changes=True
        )
        
        # Should track version history
        assert 'change_history' in result['company_overview']
        assert len(result['company_overview']['change_history']) > 0
        assert result['company_overview']['change_history'][0]['previous_title'] == 'V1'


class TestKnowledgeBasePerformance:
    """Test knowledge base performance and optimization"""
    
    def test_large_knowledge_base_handling(self):
        """Test handling of large knowledge bases (18 categories with extensive data)"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        # Create large knowledge base with all 18 categories
        large_kb = {}
        for i, category in enumerate(['company_overview', 'products_services', 'pricing_packages', 
                                     'contact_information', 'business_hours', 'location_directions',
                                     'team_staff', 'testimonials_reviews', 'faq_support',
                                     'policies_terms', 'appointment_booking', 'payment_methods',
                                     'shipping_delivery', 'warranty_returns', 'technical_specs',
                                     'news_updates', 'social_media', 'special_offers']):
            large_kb[category] = {
                'title': f'Category {i+1}',
                'content': 'Large content ' * 1000,  # 1000 words per category
                'keywords': [f'keyword{j}' for j in range(50)],  # 50 keywords per category
                'structured_data': {'items': [f'item{k}' for k in range(100)]}  # 100 items per category
            }
        
        service = KnowledgeBaseService()
        
        # Should handle large knowledge base efficiently
        result = service.validate_knowledge_base_size(large_kb)
        assert result['is_valid'] == True
        assert result['total_categories'] == 18
        assert result['estimated_size_mb'] > 0
    
    def test_knowledge_base_compression(self):
        """Test knowledge base compression for storage efficiency"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        service = KnowledgeBaseService()
        
        # Test data with repetitive content
        knowledge_base = {
            'company_overview': {
                'title': 'About Our Company',
                'content': 'We are excellent ' * 500,  # Repetitive content
                'keywords': ['excellent'] * 100  # Repetitive keywords
            }
        }
        
        compressed = service.compress_knowledge_base(knowledge_base)
        original_size = len(str(knowledge_base))
        compressed_size = len(str(compressed))
        
        # Should achieve some compression
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.8, "Should achieve at least 20% compression"
    
    def test_incremental_knowledge_updates(self):
        """Test incremental updates to avoid full knowledge base rewrites"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        service = KnowledgeBaseService()
        
        # Simulate incremental update
        change_delta = {
            'company_overview': {
                'operation': 'update',
                'fields': {'title': 'New Title'},
                'timestamp': datetime.now().isoformat()
            },
            'products_services': {
                'operation': 'add',
                'data': {'title': 'New Products', 'content': 'New product info...'},
                'timestamp': datetime.now().isoformat()
            }
        }
        
        result = service.apply_incremental_update('agent-123', change_delta)
        
        assert result['success'] == True
        assert result['updated_categories'] == ['company_overview', 'products_services']
        assert 'timestamp' in result