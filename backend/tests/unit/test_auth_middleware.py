"""
Test for T004: Authentication Middleware
TDD: Write failing tests first for JWT validation and tenant isolation
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

# Import functions to test (will fail initially)
try:
    from src.auth.middleware import (
        AuthenticationMiddleware,
        JWTValidator,
        TenantContextMiddleware,
        get_current_user,
        get_current_tenant,
        require_auth,
        require_tenant_access
    )
    from src.auth.jwt_handler import (
        create_access_token,
        verify_token,
        decode_jwt_token,
        extract_tenant_from_token
    )
    from src.auth.models import UserAuth, TenantAuth
except ImportError:
    # Functions don't exist yet - tests will fail as expected
    pass

class TestJWTValidation:
    """Test JWT token validation functionality"""
    
    def test_create_access_token(self):
        """Test JWT access token creation"""
        payload = {
            "user_id": "123",
            "tenant_id": "tenant-456",
            "email": "user@test.com"
        }
        
        token = create_access_token(payload, expires_in=3600)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 10  # Should be a proper JWT token
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token"""
        payload = {
            "user_id": "123",
            "tenant_id": "tenant-456",
            "email": "user@test.com"
        }
        
        token = create_access_token(payload, expires_in=3600)
        decoded_payload = verify_token(token)
        
        assert decoded_payload is not None
        assert decoded_payload["user_id"] == "123"
        assert decoded_payload["tenant_id"] == "tenant-456"
        assert decoded_payload["email"] == "user@test.com"
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """Test JWT token verification with expired token"""
        payload = {
            "user_id": "123",
            "tenant_id": "tenant-456"
        }
        
        # Create token that expires immediately
        token = create_access_token(payload, expires_in=-1)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_extract_tenant_from_token(self):
        """Test extracting tenant ID from JWT token"""
        payload = {
            "user_id": "123",
            "tenant_id": "tenant-456",
            "email": "user@test.com"
        }
        
        token = create_access_token(payload)
        tenant_id = extract_tenant_from_token(token)
        
        assert tenant_id == "tenant-456"

