"""
Phone service for managing voice calls and integrating with VoiceAgent models.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from typing import Dict, Optional, Any, List
import logging
from datetime import datetime
import uuid

from .twilio_client import TwilioClient
from src.models.voice_agent import VoiceAgent
from src.services.voice.elevenlabs_client import ElevenLabsClient
from src.services.voice.voice_config import VoiceConfig


logger = logging.getLogger(__name__)


class PhoneService:
    """Service for managing phone calls with voice agents."""
    
    def __init__(
        self,
        twilio_client: TwilioClient,
        elevenlabs_client: Optional[ElevenLabsClient] = None,
        webhook_base_url: str = ""
    ):
        """
        Initialize phone service.
        
        Args:
            twilio_client: Configured Twilio client
            elevenlabs_client: Optional ElevenLabs client for custom voices
            webhook_base_url: Base URL for webhook endpoints
        """
        self.twilio = twilio_client
        self.elevenlabs = elevenlabs_client
        self.webhook_base_url = webhook_base_url
        self.active_calls: Dict[str, Dict[str, Any]] = {}
    
    def initiate_outbound_call(
        self,
        voice_agent_id: str,
        to_number: str,
        tenant_id: str,
        call_purpose: str = "customer_service",
        custom_greeting: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call using a voice agent.
        
        Args:
            voice_agent_id: ID of the voice agent to use
            to_number: Phone number to call
            tenant_id: Tenant identifier
            call_purpose: Purpose of the call
            custom_greeting: Custom greeting message
        
        Returns:
            Call initiation details
        """
        try:
            # Validate and get voice agent
            voice_agent = VoiceAgent.get_by_id(voice_agent_id, tenant_id)
            if not voice_agent:
                raise ValueError(f"Voice agent {voice_agent_id} not found")
            
            # Validate phone number
            phone_validation = self.twilio.validate_phone_number(to_number)
            if not phone_validation.get('valid'):
                raise ValueError(f"Invalid phone number: {to_number}")
            
            # Create call session
            call_session_id = str(uuid.uuid4())
            webhook_url = f"{self.webhook_base_url}/twilio/call/{call_session_id}"
            
            # Store call context
            self.active_calls[call_session_id] = {
                'voice_agent_id': voice_agent_id,
                'tenant_id': tenant_id,
                'call_purpose': call_purpose,
                'custom_greeting': custom_greeting,
                'to_number': to_number,
                'status': 'initiating',
                'created_at': datetime.now().isoformat(),
                'voice_agent': voice_agent
            }
            
            # Make the call
            call_result = self.twilio.make_call(
                to_number=to_number,
                twiml_url=webhook_url,
                record=True  # Record for quality and training
            )
            
            # Update call session with Twilio call SID
            self.active_calls[call_session_id]['call_sid'] = call_result['call_sid']
            self.active_calls[call_session_id]['status'] = 'in_progress'
            
            logger.info(f"Initiated outbound call {call_result['call_sid']} with agent {voice_agent_id}")
            
            return {
                'call_session_id': call_session_id,
                'call_sid': call_result['call_sid'],
                'status': 'initiated',
                'voice_agent': {
                    'id': voice_agent.id,
                    'name': voice_agent.name,
                    'description': voice_agent.description
                },
                'to_number': to_number
            }
            
        except Exception as e:
            logger.error(f"Failed to initiate outbound call: {str(e)}")
            raise
    
    def handle_inbound_call(
        self,
        from_number: str,
        call_sid: str,
        tenant_id: Optional[str] = None
    ) -> str:
        """
        Handle an incoming phone call.
        
        Args:
            from_number: Caller's phone number
            call_sid: Twilio call SID
            tenant_id: Optional tenant identifier
        
        Returns:
            TwiML response string
        """
        try:
            # Create call session for inbound call
            call_session_id = str(uuid.uuid4())
            
            # Find appropriate voice agent for inbound call
            # For now, use default agent - this could be enhanced with routing logic
            voice_agent = self._find_agent_for_inbound_call(from_number, tenant_id)
            
            if not voice_agent:
                # No agent available - provide fallback response
                return self.twilio.create_voice_response(
                    "Thank you for calling. All our agents are currently busy. Please try again later.",
                    voice="alice"
                )
            
            # Store inbound call context
            self.active_calls[call_session_id] = {
                'voice_agent_id': voice_agent.id,
                'tenant_id': tenant_id or voice_agent.tenant_id,
                'call_purpose': 'inbound_support',
                'from_number': from_number,
                'call_sid': call_sid,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'voice_agent': voice_agent,
                'direction': 'inbound'
            }
            
            # Generate greeting
            greeting = self._generate_agent_greeting(voice_agent)
            
            # Create TwiML response with greeting and next step
            action_url = f"{self.webhook_base_url}/twilio/gather/{call_session_id}"
            
            return self.twilio.create_gather_response(
                message=greeting,
                action_url=action_url,
                num_digits=1,
                timeout=10,
                voice=self._get_twilio_voice_for_agent(voice_agent)
            )
            
        except Exception as e:
            logger.error(f"Failed to handle inbound call from {from_number}: {str(e)}")
            # Return fallback response
            return self.twilio.create_voice_response(
                "We're experiencing technical difficulties. Please try again later.",
                voice="alice"
            )
    
    def handle_user_input(
        self,
        call_session_id: str,
        user_input: str,
        input_type: str = "digits"
    ) -> str:
        """
        Handle user input during a call.
        
        Args:
            call_session_id: Call session identifier
            user_input: User's input (digits or transcribed speech)
            input_type: Type of input ("digits" or "speech")
        
        Returns:
            TwiML response string
        """
        try:
            call_context = self.active_calls.get(call_session_id)
            if not call_context:
                return self.twilio.create_voice_response(
                    "Session expired. Please call again.",
                    voice="alice"
                )
            
            voice_agent = call_context['voice_agent']
            
            # Process input through voice agent's knowledge base
            agent_response = self._process_user_input_with_agent(
                voice_agent, 
                user_input, 
                input_type,
                call_context
            )
            
            # Determine next action based on response
            if agent_response.get('requires_transfer'):
                return self._handle_call_transfer(call_session_id, agent_response)
            elif agent_response.get('requires_callback'):
                return self._handle_callback_request(call_session_id, agent_response)
            elif agent_response.get('call_complete'):
                return self._handle_call_completion(call_session_id, agent_response)
            else:
                # Continue conversation
                return self._continue_conversation(call_session_id, agent_response)
                
        except Exception as e:
            logger.error(f"Failed to handle user input for session {call_session_id}: {str(e)}")
            return self.twilio.create_voice_response(
                "I'm having trouble processing your request. Let me transfer you to a human agent.",
                voice="alice"
            )
    
    def handle_recording_complete(
        self,
        call_session_id: str,
        recording_url: str,
        transcription: Optional[str] = None
    ) -> str:
        """
        Handle completed call recording.
        
        Args:
            call_session_id: Call session identifier
            recording_url: URL of the recording
            transcription: Optional transcription text
        
        Returns:
            TwiML response string
        """
        try:
            call_context = self.active_calls.get(call_session_id)
            if not call_context:
                return self.twilio.create_voice_response("Thank you for your message.")
            
            # Store recording information
            call_context['recording_url'] = recording_url
            call_context['transcription'] = transcription
            
            # Process recorded message if transcription available
            if transcription:
                voice_agent = call_context['voice_agent']
                response = self._process_user_input_with_agent(
                    voice_agent,
                    transcription,
                    "speech",
                    call_context
                )
                
                return self.twilio.create_voice_response(
                    response.get('message', 'Thank you for your message. We will get back to you soon.'),
                    voice=self._get_twilio_voice_for_agent(voice_agent)
                )
            
            return self.twilio.create_voice_response(
                "Thank you for your message. We will review it and get back to you."
            )
            
        except Exception as e:
            logger.error(f"Failed to handle recording for session {call_session_id}: {str(e)}")
            return self.twilio.create_voice_response("Thank you for your message.")
    
    def get_call_session(self, call_session_id: str) -> Optional[Dict[str, Any]]:
        """Get call session details."""
        return self.active_calls.get(call_session_id)
    
    def end_call_session(self, call_session_id: str) -> bool:
        """End and cleanup call session."""
        if call_session_id in self.active_calls:
            call_context = self.active_calls[call_session_id]
            call_context['status'] = 'completed'
            call_context['ended_at'] = datetime.now().isoformat()
            
            # Could save to database here for analytics
            logger.info(f"Call session {call_session_id} completed")
            
            # Remove from active calls after a delay (for potential webhook callbacks)
            # In production, this might be handled by a cleanup job
            return True
        return False
    
    def _find_agent_for_inbound_call(
        self, 
        from_number: str, 
        tenant_id: Optional[str]
    ) -> Optional[VoiceAgent]:
        """Find appropriate voice agent for inbound call."""
        # Simple implementation - in production this could include:
        # - Number-based routing
        # - Time-based routing
        # - Agent availability
        # - Customer history
        
        try:
            if tenant_id:
                # Get default agent for tenant
                agents = VoiceAgent.list_by_tenant(tenant_id)
                return agents[0] if agents else None
            else:
                # Get any available agent
                return VoiceAgent.get_default_agent()
        except:
            return None
    
    def _generate_agent_greeting(self, voice_agent: VoiceAgent) -> str:
        """Generate greeting message for voice agent."""
        if hasattr(voice_agent, 'custom_greeting') and voice_agent.custom_greeting:
            return voice_agent.custom_greeting
        
        company_name = getattr(voice_agent, 'company_name', 'our company')
        agent_name = voice_agent.name
        
        return f"Hello! Thank you for calling {company_name}. This is {agent_name}, your virtual assistant. How can I help you today?"
    
    def _get_twilio_voice_for_agent(self, voice_agent: VoiceAgent) -> str:
        """Get appropriate Twilio voice for agent."""
        # Map agent voice config to Twilio voices
        voice_config = getattr(voice_agent, 'voice_config', {})
        voice_type = voice_config.get('voice_type', 'professional')
        
        voice_mapping = {
            'professional': 'alice',
            'friendly': 'alice',
            'energetic': 'alice',
            'calm': 'alice'
        }
        
        return voice_mapping.get(voice_type, 'alice')
    
    def _process_user_input_with_agent(
        self,
        voice_agent: VoiceAgent,
        user_input: str,
        input_type: str,
        call_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user input through voice agent's knowledge base."""
        try:
            # This would integrate with the voice agent's AI processing
            # For now, provide a basic implementation
            
            knowledge_base = getattr(voice_agent, 'knowledge_base', {})
            
            # Simple keyword matching - in production this would use NLP
            user_input_lower = user_input.lower()
            
            if 'hours' in user_input_lower or 'open' in user_input_lower:
                hours_info = knowledge_base.get('business_hours', {})
                response = hours_info.get('content', 'Our standard business hours are Monday to Friday, 9 AM to 5 PM.')
                return {'message': response, 'requires_followup': True}
            
            elif 'price' in user_input_lower or 'cost' in user_input_lower:
                pricing_info = knowledge_base.get('pricing_packages', {})
                response = pricing_info.get('content', 'For pricing information, I can connect you with our sales team.')
                return {'message': response, 'requires_transfer': True, 'transfer_type': 'sales'}
            
            elif 'location' in user_input_lower or 'address' in user_input_lower:
                contact_info = knowledge_base.get('contact_information', {})
                response = contact_info.get('content', 'You can find our location and contact details on our website.')
                return {'message': response}
            
            elif any(word in user_input_lower for word in ['bye', 'goodbye', 'thanks', 'thank you']):
                return {
                    'message': 'Thank you for calling! Have a great day.',
                    'call_complete': True
                }
            
            else:
                # Default response
                return {
                    'message': 'I understand you need help. Let me connect you with a specialist who can better assist you.',
                    'requires_transfer': True,
                    'transfer_type': 'general'
                }
                
        except Exception as e:
            logger.error(f"Error processing user input with agent: {str(e)}")
            return {
                'message': 'I apologize, but I\'m having difficulty processing your request. Let me transfer you to a human agent.',
                'requires_transfer': True
            }
    
    def _handle_call_transfer(self, call_session_id: str, response: Dict[str, Any]) -> str:
        """Handle call transfer request."""
        transfer_message = "Please hold while I transfer your call to the appropriate department."
        
        # In production, this would integrate with a call center system
        # For now, provide a message and end the call
        return self.twilio.create_voice_response(
            f"{transfer_message} Thank you for calling, and someone will be with you shortly."
        )
    
    def _handle_callback_request(self, call_session_id: str, response: Dict[str, Any]) -> str:
        """Handle callback request."""
        call_context = self.active_calls.get(call_session_id, {})
        from_number = call_context.get('from_number', 'your number')
        
        return self.twilio.create_voice_response(
            f"I've scheduled a callback to {from_number}. Someone from our team will contact you within 24 hours. Thank you!"
        )
    
    def _handle_call_completion(self, call_session_id: str, response: Dict[str, Any]) -> str:
        """Handle call completion."""
        message = response.get('message', 'Thank you for calling. Have a great day!')
        return self.twilio.create_voice_response(message)
    
    def _continue_conversation(self, call_session_id: str, response: Dict[str, Any]) -> str:
        """Continue conversation with follow-up input gathering."""
        message = response.get('message', 'How else can I help you today?')
        
        if response.get('requires_followup'):
            action_url = f"{self.webhook_base_url}/twilio/gather/{call_session_id}"
            return self.twilio.create_gather_response(
                message=message,
                action_url=action_url,
                num_digits=1,
                timeout=10
            )
        else:
            return self.twilio.create_voice_response(message)