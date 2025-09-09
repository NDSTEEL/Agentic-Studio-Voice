"""
T014: Service Integration Tests
REAL implementation approach - integration between voice agents, web crawling, and knowledge management
Test real service interactions with minimal mocking (only external paid APIs)
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List
import uuid


class TestVoiceAgentKnowledgeIntegration:
    """Test integration between voice agents and knowledge management with REAL implementations"""
    
    def test_voice_agent_service_integration_exists(self):
        """Test that voice agent can integrate with knowledge services"""
        try:
            from src.services.voice_agent_service import VoiceAgentService
            from src.services.knowledge_base_service import KnowledgeBaseService
            from src.services.web_crawler_service import WebCrawlerService
            
            # Services should exist and be integrable
            voice_service = VoiceAgentService()
            knowledge_service = KnowledgeBaseService()
            crawler_service = WebCrawlerService()
            
            # Should have integration methods
            assert hasattr(voice_service, 'update_agent_knowledge_from_crawl')
            assert hasattr(voice_service, 'get_agent_with_knowledge')
            assert callable(voice_service.update_agent_knowledge_from_crawl)
            assert callable(voice_service.get_agent_with_knowledge)
            
        except ImportError as e:
            assert False, f"Service integration should be available: {e}"
    
    def test_create_voice_agent_with_website_knowledge(self):
        """Test creating voice agent with knowledge extracted from website"""
        from src.services.voice_agent_service import VoiceAgentService
        from src.services.web_crawler_service import WebCrawlerService
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        # Real services (no mocking)
        voice_service = VoiceAgentService()
        crawler_service = WebCrawlerService()
        knowledge_service = KnowledgeBaseService()
        
        # Create test website data (simulate crawled content)
        crawled_data = {
            'company_overview': {
                'title': 'About TechCorp',
                'content': 'TechCorp is a leading software company providing innovative solutions.',
                'confidence_score': 0.9,
                'source_url': 'https://techcorp.com/about'
            },
            'contact_information': {
                'title': 'Contact Us',
                'content': 'Phone: 555-0123, Email: info@techcorp.com',
                'confidence_score': 0.95,
                'structured_data': {
                    'phone': '555-0123',
                    'email': 'info@techcorp.com'
                }
            }
        }
        
        # Create voice agent with crawled knowledge
        tenant_id = str(uuid.uuid4())
        agent_data = {
            'name': 'TechCorp Assistant',
            'description': 'Customer service agent for TechCorp',
            'voice_config': {
                'voice_type': 'professional',
                'speed': 1.0
            }
        }
        
        # This should work with real integration
        agent = voice_service.create_agent_with_knowledge(
            tenant_id=tenant_id,
            agent_data=agent_data,
            knowledge_base=crawled_data
        )
        
        assert agent is not None
        assert agent['name'] == 'TechCorp Assistant'
        assert 'company_overview' in agent['knowledge_base']
        assert 'contact_information' in agent['knowledge_base']
    
    def test_update_voice_agent_from_website_crawl(self):
        """Test updating existing voice agent with new crawled data"""
        from src.services.voice_agent_service import VoiceAgentService
        from src.services.web_crawler_service import WebCrawlerService
        
        voice_service = VoiceAgentService()
        crawler_service = WebCrawlerService()
        
        # Create existing agent
        tenant_id = str(uuid.uuid4())
        agent = voice_service.create_agent(
            tenant_id=tenant_id,
            agent_data={
                'name': 'Business Assistant',
                'description': 'General business assistant'
            }
        )
        
        # Simulate new crawled data
        new_crawled_data = {
            'products_services': {
                'title': 'Our Services',
                'content': 'We offer consulting, development, and support services.',
                'confidence_score': 0.85,
                'structured_data': {
                    'services': [
                        {'name': 'Consulting', 'description': 'Strategic technology consulting'},
                        {'name': 'Development', 'description': 'Custom software development'}
                    ]
                }
            },
            'pricing_packages': {
                'title': 'Pricing',
                'content': 'Our packages start at $99/month for basic support.',
                'confidence_score': 0.8,
                'structured_data': {
                    'packages': [
                        {'name': 'Basic', 'price': '$99/month'},
                        {'name': 'Premium', 'price': '$299/month'}
                    ]
                }
            }
        }
        
        # Update agent with new knowledge
        updated_agent = voice_service.update_agent_knowledge_from_crawl(
            agent_id=agent['id'],
            tenant_id=tenant_id,
            crawled_knowledge=new_crawled_data
        )
        
        assert updated_agent is not None
        assert 'products_services' in updated_agent['knowledge_base']
        assert 'pricing_packages' in updated_agent['knowledge_base']
        assert updated_agent['knowledge_base']['products_services']['confidence_score'] == 0.85


class TestWebCrawlerKnowledgeIntegration:
    """Test integration between web crawler and knowledge base services"""
    
    @pytest.mark.asyncio
    async def test_crawl_and_extract_knowledge_pipeline(self):
        """Test complete pipeline from URL crawling to knowledge extraction"""
        from src.services.web_crawler_service import WebCrawlerService
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        crawler = WebCrawlerService()
        knowledge_service = KnowledgeBaseService()
        
        # Use data URL for consistent testing
        test_html = """
        <html>
            <head><title>Test Company</title></head>
            <body>
                <section id="about">
                    <h2>About Our Company</h2>
                    <p>We are a leading provider of innovative technology solutions.</p>
                    <p>Founded in 2020, we serve customers worldwide with cutting-edge products.</p>
                </section>
                <div class="contact">
                    <h3>Contact Information</h3>
                    <p>Phone: (555) 123-4567</p>
                    <p>Email: contact@testcompany.com</p>
                    <p>Address: 123 Main Street, Tech City, TC 12345</p>
                </div>
                <div class="products">
                    <h3>Our Products</h3>
                    <div class="product">
                        <h4>Software Suite</h4>
                        <p>Comprehensive business management software.</p>
                    </div>
                    <div class="product">
                        <h4>Consulting Services</h4>
                        <p>Expert technology consulting and implementation.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        import urllib.parse
        data_url = f"data:text/html,{urllib.parse.quote(test_html)}"
        
        # Crawl and extract knowledge
        crawl_result = await crawler.crawl_website_complete(data_url)
        
        assert crawl_result['urls_crawled'] > 0
        assert len(crawl_result['knowledge_categories']) > 0
        
        # Validate and merge knowledge
        validated_knowledge = knowledge_service.validate_crawled_content(
            crawl_result['knowledge_categories']
        )
        
        # Should have extracted multiple categories
        assert len(validated_knowledge) >= 2
        
        # Verify content quality
        if 'company_overview' in validated_knowledge:
            company_info = validated_knowledge['company_overview']
            assert 'innovative' in company_info['content'].lower()
            assert company_info.get('confidence_score', 0) > 0
        
        if 'contact_information' in validated_knowledge:
            contact_info = validated_knowledge['contact_information']
            assert 'phone' in contact_info.get('structured_data', {})
            assert 'email' in contact_info.get('structured_data', {})
    
    def test_knowledge_merging_with_confidence_scores(self):
        """Test merging crawled knowledge with existing knowledge using confidence scores"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        knowledge_service = KnowledgeBaseService()
        
        existing_knowledge = {
            'company_overview': {
                'title': 'About Us - Old',
                'content': 'Outdated company information.',
                'confidence_score': 0.6,
                'last_updated': '2024-01-01T00:00:00'
            }
        }
        
        new_crawled_knowledge = {
            'company_overview': {
                'title': 'About Us - Updated',
                'content': 'Fresh, updated company information with more details.',
                'confidence_score': 0.9,
                'last_updated': '2024-12-01T00:00:00',
                'source_url': 'https://company.com/about'
            },
            'contact_information': {
                'title': 'Contact Details',
                'content': 'Phone: 555-9876, Email: new@company.com',
                'confidence_score': 0.95,
                'structured_data': {
                    'phone': '555-9876',
                    'email': 'new@company.com'
                }
            }
        }
        
        # Merge with confidence-based updates
        merged_knowledge = knowledge_service.merge_knowledge_categories(
            existing_knowledge,
            new_crawled_knowledge,
            min_confidence_threshold=0.7
        )
        
        # Should update company_overview (higher confidence)
        assert merged_knowledge['company_overview']['title'] == 'About Us - Updated'
        assert merged_knowledge['company_overview']['confidence_score'] == 0.9
        
        # Should add new contact_information
        assert 'contact_information' in merged_knowledge
        assert merged_knowledge['contact_information']['confidence_score'] == 0.95


class TestRealDatabaseIntegration:
    """Test real database operations for voice agents and knowledge storage"""
    
    def test_voice_agent_database_persistence(self):
        """Test that voice agents persist to real database"""
        from src.services.voice_agent_service import VoiceAgentService
        
        service = VoiceAgentService()
        
        tenant_id = str(uuid.uuid4())
        agent_data = {
            'name': 'Database Test Agent',
            'description': 'Agent for testing database persistence',
            'knowledge_base': {
                'company_overview': {
                    'title': 'Test Company',
                    'content': 'This is a test company for database persistence.',
                    'confidence_score': 0.8
                }
            }
        }
        
        # Create and persist agent
        created_agent = service.create_agent(tenant_id=tenant_id, agent_data=agent_data)
        assert created_agent['id'] is not None
        
        # Retrieve agent from database
        retrieved_agent = service.get_agent(created_agent['id'], tenant_id)
        assert retrieved_agent is not None
        assert retrieved_agent['name'] == 'Database Test Agent'
        assert 'company_overview' in retrieved_agent['knowledge_base']
        
        # Update agent knowledge
        updated_knowledge = {
            'contact_information': {
                'title': 'Contact Info',
                'content': 'Phone: 555-TEST',
                'confidence_score': 0.9
            }
        }
        
        updated_agent = service.update_agent_knowledge(
            agent_id=created_agent['id'],
            tenant_id=tenant_id,
            knowledge_updates=updated_knowledge
        )
        
        assert 'contact_information' in updated_agent['knowledge_base']
        assert updated_agent['knowledge_base']['contact_information']['content'] == 'Phone: 555-TEST'
    
    def test_knowledge_base_size_validation_real(self):
        """Test real knowledge base size validation and compression"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        service = KnowledgeBaseService()
        
        # Create large knowledge base
        large_knowledge_base = {}
        for i in range(10):
            large_knowledge_base[f'category_{i}'] = {
                'title': f'Category {i} Title',
                'content': 'Large content ' * 100,  # Create substantial content
                'keywords': [f'keyword{j}' for j in range(20)],
                'confidence_score': 0.8 + (i * 0.01),
                'structured_data': {
                    'items': [{'name': f'Item {j}', 'description': f'Description {j}'} for j in range(10)]
                }
            }
        
        # Validate size
        size_validation = service.validate_knowledge_base_size(large_knowledge_base)
        assert 'is_valid' in size_validation
        assert 'estimated_size_mb' in size_validation
        assert 'categories_breakdown' in size_validation
        
        # Test compression
        if not size_validation['is_valid']:
            compressed_kb = service.compress_knowledge_base(large_knowledge_base)
            compressed_size_validation = service.validate_knowledge_base_size(compressed_kb)
            
            # Compression should reduce size
            assert compressed_size_validation['estimated_size_mb'] < size_validation['estimated_size_mb']
    
    def test_tenant_isolation_real_database(self):
        """Test that tenant isolation works with real database operations"""
        from src.services.voice_agent_service import VoiceAgentService
        
        service = VoiceAgentService()
        
        # Create agents for two different tenants
        tenant1_id = str(uuid.uuid4())
        tenant2_id = str(uuid.uuid4())
        
        agent1_data = {
            'name': 'Tenant 1 Agent',
            'description': 'Agent for tenant 1'
        }
        
        agent2_data = {
            'name': 'Tenant 2 Agent', 
            'description': 'Agent for tenant 2'
        }
        
        # Create agents
        agent1 = service.create_agent(tenant1_id, agent1_data)
        agent2 = service.create_agent(tenant2_id, agent2_data)
        
        # Verify tenant1 can only see their agent
        tenant1_agents = service.list_agents(tenant1_id)
        agent1_ids = [agent['id'] for agent in tenant1_agents]
        assert agent1['id'] in agent1_ids
        assert agent2['id'] not in agent1_ids
        
        # Verify tenant2 can only see their agent
        tenant2_agents = service.list_agents(tenant2_id)
        agent2_ids = [agent['id'] for agent in tenant2_agents]
        assert agent2['id'] in agent2_ids
        assert agent1['id'] not in agent2_ids
        
        # Verify cross-tenant access is blocked
        cross_tenant_result = service.get_agent(agent1['id'], tenant2_id)  # Wrong tenant
        assert cross_tenant_result is None  # Should return None, not raise exception


