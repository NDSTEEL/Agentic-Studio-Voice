"""Tests for phone service integration with Twilio API."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from twilio.base.exceptions import TwilioException
import uuid
from datetime import datetime

from src.services.twilio.twilio_phone_client import TwilioPhoneClient
from src.services.phone.phone_service import PhoneService
from src.services.phone.call_router import CallRouter, CallAction
from src.models.voice_agent import VoiceAgent
from src.models.tenant import Tenant


class TestTwilioPhoneClient:
    """Test cases for TwilioPhoneClient."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock Twilio client."""
        with patch('src.services.twilio.twilio_phone_client.Client') as mock_client:
            yield mock_client
            
    @pytest.fixture
    def phone_client(self, mock_twilio_client):
        """Create TwilioPhoneClient instance with mocked dependencies."""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'WEBHOOK_BASE_URL': 'https://example.com'
        }):
            return TwilioPhoneClient()
            
    def test_initialization_with_env_vars(self, mock_twilio_client):
        """Test client initialization with environment variables."""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token'
        }):
            client = TwilioPhoneClient()
            assert client.account_sid == 'test_sid'
            assert client.auth_token == 'test_token'
            
    def test_initialization_with_params(self, mock_twilio_client):
        """Test client initialization with direct parameters."""
        client = TwilioPhoneClient(
            account_sid='param_sid',
            auth_token='param_token',
            webhook_base_url='https://param.example.com'
        )
        assert client.account_sid == 'param_sid'
        assert client.auth_token == 'param_token'
        assert client.webhook_base_url == 'https://param.example.com'
        
    def test_initialization_missing_credentials(self, mock_twilio_client):
        """Test client initialization fails without credentials."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Twilio Account SID and Auth Token are required"):
                TwilioPhoneClient()
                
    @pytest.mark.asyncio
    async def test_search_phone_numbers_success(self, phone_client, mock_twilio_client):
        """Test successful phone number search."""
        # Mock available phone numbers
        mock_number = Mock()
        mock_number.phone_number = '+14155551234'
        mock_number.friendly_name = 'San Francisco Number'
        mock_number.locality = 'San Francisco'
        mock_number.region = 'CA'
        mock_number.postal_code = '94105'
        mock_number.capabilities = {'voice': True, 'sms': True, 'mms': False}
        
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.available_phone_numbers.return_value.local.list.return_value = [mock_number]
        phone_client.client = mock_client_instance
        
        results = await phone_client.search_phone_numbers(
            area_code='415',
            contains='555',
            limit=10
        )
        
        assert len(results) == 1
        assert results[0]['phone_number'] == '+14155551234'
        assert results[0]['capabilities']['voice'] is True
        assert results[0]['capabilities']['sms'] is True
        
    @pytest.mark.asyncio
    async def test_search_phone_numbers_twilio_error(self, phone_client, mock_twilio_client):
        """Test phone number search with Twilio error."""
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.available_phone_numbers.return_value.local.list.side_effect = TwilioException("API Error")
        phone_client.client = mock_client_instance
        
        with pytest.raises(TwilioException):
            await phone_client.search_phone_numbers(area_code='415')
            
    @pytest.mark.asyncio
    async def test_provision_phone_number_success(self, phone_client, mock_twilio_client):
        """Test successful phone number provisioning."""
        mock_number = Mock()
        mock_number.sid = 'PN123456789'
        mock_number.phone_number = '+14155551234'
        mock_number.friendly_name = 'Test Number'
        mock_number.voice_url = 'https://example.com/webhook/voice'
        mock_number.sms_url = 'https://example.com/webhook/sms'
        mock_number.capabilities = {'voice': True, 'sms': True}
        mock_number.status = 'active'
        
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.incoming_phone_numbers.create.return_value = mock_number
        phone_client.client = mock_client_instance
        
        result = await phone_client.provision_phone_number(
            phone_number='+14155551234',
            friendly_name='Test Number'
        )
        
        assert result['sid'] == 'PN123456789'
        assert result['phone_number'] == '+14155551234'
        assert result['status'] == 'active'
        
    @pytest.mark.asyncio
    async def test_list_provisioned_numbers(self, phone_client, mock_twilio_client):
        """Test listing provisioned phone numbers."""
        mock_number = Mock()
        mock_number.sid = 'PN123456789'
        mock_number.phone_number = '+14155551234'
        mock_number.friendly_name = 'Test Number'
        mock_number.voice_url = 'https://example.com/webhook/voice'
        mock_number.sms_url = 'https://example.com/webhook/sms'
        mock_number.capabilities = {'voice': True, 'sms': True}
        mock_number.status = 'active'
        
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.incoming_phone_numbers.list.return_value = [mock_number]
        phone_client.client = mock_client_instance
        
        results = await phone_client.list_provisioned_numbers()
        
        assert len(results) == 1
        assert results[0]['sid'] == 'PN123456789'
        
    @pytest.mark.asyncio
    async def test_release_phone_number_success(self, phone_client, mock_twilio_client):
        """Test successful phone number release."""
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.incoming_phone_numbers.return_value.delete.return_value = None
        phone_client.client = mock_client_instance
        
        result = await phone_client.release_phone_number('PN123456789')
        
        assert result is True
        mock_client_instance.incoming_phone_numbers.assert_called_with('PN123456789')
        
    @pytest.mark.asyncio
    async def test_update_phone_number_webhooks(self, phone_client, mock_twilio_client):
        """Test updating phone number webhooks."""
        mock_number = Mock()
        mock_number.sid = 'PN123456789'
        mock_number.phone_number = '+14155551234'
        mock_number.voice_url = 'https://new.example.com/voice'
        mock_number.sms_url = 'https://new.example.com/sms'
        
        mock_client_instance = mock_twilio_client.return_value
        mock_client_instance.incoming_phone_numbers.return_value.update.return_value = mock_number
        phone_client.client = mock_client_instance
        
        result = await phone_client.update_phone_number_webhooks(
            number_sid='PN123456789',
            voice_url='https://new.example.com/voice',
            sms_url='https://new.example.com/sms'
        )
        
        assert result['voice_url'] == 'https://new.example.com/voice'
        assert result['sms_url'] == 'https://new.example.com/sms'


class TestPhoneService:
    """Test cases for PhoneService."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock TwilioPhoneClient."""
        return Mock(spec=TwilioPhoneClient)
        
    @pytest.fixture
    def phone_service(self, mock_twilio_client):
        """Create PhoneService instance with mocked client."""
        return PhoneService(twilio_client=mock_twilio_client)
        
    @pytest.mark.asyncio
    async def test_search_available_numbers(self, phone_service, mock_twilio_client):
        """Test searching for available numbers."""
        mock_twilio_client.search_phone_numbers = AsyncMock(return_value=[
            {
                'phone_number': '+14155551234',
                'friendly_name': 'SF Number',
                'locality': 'San Francisco',
                'region': 'CA',
                'capabilities': {'voice': True, 'sms': True}
            }
        ])
        
        preferences = {
            'area_code': '415',
            'contains': '555',
            'limit': 10
        }
        
        results = await phone_service.search_available_numbers(preferences)
        
        assert len(results) == 1
        assert results[0]['phone_number'] == '+14155551234'
        assert results[0]['cost_per_month'] == '$1.00'
        assert results[0]['recommended'] is True
        
        mock_twilio_client.search_phone_numbers.assert_called_once_with(
            area_code='415',
            contains='555',
            country_code='US',
            limit=10
        )
        
    @pytest.mark.asyncio
    async def test_provision_number(self, phone_service, mock_twilio_client):
        """Test provisioning a phone number."""
        mock_twilio_client.provision_phone_number = AsyncMock(return_value={
            'sid': 'PN123456789',
            'phone_number': '+14155551234',
            'friendly_name': 'Number for Tenant test-tenant',
            'status': 'active'
        })
        
        with patch('src.services.phone.phone_service.PhoneService._get_current_timestamp', return_value='2023-01-01T12:00:00Z'):
            result = await phone_service.provision_number(
                phone_number='+14155551234',
                tenant_id='test-tenant'
            )
            
        assert result['tenant_id'] == 'test-tenant'
        assert result['provisioned_at'] == '2023-01-01T12:00:00Z'
        assert result['monthly_cost'] == '$1.00'
        
    @pytest.mark.asyncio
    async def test_get_tenant_numbers(self, phone_service, mock_twilio_client):
        """Test getting tenant's phone numbers."""
        mock_twilio_client.list_provisioned_numbers = AsyncMock(return_value=[
            {
                'sid': 'PN123456789',
                'phone_number': '+14155551234',
                'friendly_name': 'Number for Tenant test-tenant'
            },
            {
                'sid': 'PN987654321',
                'phone_number': '+14155559999',
                'friendly_name': 'Number for Tenant other-tenant'
            }
        ])
        
        results = await phone_service.get_tenant_numbers('test-tenant')
        
        assert len(results) == 1
        assert results[0]['sid'] == 'PN123456789'
        assert results[0]['tenant_id'] == 'test-tenant'
        
    @pytest.mark.asyncio
    async def test_release_number_success(self, phone_service, mock_twilio_client):
        """Test successful number release."""
        # Mock get_tenant_numbers to return the number
        phone_service.get_tenant_numbers = AsyncMock(return_value=[
            {'sid': 'PN123456789', 'phone_number': '+14155551234'}
        ])
        
        mock_twilio_client.release_phone_number = AsyncMock(return_value=True)
        
        result = await phone_service.release_number('PN123456789', 'test-tenant')
        
        assert result is True
        mock_twilio_client.release_phone_number.assert_called_once_with('PN123456789')
        
    @pytest.mark.asyncio
    async def test_release_number_not_owned(self, phone_service, mock_twilio_client):
        """Test releasing number not owned by tenant."""
        # Mock get_tenant_numbers to return empty list
        phone_service.get_tenant_numbers = AsyncMock(return_value=[])
        
        with pytest.raises(ValueError, match="Number PN123456789 not found for tenant test-tenant"):
            await phone_service.release_number('PN123456789', 'test-tenant')
            
    def test_is_recommended_number(self, phone_service):
        """Test number recommendation logic."""
        # Number with voice and SMS should be recommended
        number_good = {'capabilities': {'voice': True, 'sms': True}}
        assert phone_service._is_recommended_number(number_good) is True
        
        # Number with only voice should not be recommended
        number_voice_only = {'capabilities': {'voice': True, 'sms': False}}
        assert phone_service._is_recommended_number(number_voice_only) is False
        
        # Number with no capabilities should not be recommended
        number_none = {'capabilities': {}}
        assert phone_service._is_recommended_number(number_none) is False


