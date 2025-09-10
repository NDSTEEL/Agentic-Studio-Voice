"""
Comprehensive Phone API Endpoint Test Suite
Tests all phone API endpoints using FastAPI TestClient to ensure they work correctly.
"""

import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch, MagicMock, AsyncMock
import os


def setup_test_environment():
    """Setup test environment variables."""
    os.environ.update({
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'TWILIO_AUTH_TOKEN': 'test_token',
        'WEBHOOK_BASE_URL': 'https://example.com'
    })


def create_test_app():
    """Create test FastAPI app with phone router."""
    from src.api.routers.phone import router
    
    app = FastAPI()
    app.include_router(router)
    
    # Override auth dependency
    def mock_get_current_user():
        return {
            "tenant_id": "test-tenant-123",
            "user_id": "test-user-456",
            "email": "test@example.com"
        }
    
    from src.api.dependencies.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    return app


def run_comprehensive_phone_api_tests():
    """Run comprehensive phone API endpoint tests."""
    print("🧪 Running Comprehensive Phone API Endpoint Tests")
    print("=" * 70)
    
    # Setup environment
    setup_test_environment()
    
    # Create test app
    app = create_test_app()
    client = TestClient(app)
    
    passed = 0
    failed = 0
    errors = []
    
    # Test cases
    test_cases = [
        # Phone number search tests
        {
            "name": "Search Available Numbers - Basic",
            "method": "GET",
            "url": "/phone/numbers/available",
            "expected_status": 200,
            "expected_keys": ["available_numbers", "search_criteria", "total_found"],
            "mock_setup": lambda: patch_search_numbers_success()
        },
        {
            "name": "Search Available Numbers - With Parameters",
            "method": "GET", 
            "url": "/phone/numbers/available?area_code=415&contains=123&limit=5",
            "expected_status": 200,
            "expected_keys": ["available_numbers", "search_criteria", "total_found"],
            "mock_setup": lambda: patch_search_numbers_success()
        },
        {
            "name": "Search Available Numbers - Service Error",
            "method": "GET",
            "url": "/phone/numbers/available",
            "expected_status": 500,
            "mock_setup": lambda: patch_search_numbers_error()
        },
        
        # Phone number provisioning tests
        {
            "name": "Provision Phone Number - Success",
            "method": "POST",
            "url": "/phone/numbers/provision",
            "json": {
                "phone_number": "+14151234567",
                "friendly_name": "Test Number"
            },
            "expected_status": 200,
            "expected_keys": ["status", "phone_number", "phone_sid"],
            "mock_setup": lambda: patch_provision_success()
        },
        {
            "name": "Provision Phone Number - With Agent",
            "method": "POST",
            "url": "/phone/numbers/provision", 
            "json": {
                "phone_number": "+14151234567",
                "agent_id": "agent-123"
            },
            "expected_status": 200,
            "mock_setup": lambda: patch_provision_with_agent_success()
        },
        {
            "name": "Provision Phone Number - Agent Not Found",
            "method": "POST",
            "url": "/phone/numbers/provision",
            "json": {
                "phone_number": "+14151234567",
                "agent_id": "non-existent-agent"
            },
            "expected_status": 404,
            "mock_setup": lambda: patch_provision_agent_not_found()
        },
        {
            "name": "Provision Phone Number - Service Error",
            "method": "POST",
            "url": "/phone/numbers/provision",
            "json": {"phone_number": "+14151234567"},
            "expected_status": 400,
            "mock_setup": lambda: patch_provision_service_error()
        },
        
        # Phone number status tests
        {
            "name": "Get Phone Number Status - Success",
            "method": "GET",
            "url": "/phone/numbers/+14151234567/status",
            "expected_status": 200,
            "expected_keys": ["phone_number", "status", "capabilities"],
            "mock_setup": lambda: patch_status_success()
        },
        {
            "name": "Get Phone Number Status - Service Error",
            "method": "GET",
            "url": "/phone/numbers/+14151234567/status",
            "expected_status": 500,
            "mock_setup": lambda: patch_status_error()
        },
        
        # Phone number listing tests
        {
            "name": "List Phone Numbers - Basic",
            "method": "GET",
            "url": "/phone/numbers",
            "expected_status": 200,
            "expected_keys": ["phone_numbers", "total", "active_count", "tenant_id"],
            "mock_setup": lambda: None  # Uses default placeholder response
        },
        {
            "name": "List Phone Numbers - With Pagination",
            "method": "GET", 
            "url": "/phone/numbers?page=2&limit=25",
            "expected_status": 200,
            "expected_keys": ["phone_numbers", "total", "active_count"],
            "mock_setup": lambda: None
        },
        
        # Call routing configuration tests
        {
            "name": "Configure Call Routing - Success",
            "method": "POST",
            "url": "/phone/numbers/+14151234567/configure",
            "json": {
                "phone_number": "+14151234567",
                "record_calls": True,
                "transcribe_calls": True
            },
            "expected_status": 200,
            "expected_keys": ["status", "phone_number", "configuration", "webhook_urls"],
            "mock_setup": lambda: None  # Uses default success response
        },
        {
            "name": "Configure Call Routing - With Agent",
            "method": "POST",
            "url": "/phone/numbers/+14151234567/configure",
            "json": {
                "phone_number": "+14151234567",
                "agent_id": "agent-123"
            },
            "expected_status": 200,
            "mock_setup": lambda: patch_configure_with_agent_success()
        },
        {
            "name": "Configure Call Routing - Agent Not Found",
            "method": "POST",
            "url": "/phone/numbers/+14151234567/configure",
            "json": {
                "phone_number": "+14151234567",
                "agent_id": "non-existent-agent"
            },
            "expected_status": 404,
            "mock_setup": lambda: patch_configure_agent_not_found()
        },
        
        # Service status tests
        {
            "name": "Get Service Status - Success", 
            "method": "GET",
            "url": "/phone/service/status",
            "expected_status": 200,
            "expected_keys": ["status", "service_type", "active_numbers", "last_check"],
            "mock_setup": lambda: patch_service_status_success()
        },
        {
            "name": "Get Service Status - Error",
            "method": "GET",
            "url": "/phone/service/status", 
            "expected_status": 500,
            "mock_setup": lambda: patch_service_status_error()
        },
        
        # Phone number release tests
        {
            "name": "Release Phone Number - Success",
            "method": "DELETE",
            "url": "/phone/numbers/+14151234567",
            "expected_status": 200,
            "expected_keys": ["status", "phone_number", "message"],
            "mock_setup": lambda: None  # Uses default success response
        },
        
        # Bulk operations tests
        {
            "name": "Bulk Phone Action - Success",
            "method": "POST",
            "url": "/phone/numbers/bulk-action",
            "json": {
                "phone_numbers": ["+14151234567", "+14151234568"],
                "action": "status"
            },
            "expected_status": 200,
            "expected_keys": ["action", "results", "success_count", "error_count", "total_count"],
            "mock_setup": lambda: None  # Uses default success response
        },
        {
            "name": "Bulk Phone Action - Empty List",
            "method": "POST",
            "url": "/phone/numbers/bulk-action",
            "json": {
                "phone_numbers": [],
                "action": "status"
            },
            "expected_status": 200,
            "mock_setup": lambda: None
        }
    ]
    
    # Run all test cases
    for test_case in test_cases:
        try:
            print(f"\n📋 Testing: {test_case['name']}")
            
            # Setup mocks if needed
            mock_context = test_case.get('mock_setup', lambda: None)()
            
            # Make request
            if test_case['method'] == 'GET':
                response = client.get(test_case['url'])
            elif test_case['method'] == 'POST':
                response = client.post(
                    test_case['url'],
                    json=test_case.get('json', {})
                )
            elif test_case['method'] == 'DELETE':
                response = client.delete(test_case['url'])
            else:
                raise ValueError(f"Unsupported method: {test_case['method']}")
            
            # Check status code
            if response.status_code != test_case['expected_status']:
                print(f"❌ FAILED: Expected status {test_case['expected_status']}, got {response.status_code}")
                print(f"   Response: {response.json()}")
                failed += 1
                errors.append((test_case['name'], f"Status code mismatch: {response.status_code}"))
                continue
            
            # Check response keys for successful responses
            if response.status_code == 200 and 'expected_keys' in test_case:
                data = response.json()
                missing_keys = []
                for key in test_case['expected_keys']:
                    if key not in data:
                        missing_keys.append(key)
                
                if missing_keys:
                    print(f"❌ FAILED: Missing response keys: {missing_keys}")
                    failed += 1
                    errors.append((test_case['name'], f"Missing keys: {missing_keys}"))
                    continue
            
            print(f"✅ PASSED: {test_case['name']}")
            passed += 1
            
            # Cleanup mocks
            if mock_context:
                if hasattr(mock_context, 'stop'):
                    mock_context.stop()
                elif hasattr(mock_context, '__exit__'):
                    mock_context.__exit__(None, None, None)
            
        except Exception as e:
            print(f"❌ ERROR: {test_case['name']} - {str(e)}")
            failed += 1
            errors.append((test_case['name'], str(e)))
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if errors:
        print(f"\n🔍 FAILURE DETAILS:")
        for test_name, error in errors:
            print(f"• {test_name}: {error}")
    
    # Analysis
    success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
    
    print(f"\n🎯 PHONE API ENDPOINT ANALYSIS:")
    print("=" * 50)
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ Phone API endpoints are highly functional")
        print("✅ All core operations working correctly")
        print("✅ Error handling is properly implemented")
    elif success_rate >= 70:
        print("⚠️  Phone API endpoints are mostly functional")
        print("⚠️  Some endpoints may need attention")
        print("⚠️  Minor issues detected")
    else:
        print("❌ Phone API endpoints have significant issues")
        print("❌ Major functionality problems detected")
        print("❌ Requires immediate attention")
    
    return passed, failed, errors


