"""
Test for T002: Database Models & Migrations
TDD: Write failing tests first, then implement models
"""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Import models (will fail initially)
try:
    from src.models.tenant import Tenant
    from src.models.agent import VoiceAgent
    from src.models.knowledge import KnowledgeBase
    from src.database.connection import get_database_url, create_tables
except ImportError:
    # Models don't exist yet - tests will fail as expected
    pass

class TestTenantModel:
    """Test tenant model with RLS requirements"""
    
    def test_tenant_model_exists(self):
        """Test that Tenant model can be imported and instantiated"""
        tenant = Tenant(
            name="Test Company",
            subdomain="testco"
        )
        assert tenant.name == "Test Company"
        assert tenant.subdomain == "testco"
        assert tenant.id is None  # Not saved yet
    
    def test_tenant_model_has_required_fields(self):
        """Test that Tenant model has all required fields"""
        tenant = Tenant()
        
        # Test required columns exist
        assert hasattr(tenant, 'id')
        assert hasattr(tenant, 'name')
        assert hasattr(tenant, 'subdomain')
        assert hasattr(tenant, 'created_at')
        assert hasattr(tenant, 'updated_at')
    
    def test_tenant_model_relationships(self):
        """Test that Tenant has proper relationships"""
        tenant = Tenant(name="Test", subdomain="test")
        
        # Test relationships exist
        assert hasattr(tenant, 'voice_agents')
        assert hasattr(tenant, 'knowledge_bases')

class TestVoiceAgentModel:
    """Test voice agent model with tenant isolation"""
    
    def test_voice_agent_model_exists(self):
        """Test that VoiceAgent model can be imported and instantiated"""
        tenant_id = uuid.uuid4()
        agent = VoiceAgent(
            tenant_id=tenant_id,
            name="Test Agent",
            phone_number="+1234567890",
            elevenlabs_voice_id="test_voice_123"
        )
        assert agent.name == "Test Agent"
        assert agent.tenant_id == tenant_id
        assert agent.phone_number == "+1234567890"
    
    def test_voice_agent_required_fields(self):
        """Test that VoiceAgent has all required fields"""
        agent = VoiceAgent()
        
        # Test required columns exist
        assert hasattr(agent, 'id')
        assert hasattr(agent, 'tenant_id')
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'phone_number')
        assert hasattr(agent, 'elevenlabs_voice_id')
        assert hasattr(agent, 'knowledge_categories')
        assert hasattr(agent, 'configuration')
        assert hasattr(agent, 'status')
        assert hasattr(agent, 'created_at')
        assert hasattr(agent, 'updated_at')
    
    def test_voice_agent_knowledge_categories_structure(self):
        """Test that knowledge_categories field has 18-category structure"""
        agent = VoiceAgent()
        
        # Should have JSONB field for 18 categories
        expected_categories = [
            'business_information', 'products_services', 'support_faq',
            'company_history', 'policies', 'processes_procedures',
            'events_news', 'technical_specs', 'pricing_billing',
            'inventory_stock', 'legal_compliance', 'partnerships',
            'marketing_promotions', 'training_education', 'quality_standards',
            'feedback_reviews', 'emergency_contact', 'custom_business_logic'
        ]
        
        # Test that model supports setting knowledge categories
        knowledge_data = {cat: {"content": f"Test content for {cat}"} for cat in expected_categories}
        agent.knowledge_categories = knowledge_data
        assert agent.knowledge_categories is not None

class TestKnowledgeBaseModel:
    """Test knowledge base model with 18-category validation"""
    
    def test_knowledge_base_model_exists(self):
        """Test that KnowledgeBase model can be imported and instantiated"""
        tenant_id = uuid.uuid4()
        agent_id = uuid.uuid4()
        
        knowledge = KnowledgeBase(
            tenant_id=tenant_id,
            agent_id=agent_id,
            category="business_information",
            content={"data": "test business info"}
        )
        
        assert knowledge.tenant_id == tenant_id
        assert knowledge.agent_id == agent_id
        assert knowledge.category == "business_information"
    
    def test_knowledge_base_required_fields(self):
        """Test that KnowledgeBase has all required fields"""
        knowledge = KnowledgeBase()
        
        # Test required columns exist
        assert hasattr(knowledge, 'id')
        assert hasattr(knowledge, 'tenant_id')
        assert hasattr(knowledge, 'agent_id')
        assert hasattr(knowledge, 'category')
        assert hasattr(knowledge, 'content')
        assert hasattr(knowledge, 'meta_data')
        assert hasattr(knowledge, 'created_at')
        assert hasattr(knowledge, 'updated_at')
    
    def test_knowledge_base_valid_categories(self):
        """Test that KnowledgeBase validates categories"""
        valid_categories = [
            'business_information', 'products_services', 'support_faq',
            'company_history', 'policies', 'processes_procedures',
            'events_news', 'technical_specs', 'pricing_billing',
            'inventory_stock', 'legal_compliance', 'partnerships',
            'marketing_promotions', 'training_education', 'quality_standards',
            'feedback_reviews', 'emergency_contact', 'custom_business_logic'
        ]
        
        # Each category should be valid
        for category in valid_categories:
            knowledge = KnowledgeBase(category=category)
            assert knowledge.category == category

class TestDatabaseConnection:
    """Test database connection and table creation"""
    
    def test_database_url_function_exists(self):
        """Test that get_database_url function exists"""
        db_url = get_database_url()
        assert db_url is not None
        assert isinstance(db_url, str)
        assert "postgresql" in db_url
    
    def test_create_tables_function_exists(self):
        """Test that create_tables function exists"""
        # This should not raise an ImportError
        from src.database.connection import create_tables
        assert callable(create_tables)

class TestAlembicMigrations:
    """Test Alembic migration setup"""
    
    def test_alembic_config_exists(self):
        """Test that alembic.ini exists in backend directory"""
        import os
        alembic_config_path = "alembic.ini"
        assert os.path.exists(alembic_config_path), "alembic.ini should exist"
    
    def test_migrations_directory_exists(self):
        """Test that migrations directory exists"""
        import os
        migrations_dir = "src/database/migrations"
        assert os.path.exists(migrations_dir), "Migrations directory should exist"
        
        # Should contain alembic files
        env_py = os.path.join(migrations_dir, "env.py")
        assert os.path.exists(env_py), "env.py should exist in migrations"

class TestRowLevelSecurity:
    """Test RLS policies and tenant isolation"""
    
    def test_rls_policies_file_exists(self):
        """Test that RLS policies configuration exists"""
        import os
        rls_file = "src/database/rls_policies.py"
        assert os.path.exists(rls_file), "RLS policies file should exist"
    
    def test_tenant_isolation_setup(self):
        """Test that tenant isolation is properly configured"""
        from src.database.rls_policies import setup_rls_policies
        
        # Function should exist and be callable
        assert callable(setup_rls_policies)

if __name__ == "__main__":
    # Run tests to see them fail first (Red phase)
    pytest.main([__file__, "-v"])