class TestCallRouter:
    """Test cases for CallRouter."""
    pass

# Integration tests combining multiple components
class TestPhoneIntegration:
    """Integration tests for phone service components."""
    
    @pytest.fixture
    def phone_system(self):
        """Create integrated phone system."""
        with patch('src.services.twilio.twilio_phone_client.Client'):
            with patch.dict('os.environ', {
                'TWILIO_ACCOUNT_SID': 'test_sid',
                'TWILIO_AUTH_TOKEN': 'test_token'
            }):
                twilio_client = TwilioPhoneClient()
                phone_service = PhoneService(twilio_client)
                call_router = CallRouter()
                
                return {
                    'twilio_client': twilio_client,
                    'phone_service': phone_service,
                    'call_router': call_router
                }
                
    @pytest.mark.asyncio
    async def test_full_phone_provisioning_workflow(self, phone_system):
        """Test complete phone number provisioning workflow."""
        phone_service = phone_system['phone_service']
        
        # Mock the underlying Twilio client methods
        phone_service.twilio_client.search_phone_numbers = AsyncMock(return_value=[
            {'phone_number': '+14155551234', 'capabilities': {'voice': True, 'sms': True}}
        ])
        
        phone_service.twilio_client.provision_phone_number = AsyncMock(return_value={
            'sid': 'PN123456789',
            'phone_number': '+14155551234',
            'status': 'active'
        })
        
        # 1. Search for numbers
        available = await phone_service.search_available_numbers({'area_code': '415'})
        assert len(available) == 1
        
        # 2. Provision a number
        provisioned = await phone_service.provision_number(
            available[0]['phone_number'],
            'test-tenant'
        )
        assert provisioned['tenant_id'] == 'test-tenant'
        
    @pytest.mark.asyncio
    async def test_call_handling_with_provisioned_number(self, phone_system):
        """Test call handling for a provisioned number."""
        call_router = phone_system['call_router']
        
        # Simulate incoming call
        call_data = {
            'From': '+14155551234',
            'To': '+14155559999',
            'CallStatus': 'ringing'
        }
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value.hour = 10  # Business hours
            
            twiml_response = await call_router.handle_incoming_call(call_data, 'test-tenant')
            
        # Should route to voice agent
        assert 'voice-agent-test-tenant' in twiml_response
        assert '<Conference' in twiml_response