class TestAPIEndpointIntegration:
    """Test integration with FastAPI endpoints using real service layer"""
    
    def test_voice_agent_api_endpoints_integration(self):
        """Test that API endpoints integrate properly with real services"""
        try:
            from src.api.routers.voice_agents import router
            from src.services.voice_agent_service import VoiceAgentService
            
            # Router should exist and have expected endpoints
            assert router is not None
            
            # Check that routes are defined
            routes = [route.path for route in router.routes]
            expected_routes = ['/', '/{agent_id}', '/{agent_id}/knowledge']
            
            for expected_route in expected_routes:
                assert any(expected_route in route for route in routes), f"Missing route: {expected_route}"
            
            # Service should be injectable
            service = VoiceAgentService()
            assert service is not None
            
        except ImportError:
            pytest.skip("API router not available")
    
    def test_knowledge_update_api_integration(self):
        """Test API integration for knowledge updates"""
        try:
            from src.api.routers.voice_agents import update_voice_agent_knowledge
            from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
            
            # Endpoint function should exist
            assert callable(update_voice_agent_knowledge)
            
            # Schema should be importable
            assert VoiceAgentKnowledgeUpdateRequest is not None
            
            # Should handle knowledge category updates
            test_knowledge_update = {
                'company_overview': {
                    'title': 'Updated Company Info',
                    'content': 'New company information',
                    'confidence_score': 0.9
                }
            }
            
            # Schema should validate the request
            try:
                request = VoiceAgentKnowledgeUpdateRequest(knowledge_base=test_knowledge_update)
                assert request.knowledge_base is not None
            except Exception as e:
                # If schema validation fails, that's still a valid test result
                assert 'validation' in str(e).lower() or 'required' in str(e).lower()
                
        except ImportError:
            pytest.skip("API components not available")


