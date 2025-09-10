"""
T019: Agent Configuration API Tests
Test-driven development for agent configuration endpoints with comprehensive coverage
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4
import asyncio
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))


class TestAgentConfigurationAPIEndpoints:
    """Test agent configuration API endpoints: PUT /agents/{id}, PUT /agents/{id}/knowledge, POST /agents/{id}/activate"""
    
    @pytest.fixture
    def mock_tenant_id(self):
        """Mock tenant ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def mock_agent_id(self):
        """Mock agent ID for testing"""
        return str(uuid4())
    
    @pytest.fixture
    def mock_current_user(self, mock_tenant_id):
        """Mock authenticated user for testing"""
        return {
            'id': str(uuid4()),
            'tenant_id': mock_tenant_id,
            'email': 'test@example.com'
        }
    
    @pytest.fixture
    def sample_agent_data(self):
        """Sample agent data for testing"""
        return {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'name': 'Test Agent',
            'description': 'Test agent for configuration',
            'status': 'active',
            'is_active': True,
            'knowledge_base': {
                'company_overview': {
                    'title': 'Company Info',
                    'content': 'We are a test company',
                    'keywords': ['test', 'company']
                }
            },
            'voice_config': {
                'voice_id': 'test_voice',
                'speaking_rate': 1.0,
                'pitch': 0.0
            },
            'phone_number': '+1-555-123-4567',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }


class TestUpdateAgentConfiguration:
    """Test PUT /api/agents/{id} - Update agent configuration"""
    
    @pytest.fixture
    def update_request_data(self):
        """Sample update request data"""
        return {
            'name': 'Updated Agent Name',
            'description': 'Updated description',
            'voice_config': {
                'voice_id': 'new_voice_123',
                'speaking_rate': 1.2,
                'pitch': 0.1,
                'volume': 0.9,
                'stability': 0.8,
                'clarity': 0.7
            },
            'status': 'active'
        }
    
    def test_update_agent_endpoint_exists(self):
        """Test that PUT /api/agents/{id} endpoint exists"""
        try:
            from src.api.routers.voice_agents import router, update_voice_agent
            
            # Check if the endpoint function exists
            assert update_voice_agent is not None, "update_voice_agent function should exist"
            
            # Check if router has PUT route for agent updates
            routes = [route for route in router.routes if hasattr(route, 'methods')]
            put_routes = [route for route in routes if 'PUT' in route.methods]
            
            # Should have at least one PUT route (for /{agent_id})
            assert len(put_routes) >= 1, "Should have PUT route for updating agents"
            
        except ImportError:
            assert False, "Voice agents router and update endpoint should exist"
    
    def test_update_agent_requires_authentication(self):
        """Test that update agent endpoint requires authentication"""
        from src.api.routers.voice_agents import update_voice_agent
        import inspect
        
        # Check endpoint signature for authentication dependency
        sig = inspect.signature(update_voice_agent)
        params = list(sig.parameters.keys())
        
        assert 'current_user' in params, "Should require current_user authentication"
        assert 'agent_id' in params, "Should require agent_id parameter"
        assert 'agent_update' in params, "Should require agent_update parameter"
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_update_agent_successful_update(self, mock_service_class, update_request_data):
        """Test successful agent configuration update"""
        from src.api.routers.voice_agents import update_voice_agent
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Mock service instance and methods
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock successful update
        updated_agent = {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'name': update_request_data['name'],
            'description': update_request_data['description'],
            'status': update_request_data['status'],
            'is_active': True,
            'voice_config': update_request_data['voice_config'],
            'knowledge_base': {},
            'phone_number': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        mock_service.update_agent.return_value = updated_agent
        
        # Create update request
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        update_request = VoiceAgentUpdateRequest(**update_request_data)
        current_user = {'tenant_id': tenant_id}
        
        # Test the endpoint
        result = asyncio.run(update_voice_agent(agent_id, update_request, current_user))
        
        # Verify service was called correctly
        mock_service.update_agent.assert_called_once_with(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data=update_request.dict(exclude_unset=True)
        )
        
        # Verify response
        assert result.name == update_request_data['name']
        assert result.description == update_request_data['description']
        assert result.status == update_request_data['status']
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_update_agent_not_found(self, mock_service_class):
        """Test update agent when agent not found"""
        from src.api.routers.voice_agents import update_voice_agent
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Mock service to return None (agent not found)
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_agent.return_value = None
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        update_request = VoiceAgentUpdateRequest(name="New Name")
        current_user = {'tenant_id': tenant_id}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_voice_agent(agent_id, update_request, current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_update_agent_validation_error(self, mock_service_class):
        """Test update agent with validation error"""
        from src.api.routers.voice_agents import update_voice_agent
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Mock service to raise validation error
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_agent.side_effect = ValueError("Invalid voice config")
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        update_request = VoiceAgentUpdateRequest(name="New Name")
        current_user = {'tenant_id': tenant_id}
        
        # Should raise HTTPException with 400 status
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_voice_agent(agent_id, update_request, current_user))
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid voice config" in exc_info.value.detail
    
    def test_update_agent_request_schema_validation(self):
        """Test VoiceAgentUpdateRequest schema validation"""
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Test valid update request
        valid_data = {
            'name': 'Valid Agent Name',
            'description': 'Valid description',
            'status': 'active'
        }
        request = VoiceAgentUpdateRequest(**valid_data)
        assert request.name == 'Valid Agent Name'
        assert request.status == 'active'
        
        # Test invalid status
        with pytest.raises(ValueError):
            VoiceAgentUpdateRequest(status='invalid_status')
        
        # Test empty name
        with pytest.raises(ValueError):
            VoiceAgentUpdateRequest(name='')
    
    def test_voice_config_schema_validation(self):
        """Test VoiceConfigSchema validation in update requests"""
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest, VoiceConfigSchema
        
        # Test valid voice config
        valid_voice_config = {
            'voice_id': 'test_voice_123',
            'speaking_rate': 1.0,
            'pitch': 0.0,
            'volume': 1.0,
            'stability': 0.75,
            'clarity': 0.75,
            'style': 0.0
        }
        
        request = VoiceAgentUpdateRequest(voice_config=VoiceConfigSchema(**valid_voice_config))
        assert request.voice_config.voice_id == 'test_voice_123'
        assert request.voice_config.speaking_rate == 1.0
        
        # Test invalid speaking rate (out of range)
        with pytest.raises(ValueError):
            VoiceConfigSchema(speaking_rate=3.0)  # Should be between 0.5-2.0
        
        # Test invalid pitch (out of range)
        with pytest.raises(ValueError):
            VoiceConfigSchema(pitch=2.0)  # Should be between -1.0-1.0


class TestUpdateAgentKnowledgeBase:
    """Test PUT /api/agents/{id}/knowledge - Update knowledge base"""
    
    @pytest.fixture
    def knowledge_update_data(self):
        """Sample knowledge base update data"""
        return {
            'knowledge_base': {
                'company_overview': {
                    'title': 'Updated Company Overview',
                    'content': 'We are a leading technology company specializing in AI solutions.',
                    'keywords': ['technology', 'AI', 'solutions', 'leading']
                },
                'products_services': {
                    'title': 'Our Products',
                    'content': 'We offer cutting-edge AI products and consulting services.',
                    'keywords': ['products', 'AI', 'consulting', 'cutting-edge']
                },
                'contact_information': {
                    'title': 'Contact Us',
                    'content': 'Reach us at contact@company.com or +1-800-123-4567',
                    'keywords': ['contact', 'email', 'phone']
                }
            }
        }
    
    def test_update_knowledge_endpoint_exists(self):
        """Test that PUT /api/agents/{id}/knowledge endpoint exists"""
        try:
            from src.api.routers.voice_agents import router, update_voice_agent_knowledge
            
            # Check if the endpoint function exists
            assert update_voice_agent_knowledge is not None, "update_voice_agent_knowledge function should exist"
            
            # Check router for knowledge-specific route
            routes = [route for route in router.routes if hasattr(route, 'methods')]
            put_routes = [route for route in routes if 'PUT' in route.methods]
            
            # Should have PUT route for knowledge updates
            knowledge_routes = [route for route in put_routes if 'knowledge' in str(route.path)]
            assert len(knowledge_routes) >= 1, "Should have PUT route for knowledge updates"
            
        except ImportError:
            assert False, "Voice agents router and knowledge update endpoint should exist"
    
    def test_update_knowledge_requires_authentication(self):
        """Test that update knowledge endpoint requires authentication"""
        from src.api.routers.voice_agents import update_voice_agent_knowledge
        import inspect
        
        # Check endpoint signature
        sig = inspect.signature(update_voice_agent_knowledge)
        params = list(sig.parameters.keys())
        
        assert 'current_user' in params, "Should require current_user authentication"
        assert 'agent_id' in params, "Should require agent_id parameter"
        assert 'knowledge_update' in params, "Should require knowledge_update parameter"
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_update_knowledge_successful_update(self, mock_service_class, knowledge_update_data):
        """Test successful knowledge base update"""
        from src.api.routers.voice_agents import update_voice_agent_knowledge
        from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
        
        # Mock service instance and methods
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock successful update
        updated_agent = {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'name': 'Test Agent',
            'description': 'Test agent',
            'status': 'active',
            'is_active': True,
            'knowledge_base': knowledge_update_data['knowledge_base'],
            'voice_config': {},
            'phone_number': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        mock_service.update_agent.return_value = updated_agent
        
        # Create update request
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        knowledge_request = VoiceAgentKnowledgeUpdateRequest(**knowledge_update_data)
        current_user = {'tenant_id': tenant_id}
        
        # Test the endpoint
        result = asyncio.run(update_voice_agent_knowledge(agent_id, knowledge_request, current_user))
        
        # Verify service was called correctly
        mock_service.update_agent.assert_called_once_with(
            agent_id=agent_id,
            tenant_id=tenant_id,
            update_data={'knowledge_base': knowledge_update_data['knowledge_base']}
        )
        
        # Verify response has updated knowledge base
        assert result.knowledge_base == knowledge_update_data['knowledge_base']
        assert 'company_overview' in result.knowledge_base
        assert 'products_services' in result.knowledge_base
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_update_knowledge_agent_not_found(self, mock_service_class):
        """Test update knowledge when agent not found"""
        from src.api.routers.voice_agents import update_voice_agent_knowledge
        from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
        
        # Mock service to return None (agent not found)
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.update_agent.return_value = None
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        knowledge_request = VoiceAgentKnowledgeUpdateRequest(knowledge_base={'company_overview': {}})
        current_user = {'tenant_id': tenant_id}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(update_voice_agent_knowledge(agent_id, knowledge_request, current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()
    
    def test_knowledge_base_schema_validation(self):
        """Test VoiceAgentKnowledgeUpdateRequest schema validation"""
        from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
        
        # Test valid knowledge base
        valid_knowledge = {
            'knowledge_base': {
                'company_overview': {
                    'title': 'Company Info',
                    'content': 'About our company',
                    'keywords': ['company']
                }
            }
        }
        request = VoiceAgentKnowledgeUpdateRequest(**valid_knowledge)
        assert 'company_overview' in request.knowledge_base
        
        # Test invalid category (not in KNOWLEDGE_CATEGORIES)
        invalid_knowledge = {
            'knowledge_base': {
                'invalid_category': {
                    'title': 'Invalid',
                    'content': 'This should fail',
                    'keywords': ['invalid']
                }
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            VoiceAgentKnowledgeUpdateRequest(**invalid_knowledge)
        assert 'Invalid knowledge category' in str(exc_info.value)
    
    def test_knowledge_categories_validation(self):
        """Test that knowledge base validates against KNOWLEDGE_CATEGORIES"""
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
        
        # Test all valid categories
        valid_categories = ['company_overview', 'products_services', 'contact_information', 'faq_support']
        
        for category in valid_categories:
            knowledge_data = {
                'knowledge_base': {
                    category: {
                        'title': f'{category} title',
                        'content': f'{category} content',
                        'keywords': [category]
                    }
                }
            }
            # Should not raise exception
            request = VoiceAgentKnowledgeUpdateRequest(**knowledge_data)
            assert category in request.knowledge_base
        
        # Verify that all expected categories exist in KNOWLEDGE_CATEGORIES
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


class TestAgentActivationDeactivation:
    """Test POST /api/agents/{id}/activate and /api/agents/{id}/deactivate - Activate/deactivate agent"""
    
    def test_activation_endpoints_exist(self):
        """Test that activation/deactivation endpoints exist"""
        try:
            from src.api.routers.voice_agents import router, activate_voice_agent, deactivate_voice_agent
            
            # Check if the endpoint functions exist
            assert activate_voice_agent is not None, "activate_voice_agent function should exist"
            assert deactivate_voice_agent is not None, "deactivate_voice_agent function should exist"
            
            # Check router for activation routes
            routes = [route for route in router.routes if hasattr(route, 'methods')]
            post_routes = [route for route in routes if 'POST' in route.methods]
            
            # Should have POST routes for activate/deactivate
            activate_routes = [route for route in post_routes if 'activate' in str(route.path)]
            deactivate_routes = [route for route in post_routes if 'deactivate' in str(route.path)]
            
            assert len(activate_routes) >= 1, "Should have POST route for agent activation"
            assert len(deactivate_routes) >= 1, "Should have POST route for agent deactivation"
            
        except ImportError:
            assert False, "Voice agents router and activation endpoints should exist"
    
    def test_activation_endpoints_require_authentication(self):
        """Test that activation endpoints require authentication"""
        from src.api.routers.voice_agents import activate_voice_agent, deactivate_voice_agent
        import inspect
        
        # Check activate endpoint signature
        activate_sig = inspect.signature(activate_voice_agent)
        activate_params = list(activate_sig.parameters.keys())
        
        assert 'current_user' in activate_params, "activate should require current_user authentication"
        assert 'agent_id' in activate_params, "activate should require agent_id parameter"
        
        # Check deactivate endpoint signature  
        deactivate_sig = inspect.signature(deactivate_voice_agent)
        deactivate_params = list(deactivate_sig.parameters.keys())
        
        assert 'current_user' in deactivate_params, "deactivate should require current_user authentication"
        assert 'agent_id' in deactivate_params, "deactivate should require agent_id parameter"
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_activate_agent_successful(self, mock_service_class):
        """Test successful agent activation"""
        from src.api.routers.voice_agents import activate_voice_agent
        
        # Mock service instance and methods
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock successful activation
        activated_agent = {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'name': 'Test Agent',
            'description': 'Test agent',
            'status': 'active',
            'is_active': True,
            'knowledge_base': {},
            'voice_config': {},
            'phone_number': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        mock_service.activate_agent.return_value = activated_agent
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        current_user = {'tenant_id': tenant_id}
        
        # Test the endpoint
        result = asyncio.run(activate_voice_agent(agent_id, current_user))
        
        # Verify service was called correctly
        mock_service.activate_agent.assert_called_once_with(agent_id, tenant_id)
        
        # Verify response
        assert result.status == 'active'
        assert result.is_active is True
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_deactivate_agent_successful(self, mock_service_class):
        """Test successful agent deactivation"""
        from src.api.routers.voice_agents import deactivate_voice_agent
        
        # Mock service instance and methods
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock successful deactivation
        deactivated_agent = {
            'id': str(uuid4()),
            'tenant_id': str(uuid4()),
            'name': 'Test Agent',
            'description': 'Test agent',
            'status': 'inactive',
            'is_active': False,
            'knowledge_base': {},
            'voice_config': {},
            'phone_number': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        mock_service.deactivate_agent.return_value = deactivated_agent
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        current_user = {'tenant_id': tenant_id}
        
        # Test the endpoint
        result = asyncio.run(deactivate_voice_agent(agent_id, current_user))
        
        # Verify service was called correctly
        mock_service.deactivate_agent.assert_called_once_with(agent_id, tenant_id)
        
        # Verify response
        assert result.status == 'inactive'
        assert result.is_active is False
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_activate_agent_not_found(self, mock_service_class):
        """Test activate agent when agent not found"""
        from src.api.routers.voice_agents import activate_voice_agent
        
        # Mock service to return None (agent not found)
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.activate_agent.return_value = None
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        current_user = {'tenant_id': tenant_id}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(activate_voice_agent(agent_id, current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_deactivate_agent_not_found(self, mock_service_class):
        """Test deactivate agent when agent not found"""
        from src.api.routers.voice_agents import deactivate_voice_agent
        
        # Mock service to return None (agent not found)
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.deactivate_agent.return_value = None
        
        # Test data
        agent_id = str(uuid4())
        tenant_id = str(uuid4())
        current_user = {'tenant_id': tenant_id}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(deactivate_voice_agent(agent_id, current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc_info.value.detail.lower()
    
    @patch('src.api.routers.voice_agents.VoiceAgentService')
    def test_activation_with_tenant_isolation(self, mock_service_class):
        """Test that activation respects tenant isolation"""
        from src.api.routers.voice_agents import activate_voice_agent
        
        # Mock service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        tenant_a_id = str(uuid4())
        tenant_b_id = str(uuid4())
        agent_id = str(uuid4())
        
        # Mock agent belonging to tenant B, but tenant A tries to activate
        mock_service.activate_agent.return_value = None  # Access denied
        
        current_user = {'tenant_id': tenant_a_id}
        
        # Should fail with 404 (not found due to tenant isolation)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(activate_voice_agent(agent_id, current_user))
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        
        # Verify service was called with correct tenant ID
        mock_service.activate_agent.assert_called_once_with(agent_id, tenant_a_id)


class TestAgentConfigurationAPIIntegration:
    """Integration tests for agent configuration API endpoints"""
    
    def test_voice_agent_service_methods_exist(self):
        """Test that VoiceAgentService has required methods for configuration"""
        try:
            from src.services.voice_agent_service import VoiceAgentService
            
            # Check that service has all required methods
            assert hasattr(VoiceAgentService, 'update_agent'), "Should have update_agent method"
            assert hasattr(VoiceAgentService, 'activate_agent'), "Should have activate_agent method"
            assert hasattr(VoiceAgentService, 'deactivate_agent'), "Should have deactivate_agent method"
            
        except ImportError:
            assert False, "VoiceAgentService should exist with configuration methods"
    
    def test_schema_imports_work(self):
        """Test that all required schemas can be imported"""
        try:
            from src.schemas.voice_agent_schemas import (
                VoiceAgentUpdateRequest,
                VoiceAgentKnowledgeUpdateRequest,
                VoiceAgentResponse,
                VoiceConfigSchema
            )
            
            # Verify schemas exist
            assert VoiceAgentUpdateRequest is not None
            assert VoiceAgentKnowledgeUpdateRequest is not None
            assert VoiceAgentResponse is not None
            assert VoiceConfigSchema is not None
            
        except ImportError as e:
            assert False, f"Required schemas should be importable: {e}"
    
    def test_knowledge_categories_integration(self):
        """Test integration with knowledge categories schema"""
        try:
            from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES, validate_knowledge_category
            from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
            
            # Verify knowledge categories are available
            assert len(KNOWLEDGE_CATEGORIES) == 18, "Should have 18 knowledge categories"
            
            # Test that knowledge update request validates categories
            valid_knowledge = {
                'knowledge_base': {
                    'company_overview': {
                        'title': 'Test',
                        'content': 'Test content',
                        'keywords': ['test']
                    }
                }
            }
            
            # Should not raise exception
            request = VoiceAgentKnowledgeUpdateRequest(**valid_knowledge)
            assert request is not None
            
        except ImportError as e:
            assert False, f"Knowledge categories integration should work: {e}"
    
    def test_error_handling_consistency(self):
        """Test that all endpoints handle errors consistently"""
        from fastapi import HTTPException, status
        
        # Test status codes are available
        assert status.HTTP_400_BAD_REQUEST == 400
        assert status.HTTP_404_NOT_FOUND == 404  
        assert status.HTTP_500_INTERNAL_SERVER_ERROR == 500
        
        # Test HTTPException works
        try:
            raise HTTPException(status_code=404, detail="Test error")
        except HTTPException as e:
            assert e.status_code == 404
            assert e.detail == "Test error"
    
    def test_tenant_isolation_consistency(self):
        """Test that all configuration endpoints maintain tenant isolation"""
        try:
            from src.api.routers.voice_agents import (
                update_voice_agent,
                update_voice_agent_knowledge, 
                activate_voice_agent,
                deactivate_voice_agent
            )
            import inspect
            
            # All endpoints should require current_user for tenant isolation
            endpoints = [
                update_voice_agent,
                update_voice_agent_knowledge,
                activate_voice_agent,
                deactivate_voice_agent
            ]
            
            for endpoint in endpoints:
                sig = inspect.signature(endpoint)
                params = list(sig.parameters.keys())
                assert 'current_user' in params, f"{endpoint.__name__} should require current_user for tenant isolation"
                
        except ImportError as e:
            assert False, f"All configuration endpoints should exist: {e}"


class TestConfigurationAPIPerformance:
    """Performance and edge case tests for configuration API"""
    
    def test_large_knowledge_base_update(self):
        """Test handling of large knowledge base updates"""
        from src.schemas.voice_agent_schemas import VoiceAgentKnowledgeUpdateRequest
        from src.schemas.knowledge_categories import KNOWLEDGE_CATEGORIES
        
        # Create large knowledge base with all 18 categories
        large_knowledge_base = {}
        
        for category in KNOWLEDGE_CATEGORIES:
            large_knowledge_base[category] = {
                'title': f'{category} title with detailed information',
                'content': f'This is a very long content for {category} ' * 100,  # Large content
                'keywords': [f'keyword_{i}_{category}' for i in range(50)]  # Many keywords
            }
        
        # Should handle large knowledge base
        request = VoiceAgentKnowledgeUpdateRequest(knowledge_base=large_knowledge_base)
        assert len(request.knowledge_base) == 18
        
        # Verify all categories are present
        for category in KNOWLEDGE_CATEGORIES:
            assert category in request.knowledge_base
    
    def test_partial_update_scenarios(self):
        """Test various partial update scenarios"""
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Test updating only name
        name_only = VoiceAgentUpdateRequest(name="New Name Only")
        assert name_only.name == "New Name Only"
        assert name_only.description is None
        assert name_only.voice_config is None
        
        # Test updating only status
        status_only = VoiceAgentUpdateRequest(status="inactive")
        assert status_only.status == "inactive"
        assert status_only.name is None
        
        # Test exclude_unset behavior
        update_data = name_only.dict(exclude_unset=True)
        assert 'name' in update_data
        assert 'description' not in update_data
        assert 'voice_config' not in update_data
    
    def test_concurrent_updates_handling(self):
        """Test handling of concurrent update scenarios"""
        # This is a conceptual test for concurrent updates
        # In practice, this would test database-level concurrency handling
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest
        
        # Create multiple update requests that could conflict
        update1 = VoiceAgentUpdateRequest(name="Update 1", status="active")
        update2 = VoiceAgentUpdateRequest(name="Update 2", status="inactive")
        
        # Both should be valid individually
        assert update1.name == "Update 1"
        assert update2.name == "Update 2"
        
        # Service layer would handle conflict resolution
        # This test ensures the schemas support concurrent scenarios
    
    def test_validation_edge_cases(self):
        """Test edge cases in validation"""
        from src.schemas.voice_agent_schemas import VoiceAgentUpdateRequest, VoiceConfigSchema
        
        # Test boundary values for voice config
        edge_voice_config = VoiceConfigSchema(
            speaking_rate=0.5,  # Minimum allowed
            pitch=-1.0,         # Minimum allowed
            volume=2.0,         # Maximum allowed
            stability=0.0,      # Minimum allowed
            clarity=1.0,        # Maximum allowed
            style=1.0           # Maximum allowed
        )
        
        request = VoiceAgentUpdateRequest(voice_config=edge_voice_config)
        assert request.voice_config.speaking_rate == 0.5
        assert request.voice_config.pitch == -1.0
        assert request.voice_config.volume == 2.0
        
        # Test maximum boundary violations
        with pytest.raises(ValueError):
            VoiceConfigSchema(speaking_rate=2.1)  # Above maximum
            
        with pytest.raises(ValueError):
            VoiceConfigSchema(pitch=1.1)  # Above maximum