# Mock setup functions
def patch_search_numbers_success():
    """Mock successful phone number search."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.search_available_numbers = AsyncMock(return_value=[
            {
                'phone_number': '+14151234567',
                'friendly_name': 'Test Number',
                'capabilities': {'voice': True, 'sms': True},
                'locality': 'San Francisco',
                'region': 'CA',
                'iso_country': 'US', 
                'price': '$1.00'
            }
        ])


def patch_search_numbers_error():
    """Mock phone number search error."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.search_available_numbers = AsyncMock(
            side_effect=Exception("Twilio API error")
        )


def patch_provision_success():
    """Mock successful phone number provisioning."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.provision_phone_number = AsyncMock(return_value={
            'status': 'success',
            'phone_number': '+14151234567',
            'phone_sid': 'PN123456789',
            'friendly_name': 'Test Number',
            'capabilities': {'voice': True, 'sms': True}
        })


def patch_provision_with_agent_success():
    """Mock successful provisioning with agent."""
    patch1 = patch('src.api.routers.phone.PhoneService')
    patch2 = patch('src.api.routers.phone.VoiceAgentService')
    
    mock_phone_service_class = patch1.start()
    mock_voice_service_class = patch2.start()
    
    mock_phone_service = MagicMock()
    mock_phone_service_class.return_value = mock_phone_service
    mock_phone_service.provision_phone_number = AsyncMock(return_value={
        'status': 'success',
        'phone_number': '+14151234567',
        'phone_sid': 'PN123456789'
    })
    
    mock_voice_service = MagicMock()
    mock_voice_service_class.return_value = mock_voice_service
    mock_voice_service.get_agent_by_id.return_value = {
        'id': 'agent-123',
        'name': 'Test Agent'
    }
    
    class MockContext:
        def stop(self):
            patch1.stop()
            patch2.stop()
    
    return MockContext()


def patch_provision_agent_not_found():
    """Mock provisioning with non-existent agent."""
    return patch('src.api.routers.phone.VoiceAgentService') as mock_voice_service_class:
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = None


def patch_provision_service_error():
    """Mock provisioning service error."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.provision_phone_number = AsyncMock(return_value={
            'status': 'error',
            'error': 'Phone number not available'
        })