# Database integration tests
class TestPhoneServiceDatabaseIntegration:
    """Test cases for phone service database integration."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()
        
    @pytest.fixture
    def mock_twilio_client(self):
        """Create a mock TwilioPhoneClient."""
        return Mock(spec=TwilioPhoneClient)
        
    @pytest.fixture
    def phone_service_with_db(self, mock_twilio_client, mock_db_session):
        """Create PhoneService instance with database session."""
        return PhoneService(twilio_client=mock_twilio_client, db_session=mock_db_session)
        
    @pytest.fixture
    def mock_voice_agent(self):
        """Create a mock VoiceAgent."""
        agent = Mock(spec=VoiceAgent)
        agent.id = uuid.uuid4()
        agent.name = "Test Agent"
        agent.tenant_id = uuid.uuid4()
        agent.phone_number = None
        agent.configuration = {}
        agent.status = 'active'
        agent.is_active = True
        return agent
        
    @pytest.mark.asyncio
    async def test_provision_phone_number_for_agent_success(self, phone_service_with_db, mock_db_session, mock_twilio_client, mock_voice_agent):
        """Test successful phone number provisioning for agent."""
        # Setup mocks
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_voice_agent
        mock_twilio_client.provision_phone_number = AsyncMock(return_value={
            'sid': 'PN123456789',
            'phone_number': '+14155551234',
            'status': 'active'
        })
        
        # Test provisioning
        result = await phone_service_with_db.provision_phone_number_for_agent(
            phone_number='+14155551234',
            agent_id=str(mock_voice_agent.id)
        )
        
        # Verify result
        assert result['status'] == 'success'
        assert result['phone_number'] == '+14155551234'
        assert result['phone_sid'] == 'PN123456789'
        assert result['agent_id'] == str(mock_voice_agent.id)
        
        # Verify agent was updated
        assert mock_voice_agent.phone_number == '+14155551234'
        assert 'phone_config' in mock_voice_agent.configuration
        
        # Verify database commit
        mock_db_session.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_provision_phone_number_agent_not_found(self, phone_service_with_db, mock_db_session, mock_twilio_client):
        """Test phone provisioning with non-existent agent."""
        # Setup mocks
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test provisioning
        result = await phone_service_with_db.provision_phone_number_for_agent(
            phone_number='+14155551234',
            agent_id='450ffcf2-261d-495b-bcdc-d391840fb562'
        )
        
        # Verify error result
        assert result['status'] == 'error'
        assert 'not found' in result['error']
        
        # Verify rollback
        mock_db_session.rollback.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_provision_phone_number_agent_already_has_phone(self, phone_service_with_db, mock_db_session, mock_twilio_client, mock_voice_agent):
        """Test phone provisioning when agent already has a phone number."""
        # Setup mocks
        mock_voice_agent.phone_number = '+14155559999'  # Agent already has phone
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_voice_agent
        
        # Test provisioning
        result = await phone_service_with_db.provision_phone_number_for_agent(
            phone_number='+14155551234',
            agent_id=str(mock_voice_agent.id)
        )
        
        # Verify error result
        assert result['status'] == 'error'
        assert 'already has phone number' in result['error']
        
        # Verify rollback
        mock_db_session.rollback.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_agent_phone_number_success(self, phone_service_with_db, mock_db_session, mock_voice_agent):
        """Test getting phone number for an agent."""
        # Setup mocks
        mock_voice_agent.phone_number = '+14155551234'
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_voice_agent
        
        # Test getting phone number
        phone_number = await phone_service_with_db.get_agent_phone_number(str(mock_voice_agent.id))
        
        # Verify result
        assert phone_number == '+14155551234'
        
    @pytest.mark.asyncio
    async def test_get_agent_phone_number_agent_not_found(self, phone_service_with_db, mock_db_session):
        """Test getting phone number for non-existent agent."""
        # Setup mocks
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test getting phone number
        phone_number = await phone_service_with_db.get_agent_phone_number('450ffcf2-261d-495b-bcdc-d391840fb562')
        
        # Verify result
        assert phone_number is None
        
    @pytest.mark.asyncio
    async def test_release_agent_phone_number_success(self, phone_service_with_db, mock_db_session, mock_twilio_client, mock_voice_agent):
        """Test successful phone number release from agent."""
        # Setup mocks
        mock_voice_agent.phone_number = '+14155551234'
        mock_voice_agent.configuration = {
            'phone_config': {
                'phone_sid': 'PN123456789',
                'twilio_phone_number': '+14155551234'
            }
        }
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_voice_agent
        mock_twilio_client.release_phone_number = AsyncMock(return_value=True)
        
        # Test release
        result = await phone_service_with_db.release_agent_phone_number(str(mock_voice_agent.id))
        
        # Verify result
        assert result is True
        
        # Verify agent was updated
        assert mock_voice_agent.phone_number is None
        assert 'phone_config' not in mock_voice_agent.configuration
        
        # Verify Twilio release was called
        mock_twilio_client.release_phone_number.assert_called_once_with('PN123456789')
        
        # Verify database commit
        mock_db_session.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_release_agent_phone_number_no_phone(self, phone_service_with_db, mock_db_session, mock_voice_agent):
        """Test releasing phone from agent with no phone number."""
        # Setup mocks
        mock_voice_agent.phone_number = None
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_voice_agent
        
        # Test release
        with pytest.raises(ValueError, match="has no phone number to release"):
            await phone_service_with_db.release_agent_phone_number(str(mock_voice_agent.id))
            
        # Verify rollback
        mock_db_session.rollback.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_list_agents_with_phone_numbers(self, phone_service_with_db, mock_db_session):
        """Test listing agents with phone numbers."""
        # Create mock agents
        agent1 = Mock(spec=VoiceAgent)
        agent1.id = uuid.uuid4()
        agent1.name = "Agent 1"
        agent1.tenant_id = uuid.uuid4()
        agent1.phone_number = '+14155551234'
        agent1.status = 'active'
        agent1.is_active = True
        agent1.configuration = {
            'phone_config': {
                'phone_sid': 'PN123456789',
                'provisioned_at': '2023-01-01T12:00:00Z'
            }
        }
        
        agent2 = Mock(spec=VoiceAgent)
        agent2.id = uuid.uuid4()
        agent2.name = "Agent 2"
        agent2.tenant_id = uuid.uuid4()
        agent2.phone_number = '+14155559999'
        agent2.status = 'inactive'
        agent2.is_active = False
        agent2.configuration = {
            'phone_config': {
                'phone_sid': 'PN987654321',
                'provisioned_at': '2023-01-02T12:00:00Z'
            }
        }
        
        # Setup mocks
        mock_db_session.query.return_value.filter.return_value.all.return_value = [agent1, agent2]
        
        # Test listing
        agents = await phone_service_with_db.list_agents_with_phone_numbers()
        
        # Verify result
        assert len(agents) == 2
        
        assert agents[0]['agent_id'] == str(agent1.id)
        assert agents[0]['agent_name'] == 'Agent 1'
        assert agents[0]['phone_number'] == '+14155551234'
        assert agents[0]['phone_sid'] == 'PN123456789'
        assert agents[0]['status'] == 'active'
        assert agents[0]['is_active'] is True
        
        assert agents[1]['agent_id'] == str(agent2.id)
        assert agents[1]['agent_name'] == 'Agent 2'
        assert agents[1]['phone_number'] == '+14155559999'
        assert agents[1]['phone_sid'] == 'PN987654321'
        assert agents[1]['status'] == 'inactive'
        assert agents[1]['is_active'] is False
        
    @pytest.mark.asyncio
    async def test_list_agents_with_phone_numbers_filtered_by_tenant(self, phone_service_with_db, mock_db_session):
        """Test listing agents with phone numbers filtered by tenant."""
        # Setup mocks
        tenant_id = str(uuid.uuid4())
        mock_query = mock_db_session.query.return_value.filter.return_value
        mock_query.filter.return_value.all.return_value = []
        
        # Test listing with tenant filter
        agents = await phone_service_with_db.list_agents_with_phone_numbers(tenant_id=tenant_id)
        
        # Verify tenant filter was applied
        assert len(agents) == 0
        mock_query.filter.assert_called_once()
        
    def test_provision_phone_number_for_agent_no_db_session(self, mock_twilio_client):
        """Test phone provisioning without database session."""
        phone_service = PhoneService(twilio_client=mock_twilio_client, db_session=None)
        
        # Test provisioning should raise error
        with pytest.raises(ValueError, match="Database session is required"):
            import asyncio
            asyncio.run(phone_service.provision_phone_number_for_agent('+14155551234', 'agent-id'))