"""
T013: Web Crawling Service Tests
REAL implementation approach - no mocking of HTTP, HTML parsing, or database
Only mock external paid APIs if needed
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any, List


class TestWebCrawlerServiceCore:
    """Test core web crawling functionality with REAL implementations"""
    
    def test_web_crawler_service_exists(self):
        """Test that WebCrawlerService exists and is properly structured"""
        try:
            from src.services.web_crawler_service import WebCrawlerService
            service = WebCrawlerService()
            
            # Should have core methods
            assert hasattr(service, 'crawl_website')
            assert hasattr(service, 'extract_content_from_url')
            assert hasattr(service, 'parse_html_content')
            assert callable(service.crawl_website)
            assert callable(service.extract_content_from_url)
            assert callable(service.parse_html_content)
        except ImportError:
            assert False, "WebCrawlerService should exist in src.services.web_crawler_service"
    
    def test_http_client_initialization(self):
        """Test that service can initialize HTTP client properly"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Should have session attribute (may be None initially)
        assert hasattr(service, 'session')
        # Should have timeout configuration
        assert hasattr(service, 'timeout')
        assert isinstance(service.timeout, (int, float))
        assert service.timeout > 0
        # Should have user agent configured
        assert hasattr(service, 'user_agent')
        assert len(service.user_agent) > 0


class TestHTMLParsingReal:
    """Test real HTML parsing functionality"""
    
    def test_parse_simple_html_content(self):
        """Test parsing of simple HTML content with BeautifulSoup"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Welcome</h1>
                <p>This is test content.</p>
                <div class="contact">
                    <p>Phone: 555-123-4567</p>
                    <p>Email: test@example.com</p>
                </div>
            </body>
        </html>
        """
        
        result = service.parse_html_content(html_content)
        
        # Should extract basic elements
        assert 'title' in result
        assert result['title'] == 'Test Page'
        assert 'headings' in result
        assert 'Welcome' in str(result['headings'])
        assert 'text_content' in result
        assert 'test content' in result['text_content'].lower()
    
    def test_extract_contact_information_from_html(self):
        """Test extraction of contact info from HTML using real parsing"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        html_content = """
        <html>
            <body>
                <div class="contact">
                    <p>Call us: (555) 123-4567</p>
                    <p>Email: contact@company.com</p>
                    <p>Address: 123 Main St, City, State 12345</p>
                </div>
            </body>
        </html>
        """
        
        result = service.parse_html_content(html_content)
        contact_info = service.extract_contact_information(result)
        
        assert 'phone' in contact_info
        assert 'email' in contact_info
        assert 'address' in contact_info
        assert '555' in contact_info['phone']
        assert 'contact@company.com' in contact_info['email']
    
    def test_extract_company_information(self):
        """Test extraction of company overview information"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        html_content = """
        <html>
            <body>
                <section id="about">
                    <h2>About Our Company</h2>
                    <p>We are a leading provider of innovative solutions.</p>
                    <p>Founded in 2020, we serve customers worldwide.</p>
                </section>
            </body>
        </html>
        """
        
        result = service.parse_html_content(html_content)
        company_info = service.extract_company_information(result)
        
        assert 'title' in company_info
        assert 'content' in company_info
        assert 'about' in company_info['title'].lower()
        assert 'innovative solutions' in company_info['content']


class TestRealWebRequests:
    """Test real web requests with proper error handling"""
    
    @pytest.mark.asyncio
    async def test_fetch_real_website(self):
        """Test fetching content from a real website (httpbin.org for testing)"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Use httpbin.org for reliable testing
        test_url = "https://httpbin.org/html"
        
        try:
            result = await service.fetch_url_content(test_url)
            
            # Should return valid response
            assert 'content' in result
            assert 'status_code' in result
            assert result['status_code'] == 200
            assert '<html>' in result['content']
            
        except Exception as e:
            # If network issues, should handle gracefully
            assert 'connection' in str(e).lower() or 'timeout' in str(e).lower()
    
    def test_url_validation(self):
        """Test URL validation with real parsing"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Valid URLs
        assert service.is_valid_url("https://example.com")
        assert service.is_valid_url("http://test.org/page")
        
        # Invalid URLs
        assert not service.is_valid_url("not-a-url")
        assert not service.is_valid_url("")
        assert not service.is_valid_url("javascript:alert(1)")
    
    @pytest.mark.asyncio
    async def test_respect_robots_txt(self):
        """Test that crawler respects robots.txt"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Should check robots.txt before crawling
        can_crawl = await service.can_crawl_url("https://example.com/test-page")
        
        # Should return boolean
        assert isinstance(can_crawl, bool)


