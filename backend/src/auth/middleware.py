"""
Authentication and tenant context middleware for FastAPI
"""
import os
from typing import Callable, Optional
from functools import wraps
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_handler import verify_token, extract_tenant_from_token, get_jwt_secret, get_jwt_algorithm
from .models import UserAuth, TenantAuth


# Global tenant context storage
_tenant_context: Optional[str] = None


def set_tenant_context(tenant_id: str):
    """Set current tenant context"""
    global _tenant_context
    _tenant_context = tenant_id


def get_tenant_context() -> Optional[str]:
    """Get current tenant context"""
    return _tenant_context


class JWTValidator:
    """JWT validation class"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expires_in: int = 3600):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expires_in = expires_in
    
    def create_token(self, payload: dict) -> str:
        """Create JWT token"""
        from .jwt_handler import create_access_token
        return create_access_token(payload, expires_in=self.expires_in)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        from .jwt_handler import verify_token
        return verify_token(token)


class AuthenticationMiddleware:
    """FastAPI authentication middleware"""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process authentication middleware"""
        # Check for authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        # Extract token from Bearer header
        try:
            scheme, token = auth_header.split(" ")
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        # Verify token
        payload = verify_token(token)
        
        # Add user context to request state
        request.state.user = payload
        
        # Process request
        response = await call_next(request)
        return response


class TenantContextMiddleware:
    """Multi-tenant context middleware"""
    
    async def __call__(self, request: Request, call_next: Callable):
        """Process tenant context middleware"""
        # Get user from request state (set by AuthenticationMiddleware)
        user_context = getattr(request.state, 'user', None)
        
        if not user_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User context not found"
            )
        
        # Extract tenant ID
        tenant_id = user_context.get("tenant_id")
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context not found"
            )
        
        # Set tenant context
        set_tenant_context(tenant_id)
        request.state.tenant_id = tenant_id
        
        # Process request
        response = await call_next(request)
        return response


# Dependency injection functions
security = HTTPBearer()


async def get_current_user(token) -> UserAuth:
    """Get current authenticated user"""
    # Handle both string tokens (for testing) and HTTPAuthorizationCredentials (for production)
    if isinstance(token, str):
        token_str = token
    elif hasattr(token, 'credentials'):
        token_str = token.credentials
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    payload = verify_token(token_str)
    
    return UserAuth(
        user_id=payload["user_id"],
        email=payload["email"], 
        tenant_id=payload["tenant_id"]
    )


async def get_current_tenant(request: Request) -> TenantAuth:
    """Get current tenant context"""
    tenant_id = getattr(request.state, 'tenant_id', None)
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context not found"
        )
    
    # In a real implementation, you'd fetch tenant details from database
    return TenantAuth(
        tenant_id=tenant_id,
        name=f"Tenant {tenant_id}"
    )


# Decorators
def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would normally be handled by FastAPI dependencies
        return await func(*args, **kwargs)
    
    # Add type annotation for user parameter
    wrapper.__annotations__ = getattr(func, '__annotations__', {})
    if 'user' not in wrapper.__annotations__:
        wrapper.__annotations__['user'] = UserAuth
    
    return wrapper


def require_tenant_access(func):
    """Decorator to require tenant access"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would normally be handled by FastAPI dependencies
        return await func(*args, **kwargs)
    
    # Add type annotations for both user and tenant parameters
    wrapper.__annotations__ = getattr(func, '__annotations__', {})
    if 'user' not in wrapper.__annotations__:
        wrapper.__annotations__['user'] = UserAuth
    if 'tenant' not in wrapper.__annotations__:
        wrapper.__annotations__['tenant'] = TenantAuth
    
    return wrapper