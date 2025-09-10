"""
Test suite for Twilio phone integration service.
TDD approach: Tests written for phone call handling and VoiceAgent integration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import uuid

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from src.services.twilio.twilio_client import TwilioClient
from src.services.twilio.phone_service import PhoneService
from src.services.twilio.call_handler import CallHandler


class TestTwilioClient:
    """Test Twilio API client functionality."""
    
    @pytest.fixture
    def mock_credentials(self):
        return {
            'account_sid': 'test_account_sid',
            'auth_token': 'test_auth_token',
            'phone_number': '+15551234567'
        }
    
    @pytest.fixture
    def client(self, mock_credentials):
        with patch('src.services.twilio.twilio_client.Client') as mock_twilio:
            client = TwilioClient(**mock_credentials)
            client.client = mock_twilio.return_value
            return client
    
    def test_client_initialization(self, mock_credentials):
        """Test Twilio client initializes with proper configuration."""
        with patch('src.services.twilio.twilio_client.Client'):
            client = TwilioClient(**mock_credentials)
            assert client.account_sid == mock_credentials['account_sid']
            assert client.auth_token == mock_credentials['auth_token']
            assert client.phone_number == mock_credentials['phone_number']
    
    def test_client_initialization_without_credentials(self):
        """Test client raises error without proper credentials."""
        with pytest.raises(ValueError, match="Account SID and Auth Token are required"):
            TwilioClient(account_sid=None, auth_token="token")
        
        with pytest.raises(ValueError, match="Account SID and Auth Token are required"):
            TwilioClient(account_sid="sid", auth_token=None)
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_make_call_success(self, mock_twilio_class, client):
        """Test successful outbound call creation."""
        mock_call = Mock()
        mock_call.sid = 'CA123456789'
        mock_call.status = 'queued'
        mock_call.date_created = datetime.now()
        mock_call.duration = None
        
        # Fix: Configure the mock properly
        client.client.calls.create.return_value = mock_call
        
        result = client.make_call(
            to_number='+15559876543',
            twiml_url='https://example.com/twiml'
        )
        
        assert result['call_sid'] == 'CA123456789'
        assert result['to'] == '+15559876543'
        assert result['status'] == 'queued'
        
        client.client.calls.create.assert_called_once()
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_make_call_failure(self, mock_twilio_class, client):
        """Test call creation failure handling."""
        # Fix: Configure the mock properly
        client.client.calls.create.side_effect = Exception("Twilio API error")
        
        with pytest.raises(Exception, match="Twilio API error"):
            client.make_call(
                to_number='+15559876543',
                twiml_url='https://example.com/twiml'
            )
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_send_sms_success(self, mock_twilio_class, client):
        """Test successful SMS sending."""
        mock_message = Mock()
        mock_message.sid = 'SM123456789'
        mock_message.status = 'queued'
        mock_message.date_created = datetime.now()
        
        # Fix: Configure the mock properly
        client.client.messages.create.return_value = mock_message
        
        result = client.send_sms(
            to_number='+15559876543',
            message='Test message'
        )
        
        assert result['message_sid'] == 'SM123456789'
        assert result['status'] == 'queued'
        assert result['body'] == 'Test message'
        
        client.client.messages.create.assert_called_once()
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_get_call_details(self, mock_twilio_class, client):
        """Test retrieving call details."""
        mock_call = Mock()
        mock_call.sid = 'CA123456789'
        mock_call.to = '+15559876543'
        mock_call.from_ = '+15551234567'
        mock_call.status = 'completed'
        mock_call.duration = '120'
        mock_call.start_time = datetime.now()
        mock_call.end_time = datetime.now()
        mock_call.direction = 'outbound-api'
        mock_call.answered_by = 'human'
        mock_call.price = '-0.015'
        mock_call.price_unit = 'USD'
        
        # Fix: Configure the mock properly
        client.client.calls.return_value.fetch.return_value = mock_call
        
        result = client.get_call_details('CA123456789')
        
        assert result['call_sid'] == 'CA123456789'
        assert result['status'] == 'completed'
        assert result['duration'] == '120'
        assert result['direction'] == 'outbound-api'
    
    def test_create_voice_response(self, client):
        """Test TwiML voice response creation."""
        twiml = client.create_voice_response("Hello, this is a test message")
        
        assert '<Say voice="alice">Hello, this is a test message</Say>' in twiml
        assert '<Response>' in twiml
    
    def test_create_gather_response(self, client):
        """Test TwiML gather response creation."""
        twiml = client.create_gather_response(
            message="Press 1 for sales",
            action_url="https://example.com/handle-input",
            num_digits=1
        )
        
        assert '<Gather' in twiml
        assert 'action="https://example.com/handle-input"' in twiml
        assert 'numDigits="1"' in twiml
        assert 'Press 1 for sales' in twiml
    
    def test_create_record_response(self, client):
        """Test TwiML record response creation."""
        twiml = client.create_record_response(
            message="Please leave a message after the beep",
            action_url="https://example.com/handle-recording"
        )
        
        assert '<Record' in twiml
        assert 'action="https://example.com/handle-recording"' in twiml
        assert 'Please leave a message after the beep' in twiml
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_validate_phone_number_success(self, mock_twilio_class, client):
        """Test successful phone number validation."""
        mock_phone_info = Mock()
        mock_phone_info.phone_number = '+15559876543'
        mock_phone_info.country_code = 'US'
        mock_phone_info.national_format = '(555) 987-6543'
        
        # Fix: Configure the mock properly
        client.client.lookups.v1.phone_numbers.return_value.fetch.return_value = mock_phone_info
        
        result = client.validate_phone_number('+15559876543')
        
        assert result['valid'] is True
        assert result['phone_number'] == '+15559876543'
        assert result['country_code'] == 'US'
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_validate_phone_number_failure(self, mock_twilio_class, client):
        """Test phone number validation failure."""
        # Fix: Configure the mock properly
        client.client.lookups.v1.phone_numbers.return_value.fetch.side_effect = Exception("Invalid number")
        
        result = client.validate_phone_number('invalid-number')
        
        assert result['valid'] is False
        assert 'error' in result


class TestPhoneService:
    """Test phone service integration with VoiceAgent models."""
    
    @pytest.fixture
    def mock_twilio_client(self):
        return Mock(spec=TwilioClient)
    
    @pytest.fixture
    def mock_voice_agent(self):
        agent = Mock()
        agent.id = 'agent_123'
        agent.name = 'Customer Service Agent'
        agent.description = 'Helpful customer service agent'
        agent.tenant_id = 'tenant_456'
        agent.knowledge_base = {
            'business_hours': {
                'title': 'Business Hours',
                'content': 'We are open Monday to Friday, 9 AM to 5 PM.',
                'confidence_score': 0.9
            },
            'contact_information': {
                'title': 'Contact Info',
                'content': 'You can reach us at support@company.com or call (555) 123-4567.',
                'confidence_score': 0.95
            }
        }
        return agent
    
    @pytest.fixture
    def phone_service(self, mock_twilio_client):
        return PhoneService(
            twilio_client=mock_twilio_client,
            webhook_base_url='https://example.com'
        )
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_initiate_outbound_call_success(self, mock_voice_agent_class, phone_service, mock_twilio_client, mock_voice_agent):
        """Test successful outbound call initiation."""
        # Setup mocks
        mock_voice_agent_class.get_by_id.return_value = mock_voice_agent
        mock_twilio_client.validate_phone_number.return_value = {'valid': True}
        mock_twilio_client.make_call.return_value = {
            'call_sid': 'CA123456789',
            'to': '+15559876543',
            'from': '+15551234567',
            'status': 'queued'
        }
        
        result = phone_service.initiate_outbound_call(
            voice_agent_id='agent_123',
            to_number='+15559876543',
            tenant_id='tenant_456',
            call_purpose='customer_service'
        )
        
        assert result['call_sid'] == 'CA123456789'
        assert result['status'] == 'initiated'
        assert result['voice_agent']['id'] == 'agent_123'
        assert result['to_number'] == '+15559876543'
        
        # Verify call session was created
        assert len(phone_service.active_calls) == 1
        call_session_id = result['call_session_id']
        call_session = phone_service.active_calls[call_session_id]
        assert call_session['voice_agent_id'] == 'agent_123'
        assert call_session['tenant_id'] == 'tenant_456'
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_initiate_outbound_call_invalid_agent(self, mock_voice_agent_class, phone_service):
        """Test outbound call with invalid agent ID."""
        mock_voice_agent_class.get_by_id.return_value = None
        
        with pytest.raises(ValueError, match="Voice agent .* not found"):
            phone_service.initiate_outbound_call(
                voice_agent_id='invalid_agent',
                to_number='+15559876543',
                tenant_id='tenant_456'
            )
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_initiate_outbound_call_invalid_phone(self, mock_voice_agent_class, phone_service, mock_twilio_client, mock_voice_agent):
        """Test outbound call with invalid phone number."""
        # Mock the VoiceAgent.get_by_id to return a valid agent first
        mock_voice_agent_class.get_by_id.return_value = mock_voice_agent
        mock_twilio_client.validate_phone_number.return_value = {'valid': False}
        
        with pytest.raises(ValueError, match="Invalid phone number"):
            phone_service.initiate_outbound_call(
                voice_agent_id='agent_123',
                to_number='invalid-number',
                tenant_id='tenant_456'
            )
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_handle_inbound_call_success(self, mock_voice_agent_class, phone_service, mock_twilio_client, mock_voice_agent):
        """Test successful inbound call handling."""
        mock_voice_agent_class.get_default_agent.return_value = mock_voice_agent
        mock_twilio_client.create_gather_response.return_value = '<Response>Mock TwiML</Response>'
        
        result = phone_service.handle_inbound_call(
            from_number='+15559876543',
            call_sid='CA987654321'
        )
        
        assert '<Response>' in result
        mock_twilio_client.create_gather_response.assert_called_once()
        
        # Verify call session was created
        assert len(phone_service.active_calls) == 1
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_handle_inbound_call_no_agent(self, mock_voice_agent_class, phone_service, mock_twilio_client):
        """Test inbound call when no agent is available."""
        mock_voice_agent_class.get_default_agent.return_value = None
        mock_twilio_client.create_voice_response.return_value = '<Response>No agents available</Response>'
        
        result = phone_service.handle_inbound_call(
            from_number='+15559876543',
            call_sid='CA987654321'
        )
        
        assert 'No agents available' in result or 'busy' in result.lower()
        mock_twilio_client.create_voice_response.assert_called_once()
    
    def test_handle_user_input_business_hours(self, phone_service, mock_voice_agent, mock_twilio_client):
        """Test user input handling for business hours inquiry."""
        # Setup call session
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        
        # Fix: Mock the TwiML response methods to return strings
        mock_twilio_client.create_gather_response.return_value = '<Response><Gather><Say>We are open Monday to Friday, 9 AM to 5 PM.</Say></Gather></Response>'
        
        result = phone_service.handle_user_input(
            call_session_id=call_session_id,
            user_input='What are your hours?',
            input_type='speech'
        )
        
        # Should return TwiML response with hours information
        assert isinstance(result, str)
        assert '<Response>' in result
        # The response should be processed by the agent's knowledge base
    
    def test_handle_user_input_pricing(self, phone_service, mock_voice_agent, mock_twilio_client):
        """Test user input handling for pricing inquiry."""
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        
        # Fix: Mock the TwiML response methods to return strings
        mock_twilio_client.create_voice_response.return_value = '<Response><Say>For pricing information, I can connect you with our sales team.</Say></Response>'
        
        result = phone_service.handle_user_input(
            call_session_id=call_session_id,
            user_input='How much does it cost?',
            input_type='speech'
        )
        
        assert isinstance(result, str)
        assert '<Response>' in result
        # Should handle pricing inquiry appropriately
    
    def test_handle_user_input_goodbye(self, phone_service, mock_voice_agent, mock_twilio_client):
        """Test user input handling for call completion."""
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        
        # Fix: Mock the TwiML response methods to return strings
        mock_twilio_client.create_voice_response.return_value = '<Response><Say>Thank you for calling! Have a great day.</Say></Response>'
        
        result = phone_service.handle_user_input(
            call_session_id=call_session_id,
            user_input='goodbye',
            input_type='speech'
        )
        
        assert isinstance(result, str)
        assert '<Response>' in result
        # Should handle call completion
    
    def test_handle_user_input_invalid_session(self, phone_service, mock_twilio_client):
        """Test user input with invalid session ID."""
        mock_twilio_client.create_voice_response.return_value = '<Response>Session expired</Response>'
        
        result = phone_service.handle_user_input(
            call_session_id='invalid_session',
            user_input='hello',
            input_type='speech'
        )
        
        assert 'Session expired' in result or 'call again' in result
    
    def test_handle_recording_complete(self, phone_service, mock_voice_agent, mock_twilio_client):
        """Test recording completion handling."""
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        
        # Fix: Mock the TwiML response methods to return strings
        mock_twilio_client.create_voice_response.return_value = '<Response><Say>Thank you for your message. We will get back to you soon.</Say></Response>'
        
        result = phone_service.handle_recording_complete(
            call_session_id=call_session_id,
            recording_url='https://api.twilio.com/recordings/RE123.wav',
            transcription='This is a test recording'
        )
        
        assert isinstance(result, str)
        assert '<Response>' in result
        
        # Verify recording info was stored
        call_session = phone_service.active_calls[call_session_id]
        assert call_session['recording_url'] == 'https://api.twilio.com/recordings/RE123.wav'
        assert call_session['transcription'] == 'This is a test recording'
    
    def test_end_call_session(self, phone_service, mock_voice_agent):
        """Test call session cleanup."""
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        
        success = phone_service.end_call_session(call_session_id)
        
        assert success is True
        call_session = phone_service.active_calls[call_session_id]
        assert call_session['status'] == 'completed'
        assert 'ended_at' in call_session


class TestCallHandler:
    """Test call handler webhook functionality."""
    
    @pytest.fixture
    def mock_phone_service(self):
        mock_service = Mock(spec=PhoneService)
        # Fix: Add the twilio attribute that CallHandler expects
        mock_service.twilio = Mock(spec=TwilioClient)
        mock_service.twilio.create_voice_response.return_value = '<Response>Mock TwiML</Response>'
        mock_service.twilio.create_gather_response.return_value = '<Response>Gather TwiML</Response>'
        return mock_service
    
    @pytest.fixture
    def call_handler(self, mock_phone_service):
        return CallHandler(phone_service=mock_phone_service)
    
    def test_handle_call_webhook_ringing(self, call_handler):
        """Test call webhook for ringing status."""
        webhook_data = {
            'CallStatus': 'ringing',
            'CallSid': 'CA123456789',
            'From': '+15559876543'
        }
        
        result = call_handler.handle_call_webhook('session_123', webhook_data)
        
        assert '<Response>' in result
        # Ringing status should return empty response
    
    def test_handle_call_webhook_answered(self, call_handler, mock_phone_service):
        """Test call webhook for answered status."""
        mock_voice_agent = Mock()
        mock_voice_agent.name = 'Test Agent'
        
        mock_phone_service.get_call_session.return_value = {
            'voice_agent': mock_voice_agent,
            'status': 'active'
        }
        mock_phone_service.webhook_base_url = 'https://example.com'
        mock_phone_service.twilio.create_gather_response.return_value = '<Response>Gather</Response>'
        
        webhook_data = {
            'CallStatus': 'in-progress',
            'CallSid': 'CA123456789',
            'From': '+15559876543'
        }
        
        result = call_handler.handle_call_webhook('session_123', webhook_data)
        
        assert '<Response>' in result
        mock_phone_service.twilio.create_gather_response.assert_called_once()
    
    def test_handle_call_webhook_completed(self, call_handler, mock_phone_service):
        """Test call webhook for completed status."""
        webhook_data = {
            'CallStatus': 'completed',
            'CallSid': 'CA123456789',
            'CallDuration': '120'
        }
        
        result = call_handler.handle_call_webhook('session_123', webhook_data)
        
        assert '<Response>' in result
        mock_phone_service.end_call_session.assert_called_once_with('session_123')
    
    def test_handle_gather_webhook_digits(self, call_handler, mock_phone_service):
        """Test gather webhook with digit input."""
        mock_phone_service.handle_user_input.return_value = '<Response>Handled</Response>'
        
        webhook_data = {
            'Digits': '1',
            'CallSid': 'CA123456789'
        }
        
        result = call_handler.handle_gather_webhook('session_123', webhook_data)
        
        assert result == '<Response>Handled</Response>'
        mock_phone_service.handle_user_input.assert_called_once_with(
            call_session_id='session_123',
            user_input='1',
            input_type='digits'
        )
    
    def test_handle_gather_webhook_speech(self, call_handler, mock_phone_service):
        """Test gather webhook with speech input."""
        mock_phone_service.handle_user_input.return_value = '<Response>Speech Handled</Response>'
        
        webhook_data = {
            'SpeechResult': 'What are your business hours?',
            'CallSid': 'CA123456789'
        }
        
        result = call_handler.handle_gather_webhook('session_123', webhook_data)
        
        assert result == '<Response>Speech Handled</Response>'
        mock_phone_service.handle_user_input.assert_called_once_with(
            call_session_id='session_123',
            user_input='What are your business hours?',
            input_type='speech'
        )
    
    def test_handle_gather_webhook_no_input(self, call_handler):
        """Test gather webhook with no input."""
        webhook_data = {
            'CallSid': 'CA123456789'
        }
        
        result = call_handler.handle_gather_webhook('session_123', webhook_data)
        
        # Should handle no input gracefully
        assert isinstance(result, str)
        assert '<Response>' in result
    
    def test_handle_recording_webhook(self, call_handler, mock_phone_service):
        """Test recording webhook handling."""
        mock_phone_service.handle_recording_complete.return_value = '<Response>Recording processed</Response>'
        
        webhook_data = {
            'RecordingUrl': 'https://api.twilio.com/recordings/RE123.wav',
            'RecordingDuration': '30',
            'TranscriptionText': 'This is a test message',
            'CallSid': 'CA123456789'
        }
        
        result = call_handler.handle_recording_webhook('session_123', webhook_data)
        
        assert result == '<Response>Recording processed</Response>'
        mock_phone_service.handle_recording_complete.assert_called_once()
    
    def test_handle_status_webhook(self, call_handler, mock_phone_service):
        """Test status webhook handling."""
        mock_phone_service.get_call_session.return_value = {
            'status': 'active',
            'voice_agent_id': 'agent_123'
        }
        
        webhook_data = {
            'CallStatus': 'completed',
            'CallSid': 'CA123456789',
            'CallDuration': '180'
        }
        
        result = call_handler.handle_status_webhook('session_123', webhook_data)
        
        assert result['status'] == 'received'
        assert result['call_status'] == 'completed'
    
    @patch('src.services.twilio.call_handler.CallHandler._handle_call_ringing')
    def test_conference_call_creation(self, mock_handle_ringing, call_handler, mock_phone_service):
        """Test conference call creation."""
        mock_phone_service.twilio.client.calls.create.return_value = Mock(sid='CA123456789')
        mock_phone_service.twilio.phone_number = '+15551234567'
        mock_phone_service.webhook_base_url = 'https://example.com'
        
        result = call_handler.create_conference_call(
            call_session_id='session_123',
            participant_numbers=['+15559876543', '+15555551234'],
            moderator_number='+15551111111'
        )
        
        assert result['conference_name'] == 'session-session_123'
        assert len(result['participants']) == 3  # 2 participants + 1 moderator
        assert result['status'] == 'active'


class TestTwilioIntegrationWorkflow:
    """Integration tests for complete Twilio workflow."""
    
    @pytest.fixture
    def mock_voice_agent(self):
        agent = Mock()
        agent.id = 'agent_123'
        agent.name = 'Integration Test Agent'
        agent.tenant_id = 'tenant_456'
        agent.knowledge_base = {
            'business_hours': {
                'content': 'We are open 24/7 for your convenience.',
                'confidence_score': 0.9
            }
        }
        return agent
    
    @patch('src.services.twilio.twilio_client.Client')
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_complete_outbound_call_workflow(self, mock_voice_agent_class, mock_twilio_class, mock_voice_agent):
        """Test complete outbound call workflow."""
        # Setup mocks
        mock_voice_agent_class.get_by_id.return_value = mock_voice_agent
        
        mock_twilio = Mock()
        mock_twilio_class.return_value = mock_twilio
        
        # Mock successful call creation
        mock_call = Mock()
        mock_call.sid = 'CA123456789'
        mock_call.status = 'queued'
        mock_call.date_created = datetime.now()
        mock_call.duration = None
        mock_twilio.calls.create.return_value = mock_call
        
        # Create services
        twilio_client = TwilioClient('test_sid', 'test_token', '+15551234567')
        phone_service = PhoneService(twilio_client, webhook_base_url='https://example.com')
        call_handler = CallHandler(phone_service)
        
        # Mock phone validation
        twilio_client.validate_phone_number = Mock(return_value={'valid': True})
        
        # Initiate call
        call_result = phone_service.initiate_outbound_call(
            voice_agent_id='agent_123',
            to_number='+15559876543',
            tenant_id='tenant_456'
        )
        
        assert call_result['status'] == 'initiated'
        call_session_id = call_result['call_session_id']
        
        # Simulate call answered webhook
        webhook_data = {
            'CallStatus': 'in-progress',
            'CallSid': 'CA123456789',
            'From': '+15559876543'
        }
        
        # Mock TwiML responses
        twilio_client.create_gather_response = Mock(return_value='<Response>Gather</Response>')
        
        twiml_response = call_handler.handle_call_webhook(call_session_id, webhook_data)
        
        assert '<Response>' in twiml_response
        
        # Simulate user input
        phone_service.handle_user_input = Mock(return_value='<Response>Input handled</Response>')
        
        gather_webhook_data = {
            'Digits': '1',
            'CallSid': 'CA123456789'
        }
        
        input_response = call_handler.handle_gather_webhook(call_session_id, gather_webhook_data)
        assert input_response == '<Response>Input handled</Response>'
        
        # Verify call session exists and has proper data
        call_session = phone_service.get_call_session(call_session_id)
        assert call_session is not None
        assert call_session['voice_agent_id'] == 'agent_123'
        assert call_session['call_sid'] == 'CA123456789'


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""
    
    @patch('src.services.twilio.twilio_client.Client')
    def test_twilio_api_unavailable(self, mock_twilio_class):
        """Test handling when Twilio API is unavailable."""
        mock_twilio_class.side_effect = Exception("Twilio service unavailable")
        
        with pytest.raises(Exception, match="Twilio service unavailable"):
            TwilioClient('test_sid', 'test_token')
    
    def test_invalid_webhook_data(self):
        """Test handling of malformed webhook data."""
        mock_phone_service = Mock(spec=PhoneService)
        # Fix: Add the twilio attribute that CallHandler expects
        mock_phone_service.twilio = Mock(spec=TwilioClient)
        mock_phone_service.twilio.create_voice_response.return_value = '<Response>Error</Response>'
        call_handler = CallHandler(mock_phone_service)
        
        # Malformed webhook data
        webhook_data = {}
        
        result = call_handler.handle_call_webhook('session_123', webhook_data)
        
        # Should handle gracefully
        assert isinstance(result, str)
        assert '<Response>' in result
    
    def test_call_session_cleanup_on_error(self):
        """Test proper cleanup when call encounters error."""
        mock_twilio_client = Mock(spec=TwilioClient)
        phone_service = PhoneService(mock_twilio_client)
        
        # Create a call session
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        # End session
        success = phone_service.end_call_session(call_session_id)
        
        assert success is True
        call_session = phone_service.active_calls[call_session_id]
        assert call_session['status'] == 'completed'
    
    @patch('src.services.twilio.phone_service.VoiceAgent')
    def test_agent_knowledge_base_empty(self, mock_voice_agent_class):
        """Test handling when agent has no knowledge base."""
        mock_agent = Mock()
        mock_agent.id = 'agent_empty'
        mock_agent.name = 'Empty Agent'
        mock_agent.knowledge_base = {}
        
        mock_twilio_client = Mock(spec=TwilioClient)
        # Fix: Mock the TwiML response methods to return strings
        mock_twilio_client.create_voice_response.return_value = '<Response><Say>I apologize, but I\'m having difficulty processing your request.</Say></Response>'
        mock_twilio_client.create_gather_response.return_value = '<Response><Gather><Say>How else can I help you today?</Say></Gather></Response>'
        phone_service = PhoneService(mock_twilio_client)
        
        call_session_id = str(uuid.uuid4())
        phone_service.active_calls[call_session_id] = {
            'voice_agent': mock_agent,
            'status': 'active'
        }
        
        # Should handle empty knowledge base gracefully
        result = phone_service.handle_user_input(
            call_session_id=call_session_id,
            user_input='What are your hours?',
            input_type='speech'
        )
        
        assert isinstance(result, str)
        assert '<Response>' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])