class TestKnowledgeCategoryExtraction:
    """Test extraction of knowledge categories from crawled content"""
    
    def test_extract_products_services_category(self):
        """Test extraction of products/services information"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        html_content = """
        <html>
            <body>
                <section class="products">
                    <h2>Our Products</h2>
                    <div class="product">
                        <h3>Premium Software</h3>
                        <p>Advanced business solution for enterprises.</p>
                    </div>
                    <div class="product">
                        <h3>Basic Package</h3>
                        <p>Essential features for small businesses.</p>
                    </div>
                </section>
            </body>
        </html>
        """
        
        parsed = service.parse_html_content(html_content)
        products_info = service.extract_products_services(parsed)
        
        assert 'title' in products_info
        assert 'content' in products_info
        assert 'structured_data' in products_info
        assert 'products' in products_info['structured_data']
        assert len(products_info['structured_data']['products']) >= 2
    
    def test_extract_pricing_information(self):
        """Test extraction of pricing information"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        html_content = """
        <html>
            <body>
                <div class="pricing">
                    <h2>Pricing Plans</h2>
                    <div class="plan">
                        <h3>Starter - $29/month</h3>
                        <ul><li>Feature 1</li><li>Feature 2</li></ul>
                    </div>
                    <div class="plan">
                        <h3>Professional - $99/month</h3>
                        <ul><li>All Starter features</li><li>Advanced analytics</li></ul>
                    </div>
                </div>
            </body>
        </html>
        """
        
        parsed = service.parse_html_content(html_content)
        pricing_info = service.extract_pricing_packages(parsed)
        
        assert 'title' in pricing_info
        assert 'structured_data' in pricing_info
        assert 'packages' in pricing_info['structured_data']
        assert len(pricing_info['structured_data']['packages']) >= 2
        
        # Should extract price information
        packages = pricing_info['structured_data']['packages']
        starter_found = any('29' in pkg.get('price', '') for pkg in packages)
        professional_found = any('99' in pkg.get('price', '') for pkg in packages)
        assert starter_found and professional_found


class TestSitemapParsing:
    """Test sitemap.xml parsing functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_and_parse_sitemap(self):
        """Test fetching and parsing sitemap.xml"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/</loc>
                <lastmod>2024-01-01</lastmod>
                <priority>1.0</priority>
            </url>
            <url>
                <loc>https://example.com/about</loc>
                <lastmod>2024-01-02</lastmod>
                <priority>0.8</priority>
            </url>
            <url>
                <loc>https://example.com/products</loc>
                <lastmod>2024-01-03</lastmod>
                <priority>0.9</priority>
            </url>
        </urlset>"""
        
        urls = service.parse_sitemap_xml(sitemap_xml)
        
        assert isinstance(urls, list)
        assert len(urls) == 3
        assert 'https://example.com/' in urls
        assert 'https://example.com/about' in urls
        assert 'https://example.com/products' in urls
    
    def test_prioritize_urls_for_crawling(self):
        """Test URL prioritization based on sitemap priority and content type"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        urls = [
            'https://example.com/',
            'https://example.com/about', 
            'https://example.com/products',
            'https://example.com/contact',
            'https://example.com/blog/post-1'
        ]
        
        prioritized = service.prioritize_crawling_urls(urls)
        
        assert isinstance(prioritized, list)
        assert len(prioritized) == len(urls)
        # High-priority pages should come first
        assert prioritized[0] in ['https://example.com/', 'https://example.com/about']


class TestCrawlingLimitsAndRespect:
    """Test crawling limits and respectful crawling practices"""
    
    def test_rate_limiting_configuration(self):
        """Test that rate limiting is properly configured"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Should have delay configuration
        assert hasattr(service, 'delay_between_requests')
        assert isinstance(service.delay_between_requests, (int, float))
        assert service.delay_between_requests >= 1.0  # At least 1 second
        
        # Should have max pages limit
        assert hasattr(service, 'max_pages_per_site')
        assert isinstance(service.max_pages_per_site, int)
        assert service.max_pages_per_site <= 50  # Reasonable limit
    
    def test_user_agent_configuration(self):
        """Test that User-Agent is properly set"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        user_agent = service.get_user_agent()
        
        # Should identify as a business bot, not try to hide
        assert 'bot' in user_agent.lower() or 'crawler' in user_agent.lower()
        assert len(user_agent) > 10  # Should be descriptive
    
    @pytest.mark.asyncio
    async def test_graceful_error_handling(self):
        """Test graceful handling of various error conditions"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Test timeout handling
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await service.fetch_url_content("https://slow-site.com")
            
            # Should return error result, not raise exception
            assert 'error' in result
            assert 'timeout' in result['error'].lower()
        
        # Test 404 handling
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = Mock()
            mock_response.status = 404
            mock_response.text = AsyncMock(return_value="Not Found")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await service.fetch_url_content("https://example.com/missing")
            
            assert 'status_code' in result
            assert result['status_code'] == 404


