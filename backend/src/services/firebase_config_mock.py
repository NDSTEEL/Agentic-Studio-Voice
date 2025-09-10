"""
Mock Firebase configuration for testing
"""
from typing import Optional, Dict, Any
from .voice_agent_service import MockFirestoreClient


class MockFirebaseConfig:
    """Mock Firebase configuration for testing"""
    
    def __init__(self):
        pass
    
    @property
    def firestore_client(self):
        """Get mock Firestore client"""
        return MockFirestoreClient()
    
    async def verify_token(self, token: str) -> dict:
        """Mock token verification"""
        return {
            'uid': 'test_user_123',
            'email': 'test@example.com',
            'email_verified': True,
            'name': 'Test User'
        }


# Global mock Firebase config instance
firebase_config = MockFirebaseConfig()


# Convenience functions
async def verify_firebase_token(token: str) -> dict:
    """Mock verify Firebase token"""
    return await firebase_config.verify_token(token)


def get_firestore_client():
    """Get mock Firestore client"""
    return firebase_config.firestore_client