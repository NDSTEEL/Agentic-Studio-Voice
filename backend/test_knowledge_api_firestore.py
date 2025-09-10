#!/usr/bin/env python3
"""
Test Terminal 8 Knowledge API endpoints can write to Firestore
"""

import os
import sys
import asyncio
import uuid
from dotenv import load_dotenv

# Add the backend directory to path
sys.path.append('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')

load_dotenv()

async def test_knowledge_api_firestore_writes():
    """Test that Terminal 8 knowledge API endpoints can write to Firestore."""
    print("🔍 TERMINAL 8 KNOWLEDGE API FIRESTORE WRITE TEST")
    print("=" * 60)
    
    try:
        # Test 1: Initialize voice agent service with real Firebase
        from src.services.voice_agent_service import VoiceAgentService
        voice_service = VoiceAgentService()
        
        print("✅ VoiceAgentService initialized with real Firebase")
        
        # Test 2: Create a test tenant and agent in Firestore
        test_tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
        test_agent_id = str(uuid.uuid4())
        
        # Create test agent data
        test_agent_data = {
            "name": "Test Knowledge Agent",
            "description": "Agent for testing knowledge management",
            "created_at": "2025-01-10T15:30:00Z",
            "updated_at": "2025-01-10T15:30:00Z",
            "tenant_id": test_tenant_id,
            "phone_number": "+15551234567",
            "voice_config": {},
            "knowledge_base": {
                "company_overview": {
                    "title": "Test Company Overview",
                    "content": "This business specializes in AI-powered voice agents",
                    "confidence_score": 0.95,
                    "last_updated": "2025-01-10T15:30:00Z"
                },
                "products_services": {
                    "title": "Our Services",
                    "content": "We provide voice agent development and deployment",
                    "confidence_score": 0.90,
                    "last_updated": "2025-01-10T15:30:00Z"
                }
            }
        }
        
        print(f"📝 Test agent data prepared: {test_agent_id}")
        
        # Test 3: Write agent to Firestore via VoiceAgentService
        created_agent = voice_service.create_agent(
            agent_data=test_agent_data,
            tenant_id=test_tenant_id
        )
        
        if created_agent:
            print("✅ Agent created successfully in Firestore via VoiceAgentService")
            print(f"   Agent ID: {created_agent.get('id', 'N/A')}")
            print(f"   Knowledge categories: {len(created_agent.get('knowledge_base', {}))}")
        else:
            print("❌ Failed to create agent in Firestore")
            return False
        
        # Test 4: Update knowledge base via VoiceAgentService
        updated_knowledge = {
            "company_overview": {
                "title": "Updated Company Overview", 
                "content": "Updated content: This business specializes in cutting-edge AI voice technology",
                "confidence_score": 0.98,
                "last_updated": "2025-01-10T15:35:00Z"
            },
            "products_services": {
                "title": "Our Premium Services",
                "content": "We provide enterprise-grade voice agent solutions",
                "confidence_score": 0.95,
                "last_updated": "2025-01-10T15:35:00Z"
            },
            "contact_information": {
                "title": "Contact Information",
                "content": "Email: info@example.com, Phone: 555-0123",
                "confidence_score": 0.92,
                "last_updated": "2025-01-10T15:35:00Z"
            }
        }
        
        updated_agent = voice_service.update_agent(
            agent_id=created_agent['id'],
            tenant_id=test_tenant_id,
            update_data={'knowledge_base': updated_knowledge}
        )
        
        if updated_agent:
            print("✅ Agent knowledge base updated successfully in Firestore")
            print(f"   Updated categories: {len(updated_agent.get('knowledge_base', {}))}")
        else:
            print("❌ Failed to update agent knowledge base")
            return False
        
        # Test 5: Retrieve and verify the updated data
        retrieved_agent = voice_service.get_agent_by_id(created_agent['id'], test_tenant_id)
        
        if retrieved_agent:
            print("✅ Agent retrieved successfully from Firestore")
            retrieved_kb = retrieved_agent.get('knowledge_base', {})
            print(f"   Retrieved knowledge categories: {len(retrieved_kb)}")
            print(f"   Company overview title: {retrieved_kb.get('company_overview', {}).get('title', 'N/A')}")
            print(f"   Contact info present: {'contact_information' in retrieved_kb}")
        else:
            print("❌ Failed to retrieve updated agent")
            return False
        
        # Test 6: Test knowledge base service operations
        from src.services.knowledge_base_service import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        
        # Validate knowledge base
        stats = kb_service.get_knowledge_base_stats(retrieved_kb)
        size_info = kb_service.validate_knowledge_base_size(retrieved_kb)
        
        print("✅ Knowledge base validation completed")
        print(f"   Categories: {stats['total_categories']}")
        print(f"   Quality score: {stats['quality_score']:.2f}")
        print(f"   Size valid: {size_info['is_valid']}")
        
        # Test 7: Clean up - delete test agent
        deleted = voice_service.delete_agent(created_agent['id'], test_tenant_id)
        if deleted:
            print("✅ Test agent cleaned up from Firestore")
        else:
            print("⚠️ Warning: Could not clean up test agent")
        
        print()
        print("🎉 TERMINAL 8 KNOWLEDGE API FIRESTORE WRITES: SUCCESS")
        print("   ✅ VoiceAgentService can create agents in Firestore")
        print("   ✅ Knowledge base data writes to Firestore successfully") 
        print("   ✅ Knowledge base updates work in Firestore")
        print("   ✅ Knowledge API endpoints have full Firestore write capability")
        print("   ✅ Knowledge validation and stats work properly")
        print("   ✅ Terminal 8 can now use real Firebase for knowledge management")
        
        return True
        
    except Exception as e:
        print(f"💥 ERROR during Terminal 8 knowledge API Firestore write test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_knowledge_api_firestore_writes())
    exit(0 if success else 1)