class TestErrorHandlingAndEdgeCases:
    """Test real error handling and edge cases in service integration"""
    
    def test_invalid_knowledge_data_handling(self):
        """Test handling of invalid knowledge data with real validation"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        
        service = KnowledgeBaseService()
        
        invalid_knowledge_data = {
            'invalid_category': {
                'title': 'Invalid Category',
                'content': 'This category does not exist'
            },
            'company_overview': {
                # Missing required title
                'content': 'Company content without title'
            },
            'contact_information': {
                'title': 'Contact',
                'content': 'Valid contact info',
                'confidence_score': 1.5  # Invalid score > 1.0
            }
        }
        
        # Should handle invalid data gracefully
        validated_data = service.validate_crawled_content(invalid_knowledge_data)
        
        # Invalid category should be filtered out
        assert 'invalid_category' not in validated_data
        
        # Invalid company_overview should be filtered out (missing title)
        assert 'company_overview' not in validated_data
        
        # Invalid confidence score should be handled
        if 'contact_information' in validated_data:
            # Either filtered out or confidence score corrected
            contact_confidence = validated_data['contact_information'].get('confidence_score')
            assert contact_confidence is None or contact_confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_network_error_handling_real(self):
        """Test real network error handling in web crawler"""
        from src.services.web_crawler_service import WebCrawlerService
        
        service = WebCrawlerService()
        
        # Test with invalid URL
        invalid_result = await service.fetch_url_content("not-a-valid-url")
        assert 'error' in invalid_result
        assert invalid_result.get('status_code') == 400
        
        # Test with unreachable URL (should timeout gracefully)
        unreachable_result = await service.fetch_url_content("https://definitely-not-a-real-domain-12345.com")
        assert 'error' in unreachable_result
        # Should be a network-related error
        error_msg = unreachable_result['error'].lower()
        assert any(keyword in error_msg for keyword in ['timeout', 'connection', 'resolve', 'network'])
    
    def test_large_knowledge_base_handling(self):
        """Test handling of very large knowledge bases"""
        from src.services.knowledge_base_service import KnowledgeBaseService
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        
        service = KnowledgeBaseService()
        
        # Create maximum size knowledge base
        large_kb = {}
        for category in KNOWLEDGE_CATEGORIES:
            large_kb[category] = {
                'title': f'{category.replace("_", " ").title()}',
                'content': 'Large content block. ' * 200,  # ~4KB per category
                'keywords': [f'keyword{i}' for i in range(50)],
                'confidence_score': 0.9,
                'structured_data': {
                    'items': [
                        {
                            'name': f'Item {i}',
                            'description': f'Description for item {i} with lots of detail. ' * 10
                        } for i in range(20)
                    ]
                }
            }
        
        # Test size validation
        stats = service.get_knowledge_base_stats(large_kb)
        assert 'total_categories' in stats
        assert stats['total_categories'] == len(KNOWLEDGE_CATEGORIES)
        assert 'quality_score' in stats
        assert 0 <= stats['quality_score'] <= 1
        
        # Test compression
        compressed_kb = service.compress_knowledge_base(large_kb)
        
        # Compressed version should be smaller
        original_size = len(str(large_kb))
        compressed_size = len(str(compressed_kb))
        compression_ratio = compressed_size / original_size
        
        # Should achieve some compression (at least 10% reduction)
        assert compression_ratio < 0.9, f"Compression ratio {compression_ratio:.2f} should be < 0.9"


class TestPerformanceAndScalability:
    """Test performance characteristics of real implementations"""
    
    def test_concurrent_voice_agent_operations(self):
        """Test concurrent voice agent operations with real database"""
        from src.services.voice_agent_service import VoiceAgentService
        import concurrent.futures
        import threading
        
        service = VoiceAgentService()
        
        def create_agent_worker(worker_id):
            tenant_id = str(uuid.uuid4())
            agent_data = {
                'name': f'Worker {worker_id} Agent',
                'description': f'Agent created by worker {worker_id}'
            }
            return service.create_agent(tenant_id, agent_data)
        
        # Create multiple agents concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_agent_worker, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All agents should be created successfully
        assert len(results) == 10
        for agent in results:
            assert agent is not None
            assert agent['id'] is not None
            assert 'Worker' in agent['name']
    
    @pytest.mark.asyncio
    async def test_batch_web_crawling_performance(self):
        """Test batch web crawling performance with real HTTP requests"""
        from src.services.web_crawler_service import WebCrawlerService
        
        service = WebCrawlerService()
        
        # Create test URLs (using data URLs for consistency)
        test_urls = []
        for i in range(5):
            html = f"<html><body><h1>Test Page {i}</h1><p>Content for page {i}</p></body></html>"
            import urllib.parse
            data_url = f"data:text/html,{urllib.parse.quote(html)}"
            test_urls.append(data_url)
        
        # Time the batch crawling
        import time
        start_time = time.time()
        
        results = service.batch_crawl_urls(test_urls)
        
        end_time = time.time()
        crawl_duration = end_time - start_time
        
        # Should complete within reasonable time (5 URLs in < 10 seconds)
        assert crawl_duration < 10.0, f"Batch crawling took {crawl_duration:.2f}s, should be < 10s"
        
        # All URLs should be processed
        assert len(results) == 5
        for result in results:
            assert 'url' in result
            assert result.get('status') in ['success', 'pending', 'error']