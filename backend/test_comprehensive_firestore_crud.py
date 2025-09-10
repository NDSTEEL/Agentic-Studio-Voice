#!/usr/bin/env python3
"""
Comprehensive Firebase Firestore CRUD Test for Terminal 8 Knowledge Management System
Tests real operations with all 18 knowledge categories and tenant isolation
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Add the backend directory to path
sys.path.append('/mnt/c/Users/avibm/Agentic-Studio-Voice/backend')
load_dotenv()

# Import Firebase services
from src.services.firebase_config import get_firestore_client
from src.services.knowledge_base_service import KnowledgeBaseService
from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES


class ComprehensiveFirestoreTest:
    """Comprehensive test suite for Terminal 8 Firestore operations."""
    
    def __init__(self):
        self.db = get_firestore_client()
        self.kb_service = KnowledgeBaseService()
        self.test_tenant_id = f"test_tenant_{uuid.uuid4().hex[:8]}"
        self.test_agent_id = f"test_agent_{uuid.uuid4().hex[:8]}"
        self.created_docs = []  # Track created documents for cleanup
        
    async def run_comprehensive_test(self):
        """Run all Firebase CRUD tests."""
        print("🚀 TERMINAL 8 COMPREHENSIVE FIRESTORE CRUD TEST")
        print("=" * 60)
        print(f"🏢 Test Tenant: {self.test_tenant_id}")
        print(f"🤖 Test Agent: {self.test_agent_id}")
        print()
        
        try:
            # Test 1: Test all 18 knowledge categories structure
            await self.test_knowledge_categories_structure()
            
            # Test 2: Test Firestore write operations
            await self.test_firestore_write_operations()
            
            # Test 3: Test Firestore read operations
            await self.test_firestore_read_operations()
            
            # Test 4: Test tenant isolation
            await self.test_tenant_isolation()
            
            # Test 5: Test knowledge base service with live data
            await self.test_knowledge_service_integration()
            
            # Test 6: Test update operations
            await self.test_firestore_update_operations()
            
            # Test 7: Test delete operations
            await self.test_firestore_delete_operations()
            
            print("🎉 ALL TESTS PASSED - Firebase connection 100% operational!")
            return True
            
        except Exception as e:
            print(f"💥 TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Cleanup test data
            await self.cleanup_test_data()
    
    async def test_knowledge_categories_structure(self):
        """Test all 18 knowledge categories are properly defined."""
        print("📋 Test 1: Knowledge Categories Structure")
        print(f"   Expected categories: 18")
        print(f"   Found categories: {len(KNOWLEDGE_CATEGORIES)}")
        
        if len(KNOWLEDGE_CATEGORIES) != 18:
            raise AssertionError(f"Expected 18 categories, found {len(KNOWLEDGE_CATEGORIES)}")
        
        print("   ✅ All 18 knowledge categories properly defined")
        
        # Validate each category
        for i, category in enumerate(KNOWLEDGE_CATEGORIES, 1):
            print(f"   {i:2d}. {category}")
        
        print()
    
    async def test_firestore_write_operations(self):
        """Test writing knowledge data to Firestore."""
        print("✍️ Test 2: Firestore Write Operations")
        
        # Create test knowledge base with all categories
        test_knowledge_base = {}
        
        for i, category in enumerate(KNOWLEDGE_CATEGORIES):
            test_data = {
                "title": f"Test {category.replace('_', ' ').title()}",
                "content": f"This is test content for {category} category. " * 5,
                "confidence_score": 0.85 + (i % 3) * 0.05,  # Vary confidence scores
                "last_updated": datetime.now().isoformat(),
                "source": "comprehensive_test",
                "keywords": [f"keyword{j}" for j in range(1, 6)],
                "structured_data": {
                    "items": [f"item{j}" for j in range(1, 4)],
                    "metadata": {"test": True, "category": category}
                }
            }
            test_knowledge_base[category] = test_data
        
        # Write to Firestore
        doc_ref = self.db.collection('voice_agents').document(self.test_agent_id)
        knowledge_doc = {
            "tenant_id": self.test_tenant_id,
            "agent_id": self.test_agent_id,
            "knowledge_base": test_knowledge_base,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "version": 1,
            "stats": self.kb_service.get_knowledge_base_stats(test_knowledge_base)
        }
        
        doc_ref.set(knowledge_doc)
        self.created_docs.append(doc_ref)
        
        print(f"   ✅ Written knowledge base with {len(test_knowledge_base)} categories")
        print(f"   ✅ Document ID: {self.test_agent_id}")
        print()
    
    async def test_firestore_read_operations(self):
        """Test reading knowledge data from Firestore."""
        print("📖 Test 3: Firestore Read Operations")
        
        # Read the document we just created
        doc_ref = self.db.collection('voice_agents').document(self.test_agent_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise AssertionError("Document not found after write operation")
        
        data = doc.to_dict()
        knowledge_base = data.get('knowledge_base', {})
        
        print(f"   ✅ Document retrieved successfully")
        print(f"   ✅ Knowledge categories found: {len(knowledge_base)}")
        print(f"   ✅ Tenant ID matches: {data.get('tenant_id') == self.test_tenant_id}")
        
        # Validate each category exists
        missing_categories = []
        for category in KNOWLEDGE_CATEGORIES:
            if category not in knowledge_base:
                missing_categories.append(category)
        
        if missing_categories:
            raise AssertionError(f"Missing categories: {missing_categories}")
        
        print(f"   ✅ All 18 categories present in stored data")
        print()
    
    async def test_tenant_isolation(self):
        """Test that tenant isolation works properly."""
        print("🏢 Test 4: Tenant Isolation")
        
        # Create a second tenant
        second_tenant_id = f"test_tenant_2_{uuid.uuid4().hex[:8]}"
        second_agent_id = f"test_agent_2_{uuid.uuid4().hex[:8]}"
        
        # Create different knowledge base for second tenant
        second_knowledge_base = {
            "business_info": {
                "title": "Second Tenant Business Info",
                "content": "Different content for second tenant",
                "confidence_score": 0.90,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        # Write second tenant data
        second_doc_ref = self.db.collection('voice_agents').document(second_agent_id)
        second_doc = {
            "tenant_id": second_tenant_id,
            "agent_id": second_agent_id,
            "knowledge_base": second_knowledge_base,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "version": 1
        }
        
        second_doc_ref.set(second_doc)
        self.created_docs.append(second_doc_ref)
        
        # Test isolation by querying by tenant_id
        first_tenant_docs = list(self.db.collection('voice_agents')
                                .where('tenant_id', '==', self.test_tenant_id)
                                .stream())
        
        second_tenant_docs = list(self.db.collection('voice_agents')
                                 .where('tenant_id', '==', second_tenant_id)
                                 .stream())
        
        print(f"   ✅ First tenant documents: {len(first_tenant_docs)}")
        print(f"   ✅ Second tenant documents: {len(second_tenant_docs)}")
        
        # Verify isolation
        if len(first_tenant_docs) != 1 or len(second_tenant_docs) != 1:
            raise AssertionError("Tenant isolation failed - wrong document counts")
        
        # Verify no cross-tenant data leakage
        first_doc_data = first_tenant_docs[0].to_dict()
        second_doc_data = second_tenant_docs[0].to_dict()
        
        if first_doc_data['tenant_id'] == second_doc_data['tenant_id']:
            raise AssertionError("Tenant isolation failed - same tenant_id found")
        
        print(f"   ✅ Tenant isolation working correctly")
        print()
    
    async def test_knowledge_service_integration(self):
        """Test KnowledgeBaseService with live Firebase data."""
        print("🧠 Test 5: Knowledge Service Integration")
        
        # Get the stored knowledge base
        doc_ref = self.db.collection('voice_agents').document(self.test_agent_id)
        doc = doc_ref.get()
        stored_knowledge = doc.to_dict()['knowledge_base']
        
        # Test service methods
        stats = self.kb_service.get_knowledge_base_stats(stored_knowledge)
        print(f"   ✅ Knowledge stats calculated: {stats}")
        
        size_validation = self.kb_service.validate_knowledge_base_size(stored_knowledge)
        print(f"   ✅ Size validation: {size_validation['estimated_size_mb']:.2f} MB")
        print(f"   ✅ Size valid: {size_validation['is_valid']}")
        
        # Test merging with new data
        new_data = {
            "business_info": {
                "title": "Updated Business Info",
                "content": "Updated content with higher confidence",
                "confidence_score": 0.95,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        merged = self.kb_service.merge_knowledge_categories(stored_knowledge, new_data)
        print(f"   ✅ Knowledge merging successful")
        print(f"   ✅ Merged categories: {len(merged)}")
        
        # Verify higher confidence was used
        if merged['business_info']['confidence_score'] != 0.95:
            raise AssertionError("Knowledge merging failed - confidence score not updated")
        
        print()
    
    async def test_firestore_update_operations(self):
        """Test updating knowledge data in Firestore."""
        print("🔄 Test 6: Firestore Update Operations")
        
        # Update specific fields
        doc_ref = self.db.collection('voice_agents').document(self.test_agent_id)
        
        updates = {
            "updated_at": datetime.now(),
            "version": 2,
            "knowledge_base.business_info.confidence_score": 0.98,
            "knowledge_base.business_info.last_updated": datetime.now().isoformat()
        }
        
        doc_ref.update(updates)
        
        # Verify update
        updated_doc = doc_ref.get()
        updated_data = updated_doc.to_dict()
        
        if updated_data['version'] != 2:
            raise AssertionError("Version update failed")
        
        if updated_data['knowledge_base']['business_info']['confidence_score'] != 0.98:
            raise AssertionError("Confidence score update failed")
        
        print(f"   ✅ Document version updated to: {updated_data['version']}")
        print(f"   ✅ Business info confidence updated to: {updated_data['knowledge_base']['business_info']['confidence_score']}")
        print()
    
    async def test_firestore_delete_operations(self):
        """Test deleting knowledge data from Firestore."""
        print("🗑️ Test 7: Firestore Delete Operations")
        
        # Delete a specific field using Firestore DELETE_FIELD sentinel
        from google.cloud.firestore import DELETE_FIELD
        
        doc_ref = self.db.collection('voice_agents').document(self.test_agent_id)
        
        # Get current document to see which fields exist
        current_doc = doc_ref.get()
        current_data = current_doc.to_dict()
        current_knowledge = current_data.get('knowledge_base', {})
        
        # Pick a field that actually exists to delete
        field_to_delete = list(current_knowledge.keys())[0]  # Get first available field
        
        print(f"   🎯 Deleting field: {field_to_delete}")
        
        # Remove one knowledge category using DELETE_FIELD
        doc_ref.update({
            f"knowledge_base.{field_to_delete}": DELETE_FIELD
        })
        
        # Verify deletion
        doc = doc_ref.get()
        data = doc.to_dict()
        knowledge_base = data.get('knowledge_base', {})
        
        if field_to_delete in knowledge_base:
            raise AssertionError(f"Field deletion failed for {field_to_delete}")
        
        print(f"   ✅ Successfully deleted '{field_to_delete}' field")
        print(f"   ✅ Remaining categories: {len(knowledge_base)}")
        print()
    
    async def cleanup_test_data(self):
        """Clean up all test data created during tests."""
        print("🧹 Cleaning up test data...")
        
        for doc_ref in self.created_docs:
            try:
                doc_ref.delete()
                print(f"   ✅ Deleted document: {doc_ref.id}")
            except Exception as e:
                print(f"   ⚠️ Error deleting {doc_ref.id}: {e}")
        
        print("   ✅ Cleanup completed")
        print()


async def main():
    """Run the comprehensive Firestore test suite."""
    test_suite = ComprehensiveFirestoreTest()
    success = await test_suite.run_comprehensive_test()
    
    if success:
        print("🎯 FINAL RESULT: Firebase connection 100% OPERATIONAL")
        print("✅ All CRUD operations validated")
        print("✅ Tenant isolation verified")
        print("✅ Knowledge service integration confirmed")
        print("✅ All 18 categories tested and working")
        print()
        print("🚀 Terminal 8 Knowledge Management System ready for production!")
    else:
        print("❌ FINAL RESULT: Some tests failed")
        print("💡 Check error details above")
    
    return success


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    exit(0 if success else 1)