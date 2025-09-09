"""
Firebase configuration and initialization for the backend
"""
import os
import logging
from typing import Optional
from firebase_admin import credentials, initialize_app, get_app
from firebase_admin.auth import verify_id_token
from firebase_admin.firestore import client
from google.cloud.firestore import Client
import firebase_admin

logger = logging.getLogger(__name__)


class FirebaseConfig:
    """Firebase configuration and service management"""
    
    _instance: Optional['FirebaseConfig'] = None
    _initialized = False
    
    def __new__(cls) -> 'FirebaseConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            # Try to get existing app first
            firebase_admin.get_app()
            logger.info("Firebase app already initialized")
        except ValueError:
            # Initialize new app
            try:
                # Production: use service account key or default credentials
                if os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'):
                    # JSON key as environment variable
                    import json
                    service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY'))
                    cred = credentials.Certificate(service_account_info)
                    initialize_app(cred)
                    logger.info("Firebase initialized with service account key")
                elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                    # Service account key file path
                    cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
                    initialize_app(cred)
                    logger.info("Firebase initialized with service account file")
                else:
                    # Default credentials (for Cloud Run, GAE, etc.)
                    cred = credentials.ApplicationDefault()
                    initialize_app(cred)
                    logger.info("Firebase initialized with default credentials")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                # For development, you might want to continue without Firebase
                if os.getenv('ENVIRONMENT') != 'development':
                    raise e
    
    @property
    def firestore_client(self) -> Client:
        """Get Firestore client"""
        return client()
    
    async def verify_token(self, token: str) -> dict:
        """
        Verify Firebase ID token and return user claims
        
        Args:
            token: Firebase ID token from frontend
            
        Returns:
            dict: User claims from the token
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify the ID token
            decoded_token = verify_id_token(token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'iss': decoded_token.get('iss'),
                'aud': decoded_token.get('aud'),
                'auth_time': decoded_token.get('auth_time'),
                'exp': decoded_token.get('exp'),
                'iat': decoded_token.get('iat'),
                'sub': decoded_token.get('sub')
            }
            
            logger.info(f"Token verified for user: {user_info['uid']}")
            return user_info
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {str(e)}")


# Global Firebase config instance
firebase_config = FirebaseConfig()


# Convenience functions
async def verify_firebase_token(token: str) -> dict:
    """Verify Firebase token - convenience function"""
    return await firebase_config.verify_token(token)


def get_firestore_client() -> Client:
    """Get Firestore client - convenience function"""
    return firebase_config.firestore_client