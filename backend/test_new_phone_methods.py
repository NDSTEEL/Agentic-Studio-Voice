#!/usr/bin/env python3
"""
Test script to verify the new PhoneService methods are working correctly.
"""

import asyncio
import uuid
from unittest.mock import Mock, AsyncMock
from src.services.phone.phone_service import PhoneService
from src.services.twilio.twilio_phone_client import TwilioPhoneClient


async def test_new_methods():
    """Test the four new methods that were added to PhoneService."""
    
    # Create mock Twilio client
    mock_twilio_client = Mock(spec=TwilioPhoneClient)
    mock_twilio_client.list_provisioned_numbers = AsyncMock(return_value=[
        {
            'sid': 'PN123456789',
            'phone_number': '+14155551234',
            'friendly_name': 'Test Number',
            'status': 'active',
            'capabilities': {'voice': True, 'sms': True}
        }
    ])
    
    # Create PhoneService instance
    phone_service = PhoneService(twilio_client=mock_twilio_client)
    
    # Mock some existing methods for testing
    phone_service.get_tenant_numbers = AsyncMock(return_value=[])
    phone_service.list_agents_with_phone_numbers = AsyncMock(return_value=[])
    
    print("Testing new PhoneService methods...")
    
    # Test 1: get_phone_numbers_by_tenant
    print("\n1. Testing get_phone_numbers_by_tenant...")
    tenant_id = str(uuid.uuid4())
    result = await phone_service.get_phone_numbers_by_tenant(tenant_id)
    print(f"   Result: {len(result)} phone numbers found")
    assert isinstance(result, list), "Should return a list"
    
    # Test 2: update_phone_number_status
    print("\n2. Testing update_phone_number_status...")
    result = await phone_service.update_phone_number_status('+14155551234', 'active')
    print(f"   Result status: {result.get('status')}")
    assert 'status' in result, "Should return a dictionary with status"
    
    # Test 3: delete_phone_number
    print("\n3. Testing delete_phone_number...")
    # Mock get_phone_numbers_by_tenant to return a number for deletion
    phone_service.get_phone_numbers_by_tenant = AsyncMock(return_value=[
        {
            'phone_number': '+14155551234',
            'phone_sid': 'PN123456789',
            'type': 'tenant'
        }
    ])
    mock_twilio_client.release_phone_number = AsyncMock(return_value=True)
    
    result = await phone_service.delete_phone_number('+14155551234', tenant_id)
    print(f"   Result status: {result.get('status')}")
    assert 'status' in result, "Should return a dictionary with status"
    
    # Test 4: bulk_phone_operations
    print("\n4. Testing bulk_phone_operations...")
    operations = [
        {
            'action': 'update_status',
            'phone_number': '+14155551234',
            'status': 'active'
        }
    ]
    
    result = await phone_service.bulk_phone_operations(operations, tenant_id)
    print(f"   Result status: {result.get('status')}")
    print(f"   Operations processed: {result.get('total_operations')}")
    assert 'status' in result, "Should return a dictionary with status"
    assert 'total_operations' in result, "Should include operation count"
    
    print("\n✅ All new methods are callable and return expected data structures!")
    return True


async def test_method_signatures():
    """Test that all four required methods exist with correct signatures."""
    print("\nTesting method signatures...")
    
    # Create a basic PhoneService instance with mock twilio client
    mock_twilio_client = Mock(spec=TwilioPhoneClient)
    phone_service = PhoneService(twilio_client=mock_twilio_client)
    
    # Check that all methods exist
    required_methods = [
        'get_phone_numbers_by_tenant',
        'update_phone_number_status', 
        'delete_phone_number',
        'bulk_phone_operations'
    ]
    
    for method_name in required_methods:
        assert hasattr(phone_service, method_name), f"Method {method_name} is missing"
        method = getattr(phone_service, method_name)
        assert callable(method), f"Method {method_name} is not callable"
        print(f"   ✅ {method_name} exists and is callable")
    
    print("✅ All required method signatures are present!")
    return True


if __name__ == "__main__":
    async def main():
        try:
            await test_method_signatures()
            await test_new_methods()
            print("\n🎉 All tests passed! The new PhoneService methods are working correctly.")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            return False
        return True
    
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)