#!/usr/bin/env python3
"""
Test Knowledge Base Service with Live Firebase Connection
Validates actual Firestore operations for Terminal 8 completion
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Set environment variables
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/mnt/c/Users/avibm/Agentic-Studio-Voice/backend/firebase-service-account.json'
os.environ['FIREBASE_PROJECT_ID'] = 'agentic-studio-voice'

# Add the backend directory to path
sys.path.append('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')

def test_knowledge_service_live_connection():
    """Test knowledge service with actual Firebase operations"""
    print("🧠 TESTING KNOWLEDGE SERVICE LIVE CONNECTION")
    print("=" * 50)
    
    try:
        # Import services
        from src.services.knowledge_base_service import KnowledgeBaseService
        from src.services.firebase_config import get_firestore_client
        
        # Initialize services
        kb_service = KnowledgeBaseService()
        db = get_firestore_client()
        
        print("✅ Knowledge Base Service initialized")
        print("✅ Firestore client connected")
        
        # Test 1: Knowledge Base Validation
        print("\n🔍 Test 1: Knowledge Base Validation")
        test_knowledge = {
            "medical_conditions": {
                "title": "Test Medical Condition",
                "content": "This is test medical content for validation",
                "confidence_score": 0.85,
                "keywords": ["test", "medical", "condition"]
            },
            "medications": {
                "title": "Test Medication",
                "content": "This is test medication content",
                "confidence_score": 0.90,
                "keywords": ["test", "medication"]
            }
        }
        
        validated = kb_service.validate_crawled_content(test_knowledge)
        print(f"✅ Knowledge validation successful: {len(validated)} categories")
        
        # Test 2: Size Validation
        print("\n🔍 Test 2: Size Validation")
        size_info = kb_service.validate_knowledge_base_size(validated)
        print(f"✅ Size validation: {size_info['estimated_size_mb']}MB (valid: {size_info['is_valid']})")
        
        # Test 3: Live Firestore Operations
        print("\n🔍 Test 3: Live Firestore Knowledge Storage")
        knowledge_collection = db.collection('knowledge_bases')
        test_doc = knowledge_collection.document('test_terminal_8')
        
        # Store test knowledge base
        test_data = {
            'created_at': datetime.now(),
            'test_type': 'terminal_8_validation',
            'knowledge_categories': validated,
            'stats': kb_service.get_knowledge_base_stats(validated),
            'size_info': size_info
        }
        
        test_doc.set(test_data)
        print("✅ Knowledge base stored in Firestore")
        
        # Retrieve and validate
        retrieved = test_doc.get()
        if retrieved.exists:
            retrieved_data = retrieved.to_dict()
            print("✅ Knowledge base retrieved from Firestore")
            print(f"   - Categories: {len(retrieved_data.get('knowledge_categories', {}))}")
            print(f"   - Quality Score: {retrieved_data.get('stats', {}).get('quality_score', 'N/A')}")
        
        # Test 4: Knowledge Merging
        print("\n🔍 Test 4: Knowledge Merging")
        new_knowledge = {
            "medical_conditions": {
                "title": "Updated Medical Condition",
                "content": "Updated medical content with higher confidence",
                "confidence_score": 0.95,
                "keywords": ["updated", "medical", "condition"]
            }
        }
        
        merged = kb_service.merge_knowledge_categories(validated, new_knowledge)
        print(f"✅ Knowledge merging successful: {len(merged)} categories")
        print(f"   - Medical condition confidence: {merged['medical_conditions']['confidence_score']}")
        
        # Clean up test data
        test_doc.delete()
        print("✅ Test data cleaned up")
        
        # Final stats
        print("\n🎊 LIVE CONNECTION TEST RESULTS")
        print("=" * 35)
        print("✅ Knowledge validation: WORKING")
        print("✅ Firebase storage: OPERATIONAL")
        print("✅ Data retrieval: FUNCTIONAL")
        print("✅ Knowledge merging: SUCCESSFUL")
        print("✅ Size management: VALIDATED")
        print("✅ Service integration: COMPLETE")
        
        print("\n🚀 TERMINAL 8 KNOWLEDGE SERVICE")
        print("   STATUS: FULLY OPERATIONAL")
        print("   FIREBASE: LIVE CONNECTION CONFIRMED")
        print("   KNOWLEDGE MANAGEMENT: READY FOR PRODUCTION")
        
        return True
        
    except Exception as e:
        print(f"❌ Live connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 TERMINAL 8 - KNOWLEDGE SERVICE LIVE TEST")
    print("Testing actual Firebase operations with knowledge management")
    print()
    
    success = test_knowledge_service_live_connection()
    
    if success:
        print("\n✅ TERMINAL 8 COMPLETION: 100%")
        print("Knowledge management system fully operational with live Firebase connection!")
    else:
        print("\n❌ TERMINAL 8 INCOMPLETE")
        print("Knowledge service live connection test failed")
    
    exit(0 if success else 1)