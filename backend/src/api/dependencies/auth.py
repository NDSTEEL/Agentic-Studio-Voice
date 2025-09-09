"""
Authentication dependencies for FastAPI
TODO: [MOCK_REGISTRY] Mock authentication - needs real JWT verification
"""
from typing import Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    TODO: [MOCK_REGISTRY] Mock current user - needs real JWT token validation
    
    Dependency to get current authenticated user from JWT token
    This is a mock implementation for testing purposes
    """
    # TODO: Replace with real JWT token validation
    # For now, return a mock user for testing
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock user data - in real implementation, decode JWT and fetch user
    mock_user = {
        "id": "user-12345678",
        "tenant_id": "tenant-12345678", 
        "email": "test@example.com",
        "name": "Test User"
    }
    
    return mock_user


async def get_current_tenant_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Convenience dependency to get current tenant ID
    """
    return current_user["tenant_id"]