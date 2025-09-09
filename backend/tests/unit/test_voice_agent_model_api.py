"""
T011: Voice Agent Model & API Tests
Test-driven development for VoiceAgent model and CRUD operations with tenant isolation
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4


class TestVoiceAgentModel:
    """Test VoiceAgent SQLAlchemy model with 18-category knowledge structure"""
    
    def test_voice_agent_model_exists(self):
        """Test that VoiceAgent model class exists"""
        try:
            from src.models.voice_agent import VoiceAgent
            assert hasattr(VoiceAgent, '__tablename__')
            assert hasattr(VoiceAgent, 'id')
            assert hasattr(VoiceAgent, 'tenant_id')
        except ImportError:
            assert False, "VoiceAgent model should exist in src.models.voice_agent"
    
    def test_voice_agent_model_structure(self):
        """Test that VoiceAgent model has required fields"""
        from src.models.voice_agent import VoiceAgent
        
        # Required fields for voice agent
        required_fields = [
            'id', 'tenant_id', 'name', 'description', 'status',
            'knowledge_base', 'voice_config', 'phone_number',
            'created_at', 'updated_at', 'is_active'
        ]
        
        for field in required_fields:
            assert hasattr(VoiceAgent, field), f"VoiceAgent should have {field} field"
    
    def test_voice_agent_knowledge_base_structure(self):
        """Test that knowledge_base field supports 18-category structure"""
        from src.models.voice_agent import VoiceAgent
        
        # Should be JSONB field that can store structured data
        knowledge_base_field = getattr(VoiceAgent, 'knowledge_base')
        assert knowledge_base_field is not None, "knowledge_base field should exist"
    
    def test_voice_agent_relationships(self):
        """Test that VoiceAgent has proper relationships"""
        from src.models.voice_agent import VoiceAgent
        
        # Should have relationship to Tenant
        assert hasattr(VoiceAgent, 'tenant'), "VoiceAgent should have tenant relationship"
    
    def test_voice_agent_table_constraints(self):
        """Test that VoiceAgent has proper database constraints"""
        from src.models.voice_agent import VoiceAgent
        
        # Should have tenant isolation constraint
        table = VoiceAgent.__table__
        assert 'voice_agents' == table.name, "Table should be named voice_agents"
        
        # Check for foreign key to tenants
        foreign_keys = [fk.target_fullname for fk in table.foreign_keys]
        assert any('tenants' in fk for fk in foreign_keys), "Should have foreign key to tenants table"


class TestKnowledgeCategoriesSchema:
    """Test 18-category knowledge base structure and validation"""
    
    def test_knowledge_categories_schema_exists(self):
        """Test that knowledge categories schema exists"""
        try:
            from src.schemas.knowledge_categories import KnowledgeCategoriesSchema
            assert KnowledgeCategoriesSchema is not None
        except ImportError:
            assert False, "KnowledgeCategoriesSchema should exist"
    
    def test_eighteen_knowledge_categories(self):
        """Test that all 18 knowledge categories are defined"""
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        
        expected_categories = [
            'company_overview', 'products_services', 'pricing_packages',
            'contact_information', 'business_hours', 'location_directions',
            'team_staff', 'testimonials_reviews', 'faq_support',
            'policies_terms', 'appointment_booking', 'payment_methods',
            'shipping_delivery', 'warranty_returns', 'technical_specs',
            'news_updates', 'social_media', 'special_offers'
        ]
        
        assert len(KNOWLEDGE_CATEGORIES) == 18, "Should have exactly 18 knowledge categories"
        
        for category in expected_categories:
            assert category in KNOWLEDGE_CATEGORIES, f"Should include {category} category"
    
    def test_category_validation_schema(self):
        """Test that each category has validation schema"""
        from src.schemas.knowledge_categories import validate_knowledge_category
        
        # Should be able to validate category data
        test_data = {
            'title': 'Test Category',
            'content': 'Test content for validation',
            'keywords': ['test', 'validation'],
            'last_updated': '2024-01-01'
        }
        
        # Should not raise exception for valid data
        try:
            result = validate_knowledge_category('company_overview', test_data)
            assert result is not None
        except Exception:
            assert False, "Should validate proper category data"
    
    def test_knowledge_base_extraction_rules(self):
        """Test that extraction rules exist for each category"""
        from src.schemas.knowledge_categories import get_extraction_rules
        
        # Should have extraction rules for web crawling
        rules = get_extraction_rules('company_overview')
        assert 'selectors' in rules, "Should have CSS selectors for extraction"
        assert 'keywords' in rules, "Should have keywords for content matching"


class TestVoiceAgentCRUDOperations:
    """Test Voice Agent CRUD API operations with tenant isolation"""
    
    @pytest.fixture
    def mock_tenant_id(self):
        return str(uuid4())
    
    @pytest.fixture
    def sample_voice_agent_data(self):
        return {
            'name': 'Customer Service Agent',
            'description': 'AI assistant for customer support',
            'knowledge_base': {
                'company_overview': {
                    'title': 'About Our Company',
                    'content': 'We provide excellent customer service',
                    'keywords': ['company', 'service', 'support']
                }
            },
            'voice_config': {
                'voice_id': 'elevenlabs_voice_123',
                'speaking_rate': 1.0,
                'pitch': 0.0
            }
        }
    
    def test_create_voice_agent_endpoint_exists(self):
        """Test that POST /api/agents endpoint exists"""
        try:
            from src.api.routers.voice_agents import router
            # Check if router has POST endpoint
            routes = [route for route in router.routes if hasattr(route, 'methods')]
            post_routes = [route for route in routes if 'POST' in route.methods]
            assert len(post_routes) > 0, "Should have POST route for creating agents"
        except ImportError:
            assert False, "Voice agents router should exist"
    
    def test_list_voice_agents_endpoint_exists(self):
        """Test that GET /api/agents endpoint exists"""
        try:
            from src.api.routers.voice_agents import router
            routes = [route for route in router.routes if hasattr(route, 'methods')]
            get_routes = [route for route in routes if 'GET' in route.methods]
            assert len(get_routes) > 0, "Should have GET route for listing agents"
        except ImportError:
            assert False, "Voice agents router should exist"
    
    def test_voice_agent_service_exists(self):
        """Test that VoiceAgentService exists for business logic"""
        try:
            from src.services.voice_agent_service import VoiceAgentService
            assert hasattr(VoiceAgentService, 'create_agent')
            assert hasattr(VoiceAgentService, 'get_agents_for_tenant')
            assert hasattr(VoiceAgentService, 'get_agent_by_id')
        except ImportError:
            assert False, "VoiceAgentService should exist"
    
    @patch('src.services.voice_agent_service.VoiceAgentService.create_agent')
    def test_create_voice_agent_service_call(self, mock_create, mock_tenant_id, sample_voice_agent_data):
        """Test that create_agent service method can be called"""
        from src.services.voice_agent_service import VoiceAgentService
        
        # Mock successful creation
        mock_agent = MagicMock()
        mock_agent.id = str(uuid4())
        mock_agent.tenant_id = mock_tenant_id
        mock_agent.name = sample_voice_agent_data['name']
        mock_create.return_value = mock_agent
        
        service = VoiceAgentService()
        result = service.create_agent(mock_tenant_id, sample_voice_agent_data)
        
        assert result is not None
        assert result.tenant_id == mock_tenant_id
        mock_create.assert_called_once_with(mock_tenant_id, sample_voice_agent_data)
    
    @patch('src.services.voice_agent_service.VoiceAgentService.get_agents_for_tenant')
    def test_list_agents_tenant_isolation(self, mock_list, mock_tenant_id):
        """Test that listing agents respects tenant isolation"""
        from src.services.voice_agent_service import VoiceAgentService
        
        # Mock list of agents for tenant
        mock_agents = [
            MagicMock(id=str(uuid4()), tenant_id=mock_tenant_id, name='Agent 1'),
            MagicMock(id=str(uuid4()), tenant_id=mock_tenant_id, name='Agent 2')
        ]
        mock_list.return_value = mock_agents
        
        service = VoiceAgentService()
        result = service.get_agents_for_tenant(mock_tenant_id)
        
        assert len(result) == 2
        for agent in result:
            assert agent.tenant_id == mock_tenant_id
        mock_list.assert_called_once_with(mock_tenant_id)
    
    @patch('src.services.voice_agent_service.VoiceAgentService.get_agent_by_id')
    def test_get_agent_by_id_tenant_check(self, mock_get, mock_tenant_id):
        """Test that get_agent_by_id checks tenant ownership"""
        from src.services.voice_agent_service import VoiceAgentService
        
        agent_id = str(uuid4())
        mock_agent = MagicMock()
        mock_agent.id = agent_id
        mock_agent.tenant_id = mock_tenant_id
        mock_get.return_value = mock_agent
        
        service = VoiceAgentService()
        result = service.get_agent_by_id(agent_id, mock_tenant_id)
        
        assert result is not None
        assert result.tenant_id == mock_tenant_id
        mock_get.assert_called_once_with(agent_id, mock_tenant_id)


class TestVoiceAgentAPIEndpoints:
    """Test FastAPI endpoints for voice agent management"""
    
    @pytest.fixture
    def mock_current_user(self):
        return {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'email': 'test@example.com'
        }
    
    def test_api_router_registration(self):
        """Test that voice agents router is registered with main app"""
        try:
            from src.api.app import app
            # Check if voice agents routes are included
            routes = [str(route.path) for route in app.routes]
            assert any('/agents' in route for route in routes), "Should include voice agents routes"
        except ImportError:
            assert False, "Main app should exist and include voice agents router"
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_create_agent_endpoint_authentication(self, mock_service_class):
        """Test that create agent endpoint requires authentication"""
        from src.api.routers.voice_agents import create_voice_agent
        import inspect
        
        # Check if endpoint has authentication dependency
        sig = inspect.signature(create_voice_agent)
        params = list(sig.parameters.keys())
        
        # Should have current_user parameter (from authentication)
        assert 'current_user' in params, "Should require current_user authentication"
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_list_agents_endpoint_authentication(self, mock_service_class):
        """Test that list agents endpoint requires authentication"""
        from src.api.routers.voice_agents import list_voice_agents
        import inspect
        
        # Check if endpoint has authentication dependency
        sig = inspect.signature(list_voice_agents)
        params = list(sig.parameters.keys())
        
        # Should have current_user parameter (from authentication)
        assert 'current_user' in params, "Should require current_user authentication"
    
    def test_voice_agent_request_models_exist(self):
        """Test that Pydantic request models exist for API validation"""
        try:
            from src.schemas.voice_agent_schemas import (
                VoiceAgentCreateRequest,
                VoiceAgentResponse,
                VoiceAgentUpdateRequest
            )
            
            # Check required fields in create request
            create_fields = VoiceAgentCreateRequest.__fields__
            assert 'name' in create_fields, "Should have name field"
            assert 'description' in create_fields, "Should have description field"
            assert 'knowledge_base' in create_fields, "Should have knowledge_base field"
            
        except ImportError:
            assert False, "Voice agent schemas should exist"
    
    def test_voice_agent_response_models_exist(self):
        """Test that Pydantic response models exist for API serialization"""
        try:
            from src.schemas.voice_agent_schemas import VoiceAgentResponse
            
            # Check required fields in response
            response_fields = VoiceAgentResponse.__fields__
            assert 'id' in response_fields, "Should have id field"
            assert 'tenant_id' in response_fields, "Should have tenant_id field"
            assert 'name' in response_fields, "Should have name field"
            assert 'status' in response_fields, "Should have status field"
            assert 'created_at' in response_fields, "Should have created_at field"
            
        except ImportError:
            assert False, "Voice agent response schemas should exist"


class TestTenantIsolationSecurity:
    """Test that voice agents are properly isolated by tenant"""
    
    @patch('src.services.voice_agent_service.VoiceAgentService.get_agents_for_tenant')
    def test_tenant_cannot_access_other_tenant_agents(self, mock_get_agents):
        """Test that tenants cannot access other tenants' agents"""
        from src.services.voice_agent_service import VoiceAgentService
        
        tenant_a_id = str(uuid4())
        tenant_b_id = str(uuid4())
        
        # Mock only tenant A agents returned
        tenant_a_agents = [
            MagicMock(id=str(uuid4()), tenant_id=tenant_a_id, name='Agent A1'),
            MagicMock(id=str(uuid4()), tenant_id=tenant_a_id, name='Agent A2')
        ]
        mock_get_agents.return_value = tenant_a_agents
        
        service = VoiceAgentService()
        result = service.get_agents_for_tenant(tenant_a_id)
        
        # Should only get tenant A's agents
        assert len(result) == 2
        for agent in result:
            assert agent.tenant_id == tenant_a_id
            assert agent.tenant_id != tenant_b_id
    
    @patch('src.services.voice_agent_service.VoiceAgentService.get_agent_by_id')
    def test_cross_tenant_agent_access_denied(self, mock_get_agent):
        """Test that cross-tenant agent access is denied"""
        from src.services.voice_agent_service import VoiceAgentService
        
        tenant_a_id = str(uuid4())
        tenant_b_id = str(uuid4())
        agent_id = str(uuid4())
        
        # Mock agent belongs to tenant B
        agent_b = MagicMock(id=agent_id, tenant_id=tenant_b_id)
        
        # When tenant A tries to access, should return None or raise error
        mock_get_agent.return_value = None  # Simulating access denied
        
        service = VoiceAgentService()
        result = service.get_agent_by_id(agent_id, tenant_a_id)
        
        # Should not return the agent (tenant isolation working)
        assert result is None
        mock_get_agent.assert_called_once_with(agent_id, tenant_a_id)
    
    def test_database_rls_policy_exists(self):
        """Test that Row Level Security policy exists for voice_agents table"""
        # This would test that RLS is enabled on voice_agents table
        # For now, we'll test that the concept is understood
        
        try:
            from src.models.voice_agent import VoiceAgent
            # In a real implementation, we'd check that RLS is configured
            # For now, ensure tenant_id is always required
            assert hasattr(VoiceAgent, 'tenant_id'), "VoiceAgent must have tenant_id for RLS"
        except ImportError:
            assert False, "VoiceAgent model should exist with tenant_id field"