def patch_status_success():
    """Mock successful status check."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_service_status.return_value = {
            'status': 'healthy',
            'service_type': 'real'
        }


def patch_status_error():
    """Mock status check error."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_service_status.side_effect = Exception("Service unavailable")


def patch_configure_with_agent_success():
    """Mock successful configuration with agent."""
    return patch('src.api.routers.phone.VoiceAgentService') as mock_voice_service_class:
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = {
            'id': 'agent-123',
            'name': 'Test Agent'
        }


def patch_configure_agent_not_found():
    """Mock configuration with non-existent agent."""
    return patch('src.api.routers.phone.VoiceAgentService') as mock_voice_service_class:
        mock_voice_service = MagicMock()
        mock_voice_service_class.return_value = mock_voice_service
        mock_voice_service.get_agent_by_id.return_value = None


def patch_service_status_success():
    """Mock successful service status."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_service_status.return_value = {
            'status': 'healthy',
            'service_type': 'real',
            'twilio_status': {'account_status': 'active'}
        }


def patch_service_status_error():
    """Mock service status error."""
    return patch('src.api.routers.phone.PhoneService') as mock_service_class:
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.get_service_status.side_effect = Exception("Service unavailable")


if __name__ == "__main__":
    run_comprehensive_phone_api_tests()
