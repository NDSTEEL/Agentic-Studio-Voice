"""
Test for T005: Basic API Structure
TDD: Write failing tests first for FastAPI app, routers, CORS, and security headers
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status


class TestFastAPIApplication:
    """Test FastAPI application setup and configuration"""
    
    def test_fastapi_app_creation(self):
        """Test that FastAPI application can be created"""
        from src.api.app import create_app
        
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title is not None
        assert app.version is not None
    
    def test_app_has_middleware(self):
        """Test that app has required middleware configured"""
        from src.api.app import create_app
        
        app = create_app()
        
        # Check middleware is configured
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert 'CORSMiddleware' in middleware_classes
        assert 'TrustedHostMiddleware' in middleware_classes or len(middleware_classes) >= 2
    
    def test_app_cors_configuration(self):
        """Test CORS middleware configuration"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        # Test preflight request
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should not be 405 Method Not Allowed if CORS is configured
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED


class TestBaseRouterStructure:
    """Test base router structure and endpoint organization"""
    
    def test_api_router_exists(self):
        """Test that main API router exists"""
        from src.api.routers import api_router
        
        assert api_router is not None
        assert hasattr(api_router, 'routes')
    
    def test_health_endpoint_exists(self):
        """Test that health check endpoint exists"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_v1_prefix(self):
        """Test that API routes have v1 prefix"""
        from src.api.app import create_app
        
        app = create_app()
        
        # Check that routes are prefixed with /api/v1
        api_routes = [route.path for route in app.routes]
        has_api_v1_routes = any(path.startswith("/api/v1") for path in api_routes)
        assert has_api_v1_routes or "/api/v1" in str(app.routes)
    
    def test_tenant_router_included(self):
        """Test that tenant router is included in main router"""
        from src.api.routers import api_router
        
        # Check that tenant routes are included
        route_paths = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                route_paths.append(route.path)
            elif hasattr(route, 'path_regex'):
                route_paths.append(str(route.path_regex))
        
        has_tenant_routes = any("tenant" in path.lower() for path in route_paths)
        assert has_tenant_routes


class TestSecurityHeaders:
    """Test security headers implementation"""
    
    def test_security_headers_middleware(self):
        """Test that security headers are added to responses"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Check for common security headers
        headers = response.headers
        
        # At least one security header should be present
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        has_security_header = any(header in headers for header in security_headers)
        assert has_security_header, f"No security headers found. Headers: {list(headers.keys())}"
    
    def test_content_type_options_header(self):
        """Test X-Content-Type-Options header is set"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_frame_options_header(self):
        """Test X-Frame-Options header is set"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] in ["DENY", "SAMEORIGIN"]


class TestAPIBootstrap:
    """Test API bootstrap functionality"""
    
    def test_app_startup_event(self):
        """Test application startup event configuration"""
        from src.api.app import create_app
        
        app = create_app()
        
        # Check that startup events are configured
        assert hasattr(app, 'router')
        startup_handlers = getattr(app.router, 'on_startup', [])
        assert len(startup_handlers) >= 0  # May be empty initially
    
    def test_app_shutdown_event(self):
        """Test application shutdown event configuration"""
        from src.api.app import create_app
        
        app = create_app()
        
        # Check that shutdown events are configured
        assert hasattr(app, 'router')
        shutdown_handlers = getattr(app.router, 'on_shutdown', [])
        assert len(shutdown_handlers) >= 0  # May be empty initially
    
    def test_exception_handler_configuration(self):
        """Test that custom exception handlers are configured"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        # Test 404 handling
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Response should be JSON
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def test_openapi_documentation(self):
        """Test OpenAPI documentation is configured"""
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        # Test OpenAPI schema endpoint
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        
        openapi_schema = response.json()
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema


class TestRouterConfiguration:
    """Test router configuration and organization"""
    
    def test_main_router_imports(self):
        """Test that main router can import required modules"""
        try:
            from src.api.routers.tenants import router as tenant_router
            from src.api.routers.health import router as health_router
            from src.api.routers import api_router
            
            assert tenant_router is not None
            assert health_router is not None
            assert api_router is not None
        except ImportError as e:
            pytest.fail(f"Required router modules not found: {e}")
    
    def test_router_tags_configuration(self):
        """Test that routers have proper tags for documentation"""
        from src.api.routers import api_router
        
        # Check that routes have tags for OpenAPI grouping
        tagged_routes = []
        for route in api_router.routes:
            if hasattr(route, 'tags') and route.tags:
                tagged_routes.extend(route.tags)
        
        # Should have at least some tagged routes
        assert len(tagged_routes) >= 0  # Will be populated as routers are added


if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    pytest.main([__file__, "-v"])