"""
Comprehensive Phone API Endpoint Test Suite
Tests all phone API endpoints to ensure they're working correctly.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.routers.phone import router
from src.services.phone.phone_service import PhoneService
from src.services.voice_agent_service import VoiceAgentService


# Create test FastAPI app
app = FastAPI()
app.include_router(router)

client = TestClient(app)


# Mock user authentication
@pytest.fixture
def mock_current_user():
    return {
        "tenant_id": "test-tenant-123",
        "user_id": "test-user-456",
        "email": "test@example.com"
    }


# Mock authentication dependency
def get_test_current_user():
    return {
        "tenant_id": "test-tenant-123",
        "user_id": "test-user-456",
        "email": "test@example.com"
    }


class TestPhoneAPIEndpoints:
    
    def setup_method(self):
        """Setup for each test method."""
        # Patch the authentication dependency
        from src.api.dependencies.auth import get_current_user
        app.dependency_overrides[get_current_user] = get_test_current_user
    
    def teardown_method(self):
        """Cleanup after each test method."""
        app.dependency_overrides.clear()

    @patch('src.api.routers.phone.PhoneService')
    def test_search_available_numbers_success(self, mock_phone_service_class):
        """Test successful phone number search."""
        # Setup mock
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        
        mock_service.search_available_numbers = AsyncMock(return_value=[
            {
                'phone_number': '+14151234567',
                'friendly_name': 'Test Number 1',
                'capabilities': {'voice': True, 'sms': True},
                'locality': 'San Francisco',
                'region': 'CA',
                'iso_country': 'US',
                'price': '$1.00'
            },
            {
                'phone_number': '+14151234568',
                'friendly_name': 'Test Number 2',
                'capabilities': {'voice': True, 'sms': False},
                'locality': 'San Francisco',
                'region': 'CA',
                'iso_country': 'US',
                'price': '$1.00'
            }
        ])
        
        # Make request
        response = client.get(
            "/phone/numbers/available?area_code=415&contains=123&limit=5"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "available_numbers" in data
        assert "search_criteria" in data
        assert "total_found" in data
        
        assert len(data["available_numbers"]) == 2
        assert data["total_found"] == 2
        assert data["search_criteria"]["area_code"] == "415"
        assert data["search_criteria"]["contains"] == "123"
        assert data["search_criteria"]["limit"] == 5

    @patch('src.api.routers.phone.PhoneService')
    def test_search_available_numbers_error(self, mock_phone_service_class):
        """Test phone number search with service error."""
        # Setup mock to raise exception
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.search_available_numbers = AsyncMock(
            side_effect=Exception("Twilio API error")
        )
        
        # Make request
        response = client.get("/phone/numbers/available")
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to search available numbers" in response.json()["detail"]

    @patch('src.api.routers.phone.VoiceAgentService')
    @patch('src.api.routers.phone.PhoneService')
    def test_provision_phone_number_success(self, mock_phone_service_class, mock_voice_service_class):
        """Test successful phone number provisioning."""
        # Setup mocks
        mock_phone_service = MagicMock()
        mock_phone_service_class.return_value = mock_phone_service
        
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = {
            'id': 'agent-123',
            'name': 'Test Agent'
        }
        
        mock_phone_service.provision_phone_number = AsyncMock(return_value={
            'status': 'success',
            'phone_number': '+14151234567',
            'phone_sid': 'PN123456789',
            'friendly_name': 'Test Number',
            'capabilities': {'voice': True, 'sms': True},
            'webhook_urls': {
                'voice_url': 'https://example.com/voice',
                'status_callback': 'https://example.com/status'
            }
        })
        
        # Make request
        response = client.post(
            "/phone/numbers/provision",
            json={
                "phone_number": "+14151234567",
                "friendly_name": "Test Number",
                "agent_id": "agent-123"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["phone_number"] == "+14151234567"
        assert data["phone_sid"] == "PN123456789"
        assert "capabilities" in data
        assert "webhook_urls" in data

    @patch('src.api.routers.phone.VoiceAgentService')
    @patch('src.api.routers.phone.PhoneService')
    def test_provision_phone_number_agent_not_found(self, mock_phone_service_class, mock_voice_service_class):
        """Test phone number provisioning with non-existent agent."""
        # Setup mocks
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = None
        
        # Make request
        response = client.post(
            "/phone/numbers/provision",
            json={
                "phone_number": "+14151234567",
                "agent_id": "non-existent-agent"
            }
        )
        
        # Assertions
        assert response.status_code == 404
        assert "Specified voice agent not found" in response.json()["detail"]

    @patch('src.api.routers.phone.PhoneService')
    def test_provision_phone_number_service_error(self, mock_phone_service_class):
        """Test phone number provisioning with service error."""
        # Setup mock
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.provision_phone_number = AsyncMock(return_value={
            'status': 'error',
            'error': 'Phone number not available'
        })
        
        # Make request
        response = client.post(
            "/phone/numbers/provision",
            json={"phone_number": "+14151234567"}
        )
        
        # Assertions
        assert response.status_code == 400
        assert "Phone number not available" in response.json()["detail"]

    @patch('src.api.routers.phone.PhoneService')
    def test_get_phone_number_status_success(self, mock_phone_service_class):
        """Test successful phone number status retrieval."""
        # Setup mock
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.get_service_status.return_value = {
            'status': 'healthy',
            'service_type': 'real'
        }
        
        # Make request
        response = client.get("/phone/numbers/+14151234567/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["phone_number"] == "+14151234567"
        assert data["status"] == "active"
        assert "capabilities" in data

    @patch('src.api.routers.phone.PhoneService')
    def test_get_phone_number_status_error(self, mock_phone_service_class):
        """Test phone number status with service error."""
        # Setup mock to raise exception
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.get_service_status.side_effect = Exception("Service unavailable")
        
        # Make request
        response = client.get("/phone/numbers/+14151234567/status")
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to get phone number status" in response.json()["detail"]

    def test_list_phone_numbers_success(self):
        """Test successful phone number listing."""
        # Make request (currently returns empty list as placeholder)
        response = client.get("/phone/numbers?page=1&limit=10")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "phone_numbers" in data
        assert "total" in data
        assert "active_count" in data
        assert "tenant_id" in data
        
        assert data["phone_numbers"] == []
        assert data["total"] == 0
        assert data["active_count"] == 0
        assert data["tenant_id"] == "test-tenant-123"

    def test_list_phone_numbers_pagination(self):
        """Test phone number listing with pagination parameters."""
        # Make request with different pagination
        response = client.get("/phone/numbers?page=2&limit=25")
        
        # Assertions
        assert response.status_code == 200

    @patch('src.api.routers.phone.VoiceAgentService')
    def test_configure_call_routing_success(self, mock_voice_service_class):
        """Test successful call routing configuration."""
        # Setup mock
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = {
            'id': 'agent-123',
            'name': 'Test Agent'
        }
        
        # Make request
        response = client.post(
            "/phone/numbers/+14151234567/configure",
            json={
                "phone_number": "+14151234567",
                "agent_id": "agent-123",
                "record_calls": True,
                "transcribe_calls": True
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["phone_number"] == "+14151234567"
        assert "configuration" in data
        assert "webhook_urls" in data
        assert "agent_webhook" in data["webhook_urls"]

    @patch('src.api.routers.phone.VoiceAgentService')
    def test_configure_call_routing_agent_not_found(self, mock_voice_service_class):
        """Test call routing configuration with non-existent agent."""
        # Setup mock
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = None
        
        # Make request
        response = client.post(
            "/phone/numbers/+14151234567/configure",
            json={
                "phone_number": "+14151234567",
                "agent_id": "non-existent-agent"
            }
        )
        
        # Assertions
        assert response.status_code == 404
        assert "Specified voice agent not found" in response.json()["detail"]

    @patch('src.api.routers.phone.PhoneService')
    def test_get_service_status_success(self, mock_phone_service_class):
        """Test successful service status retrieval."""
        # Setup mock
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.get_service_status.return_value = {
            'status': 'healthy',
            'service_type': 'real',
            'twilio_status': {
                'account_status': 'active',
                'balance': 100.00
            }
        }
        
        # Make request
        response = client.get("/phone/service/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service_type"] == "real"
        assert "twilio_status" in data
        assert "active_numbers" in data
        assert "last_check" in data

    @patch('src.api.routers.phone.PhoneService')
    def test_get_service_status_error(self, mock_phone_service_class):
        """Test service status with error."""
        # Setup mock to raise exception
        mock_service = MagicMock()
        mock_phone_service_class.return_value = mock_service
        mock_service.get_service_status.side_effect = Exception("Service unavailable")
        
        # Make request
        response = client.get("/phone/service/status")
        
        # Assertions
        assert response.status_code == 500
        assert "Failed to get service status" in response.json()["detail"]

    def test_release_phone_number_success(self):
        """Test successful phone number release."""
        # Make request (currently returns placeholder success)
        response = client.delete("/phone/numbers/+14151234567")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["phone_number"] == "+14151234567"
        assert "message" in data

    def test_bulk_phone_action_success(self):
        """Test successful bulk phone actions."""
        # Make request (currently returns placeholder success)
        response = client.post(
            "/phone/numbers/bulk-action",
            json={
                "phone_numbers": ["+14151234567", "+14151234568"],
                "action": "status",
                "configuration": {}
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["action"] == "status"
        assert "results" in data
        assert "success_count" in data
        assert "error_count" in data
        assert "total_count" in data
        
        assert len(data["results"]) == 2
        assert data["success_count"] == 2
        assert data["error_count"] == 0
        assert data["total_count"] == 2

    def test_bulk_phone_action_empty_list(self):
        """Test bulk phone actions with empty phone number list."""
        # Make request
        response = client.post(
            "/phone/numbers/bulk-action",
            json={
                "phone_numbers": [],
                "action": "status"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] == 0
        assert data["success_count"] == 0
        assert len(data["results"]) == 0


def run_tests():
    """Run all phone API endpoint tests."""
    print("🧪 Running Phone API Endpoint Tests...")
    print("=" * 60)
    
    # Create test instance
    test_instance = TestPhoneAPIEndpoints()
    
    test_methods = [
        ("Search Available Numbers (Success)", test_instance.test_search_available_numbers_success),
        ("Search Available Numbers (Error)", test_instance.test_search_available_numbers_error),
        ("Provision Phone Number (Success)", test_instance.test_provision_phone_number_success),
        ("Provision Phone Number (Agent Not Found)", test_instance.test_provision_phone_number_agent_not_found),
        ("Provision Phone Number (Service Error)", test_instance.test_provision_phone_number_service_error),
        ("Get Phone Number Status (Success)", test_instance.test_get_phone_number_status_success),
        ("Get Phone Number Status (Error)", test_instance.test_get_phone_number_status_error),
        ("List Phone Numbers (Success)", test_instance.test_list_phone_numbers_success),
        ("List Phone Numbers (Pagination)", test_instance.test_list_phone_numbers_pagination),
        ("Configure Call Routing (Success)", test_instance.test_configure_call_routing_success),
        ("Configure Call Routing (Agent Not Found)", test_instance.test_configure_call_routing_agent_not_found),
        ("Get Service Status (Success)", test_instance.test_get_service_status_success),
        ("Get Service Status (Error)", test_instance.test_get_service_status_error),
        ("Release Phone Number (Success)", test_instance.test_release_phone_number_success),
        ("Bulk Phone Action (Success)", test_instance.test_bulk_phone_action_success),
        ("Bulk Phone Action (Empty List)", test_instance.test_bulk_phone_action_empty_list),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_method in test_methods:
        try:
            print(f"📋 Testing: {test_name}")
            test_instance.setup_method()
            test_method()
            test_instance.teardown_method()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            errors.append((test_name, str(e)))
            failed += 1
        print()
    
    # Print summary
    print("=" * 60)
    print(f"📊 TEST SUMMARY:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if errors:
        print(f"\n🔍 FAILURE DETAILS:")
        for test_name, error in errors:
            print(f"• {test_name}: {error}")
    
    return passed, failed, errors


if __name__ == "__main__":
    run_tests()