class TestDatabaseIntegrationReal:
    """Test real database integration for storing crawled content"""
    
    def test_database_session_creation(self):
        """Test that service can create real database sessions"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Should be able to get database session
        with service.get_db_session() as session:
            assert session is not None
            # Should be real SQLAlchemy session
            assert hasattr(session, 'query')
            assert hasattr(session, 'add')
            assert hasattr(session, 'commit')
    
    def test_store_crawled_content_to_database(self):
        """Test storing crawled content to real database"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        crawl_result = {
            'url': 'https://example.com/about',
            'title': 'About Us',
            'content': 'We are a test company.',
            'knowledge_categories': {
                'company_overview': {
                    'title': 'About Us',
                    'content': 'We are a test company.',
                    'confidence_score': 0.9
                }
            },
            'crawled_at': datetime.now()
        }
        
        # Should store without error
        stored_id = service.store_crawl_result(crawl_result)
        
        assert stored_id is not None
        assert isinstance(stored_id, (int, str))
        
        # Should be able to retrieve
        retrieved = service.get_crawl_result(stored_id)
        assert retrieved is not None
        assert retrieved['url'] == 'https://example.com/about'
    
    def test_avoid_duplicate_crawling(self):
        """Test that service avoids re-crawling recently crawled URLs"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        url = 'https://example.com/test-page'
        
        # First crawl should be allowed
        should_crawl = service.should_crawl_url(url)
        assert should_crawl is True
        
        # Mark as recently crawled
        service.mark_url_crawled(url)
        
        # Second crawl attempt should be skipped
        should_crawl_again = service.should_crawl_url(url)
        assert should_crawl_again is False


class TestFullCrawlingWorkflow:
    """Test complete crawling workflow with real implementations"""
    
    @pytest.mark.asyncio
    async def test_complete_website_crawl_workflow(self):
        """Test end-to-end website crawling with real components"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        # Use a simple test HTML for controlled testing
        test_url = "data:text/html,<html><head><title>Test</title></head><body><h1>Test Page</h1><p>Test content</p></body></html>"
        
        result = await service.crawl_website_complete(test_url, max_pages=1)
        
        # Should return structured result
        assert 'urls_crawled' in result
        assert 'knowledge_categories' in result
        assert 'crawl_summary' in result
        
        # Should have extracted some content
        assert result['urls_crawled'] > 0
        assert len(result['knowledge_categories']) > 0
    
    def test_batch_crawling_multiple_urls(self):
        """Test batch crawling of multiple URLs"""
        from src.services.web_crawler_service import WebCrawlerService
        service = WebCrawlerService()
        
        urls = [
            "data:text/html,<html><body><h1>Page 1</h1></body></html>",
            "data:text/html,<html><body><h1>Page 2</h1></body></html>"
        ]
        
        results = service.batch_crawl_urls(urls)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert 'url' in result
            assert 'content' in result
            assert 'knowledge_categories' in result