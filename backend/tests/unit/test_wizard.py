"""
Test suite for Agent Creation Wizard backend functionality

This module tests the backend APIs and services that support the Agent Creation Wizard
frontend component, including agent creation, progress tracking, and validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
import json

from src.schemas.voice_agent_schemas import VoiceAgentCreateRequest, VoiceAgentResponse
from src.services.pipeline.agent_pipeline import AgentCreationPipeline
from src.websocket.progress_manager import ProgressManager


class TestAgentCreationWizardBackend:
    """Test suite for wizard backend functionality"""
    
    @pytest.fixture
    def mock_voice_agent_service(self):
        """Mock voice agent service for testing"""
        service = Mock()
        service.create_agent.return_value = Mock(
            agent_id="test-agent-123",
            name="Test Agent",
            type="voice"
        )
        service.create_agent_with_knowledge.return_value = {
            "agent_id": "test-agent-123",
            "name": "Test Agent", 
            "type": "voice",
            "status": "active"
        }
        return service
    
    @pytest.fixture 
    def mock_progress_manager(self):
        """Mock progress manager for testing"""
        manager = Mock()
        manager.create_session.return_value = "session-123"
        manager.update_progress = Mock()
        manager.complete_session = Mock()
        manager.fail_session = Mock()
        return manager
    
    @pytest.fixture
    def agent_request_data(self):
        """Valid agent creation request data"""
        return {
            "name": "Voice Assistant Pro",
            "description": "Advanced voice assistant for customer support",
            "knowledge_base": {
                "company_overview": {
                    "title": "About Our Company",
                    "content": "We provide excellent customer service...",
                    "keywords": ["company", "service", "support"]
                }
            },
            "voice_config": {
                "voice_id": "elevenlabs_voice_123",
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0,
                "stability": 0.75,
                "clarity": 0.75,
                "style": 0.0
            }
        }
    
    @pytest.fixture
    def chat_agent_request_data(self):
        """Valid chat agent creation request data"""
        return {
            "name": "Simple Chat Bot",
            "description": "Basic chat assistant",
            "knowledge_base": {},
            "voice_config": {
                "voice_id": None,
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0,
                "stability": 0.75,
                "clarity": 0.75,
                "style": 0.0
            }
        }

    def test_voice_agent_create_request_validation(self, agent_request_data):
        """Test VoiceAgentCreateRequest schema validation"""
        # Valid request should pass
        request = VoiceAgentCreateRequest(**agent_request_data)
        assert request.name == "Voice Assistant Pro"
        assert request.description == "Advanced voice assistant for customer support"
        assert request.voice_config.voice_id == "elevenlabs_voice_123"
        assert request.voice_config.speaking_rate == 1.0
        assert request.voice_config.stability == 0.75
        assert "company_overview" in request.knowledge_base
    
    def test_voice_agent_create_request_missing_required_fields(self):
        """Test validation with missing required fields"""
        # The 'name' field is the only required field, other fields have defaults
        request = VoiceAgentCreateRequest(name="Test")
        assert request.name == "Test"
        assert request.description is None
        assert request.knowledge_base == {}
        assert request.voice_config is not None  # Has default values
    
    def test_voice_agent_create_request_invalid_voice_config(self, agent_request_data):
        """Test validation fails for invalid voice config values"""
        # Speaking rate too high
        agent_request_data["voice_config"]["speaking_rate"] = 2.5
        with pytest.raises(Exception):  # Should raise validation error
            VoiceAgentCreateRequest(**agent_request_data)
        
        # Reset for next test
        agent_request_data["voice_config"]["speaking_rate"] = 1.0
            
        # Volume too low  
        agent_request_data["voice_config"]["volume"] = -0.5
        with pytest.raises(Exception):  # Should raise validation error
            VoiceAgentCreateRequest(**agent_request_data)
    
    def test_chat_agent_configuration_validation(self, chat_agent_request_data):
        """Test chat agent has correct configuration (no specific voice)"""
        request = VoiceAgentCreateRequest(**chat_agent_request_data)
        assert request.name == "Simple Chat Bot"
        assert request.description == "Basic chat assistant"
        assert request.knowledge_base == {}
        # Voice ID should be None for chat agents
        assert request.voice_config.voice_id is None
        assert request.voice_config.speaking_rate == 1.0

    @pytest.mark.asyncio
    async def test_create_voice_agent_endpoint_success(self, mock_voice_agent_service, agent_request_data):
        """Test successful voice agent creation via API endpoint"""
        with patch('src.services.voice_agent_service.VoiceAgentService', return_value=mock_voice_agent_service):
            with patch('src.api.routers.voice_agents.get_current_user', return_value={"tenant_id": "tenant-123"}):
                with patch('src.api.routers.voice_agents.get_progress_manager') as mock_pm:
                    with patch('src.api.routers.voice_agents.get_websocket_manager') as mock_wm:
                        mock_pm.return_value.create_session.return_value = "session-123"
                        
                        from src.api.routers.voice_agents import create_voice_agent_with_progress
                        
                        request = VoiceAgentCreateRequest(**agent_request_data)
                        response = await create_voice_agent_with_progress(request, {"tenant_id": "tenant-123"})
                        
                        # Verify response has session ID
                        assert "session_id" in response
                        assert response["session_id"] == "session-123"
    
    @pytest.mark.asyncio
    async def test_create_voice_agent_with_progress_tracking(self, mock_voice_agent_service, mock_progress_manager, agent_request_data):
        """Test voice agent creation with progress tracking"""
        with patch('src.api.routers.voice_agents.VoiceAgentService', return_value=mock_voice_agent_service):
            with patch('src.api.routers.voice_agents.get_progress_manager', return_value=mock_progress_manager):
                with patch('src.api.routers.voice_agents.get_websocket_manager'):
                    from src.api.routers.voice_agents import create_voice_agent_with_progress
                    
                    request = VoiceAgentCreateRequest(**agent_request_data)
                    response = await create_voice_agent_with_progress(request, {"tenant_id": "tenant-123"})
                    
                    # Verify progress session was created
                    mock_progress_manager.create_session.assert_called_once_with("agent_creation")
                    assert response["session_id"] == "session-123"
    
    @pytest.mark.asyncio 
    async def test_agent_pipeline_create_agent(self, mock_voice_agent_service):
        """Test AgentCreationPipeline initialization and service setup"""
        # Test that the pipeline can be initialized with mocked services
        with patch('src.services.pipeline.agent_pipeline.VoiceAgentService'):
            pipeline = AgentCreationPipeline(safe_mode=True)
            
            # Verify that the pipeline has the service status tracking
            assert hasattr(pipeline, 'service_status')
            assert 'voice_agent_service' in pipeline.service_status
            
            # Verify that safe_mode is set correctly
            assert pipeline.safe_mode == True

    def test_progress_manager_session_lifecycle(self):
        """Test ProgressManager session creation and lifecycle"""
        manager = ProgressManager()
        
        # Create session
        session_id = manager.create_session("agent_creation")
        assert session_id is not None
        
        # Update progress
        manager.update_progress(session_id, "validating", 25)
        session = manager.get_session_status(session_id)
        assert session is not None
        assert session["status"] == "started"
        
        # Complete session
        manager.complete_session(session_id, True, "Agent created successfully")
        session = manager.get_session_status(session_id)
        assert session["status"] == "completed"
        assert session["success"] == True
        assert session["result"] == "Agent created successfully"

    def test_progress_manager_error_handling(self):
        """Test ProgressManager error handling"""
        manager = ProgressManager()
        
        session_id = manager.create_session("agent_creation")
        
        # Fail session (using complete_session with success=False)
        error_msg = "Model validation failed"
        manager.complete_session(session_id, False, error_msg)
        
        session = manager.get_session_status(session_id)
        assert session["status"] == "completed"
        assert session["success"] == False
        assert session["result"] == error_msg

    @pytest.mark.asyncio
    async def test_agent_creation_error_handling(self, mock_progress_manager):
        """Test error handling during agent creation"""
        mock_service = Mock()
        mock_service.create_agent.side_effect = Exception("Service unavailable")
        
        with patch('src.api.routers.voice_agents.VoiceAgentService', return_value=mock_service):
            with patch('src.api.routers.voice_agents.get_progress_manager', return_value=mock_progress_manager):
                with patch('src.api.routers.voice_agents.get_websocket_manager'):
                    from src.api.routers.voice_agents import create_voice_agent_with_progress
                    
                    request_data = {
                        "name": "Error Test Agent",
                        "description": "Test error handling"
                    }
                    
                    request = VoiceAgentCreateRequest(**request_data)
                    response = await create_voice_agent_with_progress(request, {"tenant_id": "tenant-123"})
                    
                    # Should still return session_id for tracking
                    assert "session_id" in response
                    # Progress manager should be called
                    mock_progress_manager.create_session.assert_called_once()

    def test_wizard_data_transformation(self, agent_request_data):
        """Test data transformation from wizard format to backend format"""
        request = VoiceAgentCreateRequest(**agent_request_data)
        
        # Verify wizard data is correctly structured for backend
        assert request.name == agent_request_data["name"]
        assert request.description == agent_request_data["description"] 
        assert request.knowledge_base == agent_request_data["knowledge_base"]
        
        voice_config = request.voice_config
        expected_voice_config = agent_request_data["voice_config"]
        assert voice_config.voice_id == expected_voice_config["voice_id"]
        assert voice_config.speaking_rate == expected_voice_config["speaking_rate"]
        assert voice_config.pitch == expected_voice_config["pitch"]
        assert voice_config.stability == expected_voice_config["stability"]
        assert voice_config.clarity == expected_voice_config["clarity"]

    @pytest.mark.asyncio
    async def test_knowledge_base_agent_creation(self):
        """Test creation of agents with comprehensive knowledge base"""
        knowledge_data = {
            "name": "Knowledge Agent",
            "description": "Agent with comprehensive knowledge base",
            "knowledge_base": {
                "company_overview": {
                    "title": "About Our Company",
                    "content": "We provide excellent customer service...",
                    "keywords": ["company", "service", "support"]
                },
                "products_services": {
                    "title": "Our Services",
                    "content": "We offer comprehensive solutions...",
                    "keywords": ["services", "solutions", "comprehensive"]
                }
            }
        }
        
        # This should be handled by the agent creation pipeline
        request = VoiceAgentCreateRequest(**knowledge_data)
        assert request.name == "Knowledge Agent"
        assert "company_overview" in request.knowledge_base
        assert "products_services" in request.knowledge_base

    def test_agent_configuration_defaults(self):
        """Test that agent configuration includes proper defaults"""
        minimal_data = {
            "name": "Minimal Agent",
            "description": "Test agent with minimal config"
        }
        
        request = VoiceAgentCreateRequest(**minimal_data)
        
        # Should have default voice config values
        assert request.voice_config.speaking_rate == 1.0
        assert request.voice_config.pitch == 0.0
        assert request.voice_config.volume == 1.0
        assert request.voice_config.stability == 0.75
        assert request.voice_config.clarity == 0.75
        # Should have empty knowledge base by default
        assert request.knowledge_base == {}

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, mock_voice_agent_service, mock_progress_manager):
        """Test handling of concurrent agent creation requests"""
        # Simulate multiple concurrent requests
        mock_voice_agent_service.create_agent.return_value = {
            "agent_id": "concurrent-test",
            "name": "Test Agent",
            "status": "active"
        }
        
        # Mock unique session IDs for each request
        session_ids = ["session-1", "session-2", "session-3"]
        mock_progress_manager.create_session.side_effect = session_ids
        
        with patch('src.api.routers.voice_agents.VoiceAgentService', return_value=mock_voice_agent_service):
            with patch('src.api.routers.voice_agents.get_progress_manager', return_value=mock_progress_manager):
                with patch('src.api.routers.voice_agents.get_websocket_manager'):
                    from src.api.routers.voice_agents import create_voice_agent_with_progress
                    
                    requests = [
                        {
                            "name": f"Concurrent Agent {i}",
                            "description": f"Test concurrent agent {i}"
                        } for i in range(3)
                    ]
                    
                    # Submit concurrent requests
                    tasks = []
                    for req_data in requests:
                        request = VoiceAgentCreateRequest(**req_data)
                        task = create_voice_agent_with_progress(request, {"tenant_id": "tenant-123"})
                        tasks.append(task)
                    
                    responses = await asyncio.gather(*tasks)
                    
                    # All should succeed and have unique session IDs
                    assert len(responses) == 3
                    response_session_ids = [resp["session_id"] for resp in responses]
                    assert len(set(response_session_ids)) == 3  # All unique

    def test_agent_name_validation(self):
        """Test agent name validation rules"""
        # Valid names should pass
        valid_names = [
            "Simple Agent",
            "Customer Support Bot",
            "Agent-2024",
            "My_Agent_123"
        ]
        
        for name in valid_names:
            data = {
                "name": name,
                "description": "Test description",
                "type": "chat", 
                "configuration": {"language": "en", "model": "gpt-3.5-turbo"}
            }
            request = VoiceAgentCreateRequest(**data)
            assert request.name == name
    
    def test_voice_id_validation(self):
        """Test voice ID validation in voice config"""
        test_voice_ids = [
            "elevenlabs_voice_123",
            "custom_voice_456",
            None  # Should be allowed
        ]
        
        for voice_id in test_voice_ids:
            data = {
                "name": "Voice Test Agent",
                "description": "Test voice agent",
                "voice_config": {
                    "voice_id": voice_id
                }
            }
            request = VoiceAgentCreateRequest(**data)
            assert request.voice_config.voice_id == voice_id

    def test_knowledge_base_validation(self):
        """Test that knowledge base categories are validated"""
        valid_data = {
            "name": "Knowledge Test Agent",
            "description": "Test agent with knowledge",
            "knowledge_base": {
                "company_overview": {
                    "title": "Test Company",
                    "content": "Test content",
                    "keywords": ["test"]
                }
            }
        }
        request = VoiceAgentCreateRequest(**valid_data)
        assert "company_overview" in request.knowledge_base
        
        # Test invalid category should raise error
        invalid_data = {
            "name": "Invalid Knowledge Agent",
            "knowledge_base": {
                "invalid_category": {"title": "Invalid", "content": "Invalid"}
            }
        }
        with pytest.raises(Exception):
            VoiceAgentCreateRequest(**invalid_data)

    @pytest.mark.asyncio
    async def test_wizard_backend_integration_complete_flow(self, mock_voice_agent_service, mock_progress_manager):
        """Test complete wizard backend integration flow"""
        # Mock successful agent creation
        mock_voice_agent_service.create_agent.return_value = {
            "agent_id": "integration-test-123",
            "name": "Integration Test Agent",
            "status": "active",
            "voice_config": {
                "voice_id": "elevenlabs_voice_123",
                "speaking_rate": 1.0
            }
        }
        
        with patch('src.api.routers.voice_agents.VoiceAgentService', return_value=mock_voice_agent_service):
            with patch('src.api.routers.voice_agents.get_progress_manager', return_value=mock_progress_manager):
                with patch('src.api.routers.voice_agents.get_websocket_manager'):
                    from src.api.routers.voice_agents import create_voice_agent_with_progress
                    
                    # Simulate wizard form submission
                    wizard_data = {
                        "name": "Integration Test Agent",
                        "description": "Complete integration test",
                        "voice_config": {
                            "voice_id": "elevenlabs_voice_123",
                            "speaking_rate": 1.0,
                            "stability": 0.8
                        }
                    }
                    
                    request = VoiceAgentCreateRequest(**wizard_data)
                    response = await create_voice_agent_with_progress(request, {"tenant_id": "tenant-123"})
                    
                    # Verify complete integration
                    assert "session_id" in response
                    mock_progress_manager.create_session.assert_called_once()