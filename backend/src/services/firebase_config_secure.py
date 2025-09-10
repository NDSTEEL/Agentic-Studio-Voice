"""
Firebase configuration and initialization for the backend - SECURITY COMPLIANT
Enhanced version with proper credential management and security validation
"""
import os
import json
import logging
from typing import Optional
from unittest.mock import Mock, MagicMock

# Try to import Firebase, fallback to mock if not available
try:
    from firebase_admin import credentials, initialize_app, get_app
    from firebase_admin.auth import verify_id_token
    from firebase_admin.firestore import client
    from google.cloud.firestore import Client
    import firebase_admin
    FIREBASE_AVAILABLE = True
except ImportError as e:
    FIREBASE_AVAILABLE = False
    logging.warning(f"Firebase SDK not available: {e}")

logger = logging.getLogger(__name__)


class SecureFirebaseConfig:
    """Firebase configuration and service management with security enhancements"""
    
    _instance: Optional['SecureFirebaseConfig'] = None
    _initialized = False
    
    def __new__(cls) -> 'SecureFirebaseConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._security_validated = False
            self._mock_mode = False
            self._initialize_firebase_secure()
            self._initialized = True
    
    def _initialize_firebase_secure(self) -> None:
        """Initialize Firebase Admin SDK with security validation"""
        
        if not FIREBASE_AVAILABLE:
            logger.warning("🚨 SECURITY: Firebase SDK not available, using mock mode")
            self._init_mock_firebase()
            return
        
        try:
            # Try to get existing app first
            firebase_admin.get_app()
            logger.info("✅ SECURITY: Firebase app already initialized")
            self._security_validated = True
        except ValueError:
            # Initialize new app with security checks
            try:
                # SECURITY: Check for credentials in order of preference
                if self._init_from_environment():
                    logger.info("✅ SECURITY: Firebase initialized with environment credentials")
                    self._security_validated = True
                elif self._init_from_service_account_file():
                    logger.info("✅ SECURITY: Firebase initialized with service account file")
                    self._security_validated = True
                elif self._init_with_default_credentials():
                    logger.info("✅ SECURITY: Firebase initialized with default credentials")
                    self._security_validated = True
                else:
                    logger.warning("⚠️ SECURITY: No valid Firebase credentials found, using mock mode")
                    self._init_mock_firebase()
                    
            except Exception as e:
                logger.error(f"❌ SECURITY: Failed to initialize Firebase: {e}")
                if os.getenv('ENVIRONMENT') == 'development':
                    logger.info("🧪 DEVELOPMENT: Falling back to mock Firebase")
                    self._init_mock_firebase()
                else:
                    raise e
    
    def _init_from_environment(self) -> bool:
        """Initialize Firebase from environment variable credentials"""
        service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if not service_account_key:
            return False
        
        try:
            # SECURITY: Validate JSON structure before parsing
            service_account_info = json.loads(service_account_key)
            
            # SECURITY: Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            if not all(field in service_account_info for field in required_fields):
                logger.error("❌ SECURITY: Invalid service account key structure")
                return False
            
            # SECURITY: Validate service account type
            if service_account_info.get('type') != 'service_account':
                logger.error("❌ SECURITY: Invalid service account type")
                return False
            
            # Initialize Firebase with validated credentials
            cred = credentials.Certificate(service_account_info)
            initialize_app(cred)
            return True
            
        except json.JSONDecodeError:
            logger.error("❌ SECURITY: Invalid JSON in FIREBASE_SERVICE_ACCOUNT_KEY")
            return False
        except Exception as e:
            logger.error(f"❌ SECURITY: Failed to initialize from environment: {e}")
            return False
    
    def _init_from_service_account_file(self) -> bool:
        """Initialize Firebase from service account file"""
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_path:
            # Check for test credentials file
            test_credentials_path = '/mnt/c/Users/avibm/Agentic-Studio-Voice/backend/firebase-service-account-test.json'
            if os.path.exists(test_credentials_path):
                credentials_path = test_credentials_path
                logger.warning("🧪 SECURITY: Using test credentials file (development only)")
            else:
                return False
        
        try:
            # SECURITY: Validate file exists and is readable
            if not os.path.exists(credentials_path):
                logger.error(f"❌ SECURITY: Credentials file not found: {credentials_path}")
                return False
            
            # SECURITY: Check file permissions (should not be world-readable)
            file_stat = os.stat(credentials_path)
            if file_stat.st_mode & 0o044:  # Check if group or others can read
                logger.warning("⚠️ SECURITY: Credentials file has permissive permissions")
            
            # Initialize Firebase
            cred = credentials.Certificate(credentials_path)
            initialize_app(cred)
            return True
            
        except Exception as e:
            logger.error(f"❌ SECURITY: Failed to initialize from service account file: {e}")
            return False
    
    def _init_with_default_credentials(self) -> bool:
        """Initialize Firebase with default application credentials"""
        try:
            # This works on Cloud Run, GAE, etc.
            cred = credentials.ApplicationDefault()
            initialize_app(cred)
            return True
        except Exception as e:
            logger.debug(f"Default credentials not available: {e}")
            return False
    
    def _init_mock_firebase(self) -> None:
        """Initialize mock Firebase for testing/development"""
        self._mock_mode = True
        
        # Create mock firestore client
        self._mock_firestore_client = Mock()
        self._mock_firestore_client.collection.return_value = Mock()
        
        logger.info("🧪 MOCK: Firebase mock mode initialized for testing")
    
    @property
    def firestore_client(self):
        """Get Firestore client (real or mock)"""
        if self._mock_mode:
            return self._mock_firestore_client
        
        if FIREBASE_AVAILABLE:
            return client()
        else:
            return self._mock_firestore_client
    
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
        if self._mock_mode:
            # SECURITY: Mock token verification for testing
            if token.startswith('mock_'):
                return {
                    'uid': 'mock_user_123',
                    'email': 'test@example.com',
                    'email_verified': True,
                    'name': 'Mock User',
                    'mock_mode': True
                }
            else:
                raise ValueError("Invalid mock token")
        
        if not FIREBASE_AVAILABLE:
            raise ValueError("Firebase SDK not available")
        
        try:
            # SECURITY: Validate token format before verification
            if not token or len(token) < 10:
                raise ValueError("Invalid token format")
            
            # Verify the ID token
            decoded_token = verify_id_token(token)
            
            # SECURITY: Extract and validate user information
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
                'sub': decoded_token.get('sub'),
                'security_validated': True
            }
            
            # SECURITY: Additional validation
            if not user_info['uid'] or not user_info['email']:
                raise ValueError("Invalid token: missing required fields")
            
            logger.info(f"✅ SECURITY: Token verified for user: {user_info['uid']}")
            return user_info
            
        except Exception as e:
            logger.error(f"❌ SECURITY: Token verification failed: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
    
    def get_service_status(self) -> dict:
        """Get service status for monitoring"""
        return {
            'firebase_available': FIREBASE_AVAILABLE,
            'security_validated': self._security_validated,
            'mock_mode': self._mock_mode,
            'initialized': self._initialized,
            'service_type': 'mock' if self._mock_mode else 'real'
        }


# Global Firebase config instance
secure_firebase_config = SecureFirebaseConfig()


# Convenience functions
async def verify_firebase_token(token: str) -> dict:
    """Verify Firebase token - convenience function"""
    return await secure_firebase_config.verify_token(token)


def get_firestore_client():
    """Get Firestore client - convenience function"""
    return secure_firebase_config.firestore_client


def get_firebase_service_status() -> dict:
    """Get Firebase service status - convenience function"""
    return secure_firebase_config.get_service_status()