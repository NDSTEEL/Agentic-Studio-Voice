"""
Authentication dependencies for FastAPI with Firebase
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.services.firebase_config import verify_firebase_token, get_firestore_client

# Try to import Google Cloud, fallback to mock for testing
try:
    from google.cloud.firestore import DocumentSnapshot
    HAS_GOOGLE_CLOUD = True
except ImportError:
    # Mock DocumentSnapshot for testing
    class DocumentSnapshot:
        def __init__(self, data):
            self._data = data
        def to_dict(self):
            return self._data
    HAS_GOOGLE_CLOUD = False

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from Firebase ID token
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify Firebase ID token
        user_claims = await verify_firebase_token(credentials.credentials)
        
        # Get user document from Firestore
        db = get_firestore_client()
        user_doc_ref = db.collection('users').document(user_claims['uid'])
        user_doc: DocumentSnapshot = user_doc_ref.get()
        
        user_data = {
            "uid": user_claims['uid'],
            "email": user_claims.get('email'),
            "name": user_claims.get('name'),
            "email_verified": user_claims.get('email_verified', False),
            "tenant_id": None  # Will be set from Firestore document
        }
        
        # Merge with Firestore data if document exists
        if user_doc.exists:
            firestore_data = user_doc.to_dict()
            if firestore_data:
                user_data.update({
                    "tenant_id": firestore_data.get('tenantId'),
                    "created_at": firestore_data.get('created_at'),
                    "updated_at": firestore_data.get('updated_at'),
                    "displayName": firestore_data.get('displayName'),
                    "photoURL": firestore_data.get('photoURL')
                })
        
        logger.info(f"Authenticated user: {user_data['uid']}")
        return user_data
        
    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_uid(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Convenience dependency to get current user UID
    """
    return current_user["uid"]


async def get_current_tenant_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> Optional[str]:
    """
    Convenience dependency to get current tenant ID
    """
    return current_user.get("tenant_id")


async def require_tenant_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Dependency that requires user to have a tenant ID (for multi-tenant operations)
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be assigned to a tenant to perform this action"
        )
    return tenant_id