"""
JWT token handling for authentication
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException, status


def get_jwt_secret() -> str:
    """Get JWT secret from environment"""
    return os.getenv("JWT_SECRET", "your-secret-key-change-in-production")


def get_jwt_algorithm() -> str:
    """Get JWT algorithm from environment"""
    return os.getenv("JWT_ALGORITHM", "HS256")


def create_access_token(payload: Dict[str, Any], expires_in: int = 3600) -> str:
    """
    Create JWT access token with expiration
    """
    # Add expiration time to payload
    expire = datetime.utcnow() + timedelta(seconds=expires_in)
    payload_copy = payload.copy()
    payload_copy.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Create token
    secret = get_jwt_secret()
    algorithm = get_jwt_algorithm()
    
    token = jwt.encode(payload_copy, secret, algorithm=algorithm)
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return payload
    """
    try:
        secret = get_jwt_secret()
        algorithm = get_jwt_algorithm()
        
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token without verification (for testing)
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not decode token"
        )


def extract_tenant_from_token(token: str) -> str:
    """
    Extract tenant ID from JWT token
    """
    payload = verify_token(token)
    tenant_id = payload.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant information"
        )
    
    return tenant_id