class TestAuthenticationMiddleware:
    """Test authentication middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_authentication_middleware_valid_token(self):
        """Test middleware with valid JWT token"""
        # Mock request with valid authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"authorization": "Bearer valid.jwt.token"}
        
        # Mock call_next function
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response
        
        # Create middleware
        middleware = AuthenticationMiddleware()
        
        with patch('src.auth.middleware.verify_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": "123",
                "tenant_id": "tenant-456"
            }
            
            response = await middleware(mock_request, mock_call_next)
            
            # Verify token was validated and request processed
            assert response == mock_response
            mock_verify.assert_called_once()
            mock_call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_middleware_missing_token(self):
        """Test middleware with missing authorization header"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        
        mock_call_next = AsyncMock()
        middleware = AuthenticationMiddleware()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authentication_middleware_invalid_token(self):
        """Test middleware with invalid JWT token"""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"authorization": "Bearer invalid.token"}
        
        mock_call_next = AsyncMock()
        middleware = AuthenticationMiddleware()
        
        with patch('src.auth.middleware.verify_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await middleware(mock_request, mock_call_next)
            
            assert exc_info.value.status_code == 401

class TestTenantContextMiddleware:
    """Test tenant context middleware for multi-tenant isolation"""
    
    @pytest.mark.asyncio
    async def test_tenant_context_middleware_sets_tenant(self):
        """Test middleware sets tenant context from JWT"""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user = {
            "user_id": "123",
            "tenant_id": "tenant-456"
        }
        
        mock_call_next = AsyncMock()
        mock_response = MagicMock()
        mock_call_next.return_value = mock_response
        
        middleware = TenantContextMiddleware()
        
        with patch('src.auth.middleware.set_tenant_context') as mock_set_tenant:
            response = await middleware(mock_request, mock_call_next)
            
            assert response == mock_response
            mock_set_tenant.assert_called_once_with("tenant-456")
            mock_call_next.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_tenant_context_middleware_missing_user(self):
        """Test middleware when user context is missing"""
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.user = None
        
        mock_call_next = AsyncMock()
        middleware = TenantContextMiddleware()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware(mock_request, mock_call_next)
        
        assert exc_info.value.status_code == 401
        assert "User context not found" in str(exc_info.value.detail)

class TestAuthenticationDecorators:
    """Test authentication decorators and dependency injection"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid JWT token"""
        mock_token = "valid.jwt.token"
        
        with patch('src.auth.middleware.verify_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": "123",
                "email": "user@test.com",
                "tenant_id": "tenant-456"
            }
            
            user = await get_current_user(mock_token)
            
            assert user is not None
            assert user.user_id == "123"
            assert user.email == "user@test.com"
            assert user.tenant_id == "tenant-456"
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid JWT token"""
        mock_token = "invalid.token"
        
        with patch('src.auth.middleware.verify_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_token)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_tenant_valid_context(self):
        """Test get_current_tenant with valid tenant context"""
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.tenant_id = "tenant-456"
        
        tenant = await get_current_tenant(mock_request)
        
        assert tenant is not None
        assert tenant.tenant_id == "tenant-456"
    
    @pytest.mark.asyncio
    async def test_get_current_tenant_missing_context(self):
        """Test get_current_tenant without tenant context"""
        mock_request = MagicMock()
        mock_request.state = MagicMock()
        mock_request.state.tenant_id = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_tenant(mock_request)
        
        assert exc_info.value.status_code == 403
        assert "Tenant context not found" in str(exc_info.value.detail)
    
    def test_require_auth_decorator(self):
        """Test require_auth decorator functionality"""
        @require_auth
        async def protected_endpoint(user: UserAuth):
            return {"message": f"Hello {user.email}"}
        
        # The decorator should add authentication dependency
        assert hasattr(protected_endpoint, '__annotations__')
        assert 'user' in protected_endpoint.__annotations__
    
    def test_require_tenant_access_decorator(self):
        """Test require_tenant_access decorator functionality"""
        @require_tenant_access
        async def tenant_endpoint(user: UserAuth, tenant: TenantAuth):
            return {"message": f"Tenant: {tenant.tenant_id}"}
        
        # The decorator should add both user and tenant dependencies
        assert hasattr(tenant_endpoint, '__annotations__')
        assert 'user' in tenant_endpoint.__annotations__
        assert 'tenant' in tenant_endpoint.__annotations__

class TestJWTValidator:
    """Test JWT validator class functionality"""
    
    def test_jwt_validator_initialization(self):
        """Test JWTValidator can be initialized"""
        validator = JWTValidator(
            secret_key="test-secret",
            algorithm="HS256",
            expires_in=3600
        )
        
        assert validator.secret_key == "test-secret"
        assert validator.algorithm == "HS256"
        assert validator.expires_in == 3600
    
    def test_jwt_validator_create_token(self):
        """Test JWT validator token creation"""
        validator = JWTValidator(
            secret_key="test-secret",
            algorithm="HS256"
        )
        
        payload = {"user_id": "123", "tenant_id": "tenant-456"}
        token = validator.create_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_jwt_validator_verify_token(self):
        """Test JWT validator token verification"""
        validator = JWTValidator(
            secret_key="test-secret",
            algorithm="HS256"
        )
        
        payload = {"user_id": "123", "tenant_id": "tenant-456"}
        token = validator.create_token(payload)
        decoded = validator.verify_token(token)
        
        assert decoded["user_id"] == "123"
        assert decoded["tenant_id"] == "tenant-456"

class TestAuthenticationModels:
    """Test authentication data models"""
    
    def test_user_auth_model(self):
        """Test UserAuth model creation"""
        user = UserAuth(
            user_id="123",
            email="user@test.com",
            tenant_id="tenant-456"
        )
        
        assert user.user_id == "123"
        assert user.email == "user@test.com"
        assert user.tenant_id == "tenant-456"
    
    def test_tenant_auth_model(self):
        """Test TenantAuth model creation"""
        tenant = TenantAuth(
            tenant_id="tenant-456",
            name="Test Tenant"
        )
        
        assert tenant.tenant_id == "tenant-456"
        assert tenant.name == "Test Tenant"

if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    pytest.main([__file__, "-v"])