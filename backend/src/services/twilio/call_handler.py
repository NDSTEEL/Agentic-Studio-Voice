"""
Call handler for managing Twilio webhook endpoints and call flow orchestration.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from typing import Dict, Optional, Any
import logging
from datetime import datetime
import json

from .phone_service import PhoneService
from .twilio_client import TwilioClient


logger = logging.getLogger(__name__)


class CallHandler:
    """Handler for Twilio webhook callbacks and call orchestration."""
    
    def __init__(self, phone_service: PhoneService):
        """
        Initialize call handler.
        
        Args:
            phone_service: Configured phone service instance
        """
        self.phone_service = phone_service
        self.twilio = phone_service.twilio
    
    def handle_call_webhook(
        self,
        call_session_id: str,
        webhook_data: Dict[str, Any]
    ) -> str:
        """
        Handle incoming call webhook from Twilio.
        
        Args:
            call_session_id: Call session identifier
            webhook_data: Webhook data from Twilio
        
        Returns:
            TwiML response string
        """
        try:
            call_status = webhook_data.get('CallStatus', 'unknown')
            call_sid = webhook_data.get('CallSid')
            from_number = webhook_data.get('From')
            
            logger.info(f"Handling call webhook for session {call_session_id}, status: {call_status}")
            
            if call_status == 'ringing':
                return self._handle_call_ringing(call_session_id, webhook_data)
            elif call_status == 'in-progress':
                return self._handle_call_answered(call_session_id, webhook_data)
            elif call_status == 'completed':
                return self._handle_call_completed(call_session_id, webhook_data)
            elif call_status == 'failed' or call_status == 'busy' or call_status == 'no-answer':
                return self._handle_call_failed(call_session_id, webhook_data)
            else:
                # For initial call setup or unknown status
                call_session = self.phone_service.get_call_session(call_session_id)
                if call_session:
                    # Existing session - continue with agent interaction
                    return self._handle_agent_interaction(call_session_id, webhook_data)
                else:
                    # New inbound call
                    return self.phone_service.handle_inbound_call(
                        from_number=from_number,
                        call_sid=call_sid
                    )
                    
        except Exception as e:
            logger.error(f"Error handling call webhook for session {call_session_id}: {str(e)}")
            return self.twilio.create_voice_response(
                "We're experiencing technical difficulties. Please try again later."
            )
    
    def handle_gather_webhook(
        self,
        call_session_id: str,
        webhook_data: Dict[str, Any]
    ) -> str:
        """
        Handle user input gathering webhook.
        
        Args:
            call_session_id: Call session identifier
            webhook_data: Webhook data from Twilio
        
        Returns:
            TwiML response string
        """
        try:
            digits = webhook_data.get('Digits', '')
            speech_result = webhook_data.get('SpeechResult', '')
            
            # Determine input type and content
            if digits:
                user_input = digits
                input_type = 'digits'
            elif speech_result:
                user_input = speech_result
                input_type = 'speech'
            else:
                # No input received
                return self._handle_no_input(call_session_id)
            
            logger.info(f"Handling user input for session {call_session_id}: {user_input} ({input_type})")
            
            return self.phone_service.handle_user_input(
                call_session_id=call_session_id,
                user_input=user_input,
                input_type=input_type
            )
            
        except Exception as e:
            logger.error(f"Error handling gather webhook for session {call_session_id}: {str(e)}")
            return self.twilio.create_voice_response(
                "I'm having trouble processing your input. Let me transfer you to a human agent."
            )
    
    def handle_recording_webhook(
        self,
        call_session_id: str,
        webhook_data: Dict[str, Any]
    ) -> str:
        """
        Handle recording completion webhook.
        
        Args:
            call_session_id: Call session identifier
            webhook_data: Webhook data from Twilio
        
        Returns:
            TwiML response string
        """
        try:
            recording_url = webhook_data.get('RecordingUrl')
            recording_duration = webhook_data.get('RecordingDuration', '0')
            transcription_text = webhook_data.get('TranscriptionText')
            
            logger.info(f"Handling recording completion for session {call_session_id}")
            
            return self.phone_service.handle_recording_complete(
                call_session_id=call_session_id,
                recording_url=recording_url,
                transcription=transcription_text
            )
            
        except Exception as e:
            logger.error(f"Error handling recording webhook for session {call_session_id}: {str(e)}")
            return self.twilio.create_voice_response(
                "Thank you for your message. We will get back to you."
            )
    
    def handle_status_webhook(
        self,
        call_session_id: str,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Handle call status update webhook.
        
        Args:
            call_session_id: Call session identifier
            webhook_data: Webhook data from Twilio
        
        Returns:
            Status acknowledgment
        """
        try:
            call_status = webhook_data.get('CallStatus')
            call_sid = webhook_data.get('CallSid')
            call_duration = webhook_data.get('CallDuration')
            
            logger.info(f"Call status update for session {call_session_id}: {call_status}")
            
            # Update call session status
            call_session = self.phone_service.get_call_session(call_session_id)
            if call_session:
                call_session['twilio_status'] = call_status
                call_session['call_duration'] = call_duration
                call_session['last_status_update'] = datetime.now().isoformat()
                
                # If call is completed, mark session as ended
                if call_status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
                    self.phone_service.end_call_session(call_session_id)
            
            return {'status': 'received', 'call_status': call_status}
            
        except Exception as e:
            logger.error(f"Error handling status webhook for session {call_session_id}: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def create_conference_call(
        self,
        call_session_id: str,
        participant_numbers: list,
        moderator_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a conference call with multiple participants.
        
        Args:
            call_session_id: Call session identifier
            participant_numbers: List of phone numbers to include
            moderator_number: Optional moderator phone number
        
        Returns:
            Conference call details
        """
        try:
            # Create conference room name
            conference_name = f"session-{call_session_id}"
            
            # Create conference webhook URLs
            webhook_base = self.phone_service.webhook_base_url
            status_callback_url = f"{webhook_base}/twilio/conference-status/{call_session_id}"
            
            participants = []
            
            # Add moderator if specified
            if moderator_number:
                mod_call = self.twilio.client.calls.create(
                    to=moderator_number,
                    from_=self.twilio.phone_number,
                    twiml=f'''
                    <Response>
                        <Dial>
                            <Conference startConferenceOnEnter="true" endConferenceOnExit="true">
                                {conference_name}
                            </Conference>
                        </Dial>
                    </Response>
                    ''',
                    status_callback=status_callback_url
                )
                participants.append({
                    'number': moderator_number,
                    'call_sid': mod_call.sid,
                    'role': 'moderator'
                })
            
            # Add participants
            for number in participant_numbers:
                participant_call = self.twilio.client.calls.create(
                    to=number,
                    from_=self.twilio.phone_number,
                    twiml=f'''
                    <Response>
                        <Dial>
                            <Conference>{conference_name}</Conference>
                        </Dial>
                    </Response>
                    ''',
                    status_callback=status_callback_url
                )
                participants.append({
                    'number': number,
                    'call_sid': participant_call.sid,
                    'role': 'participant'
                })
            
            conference_details = {
                'conference_name': conference_name,
                'call_session_id': call_session_id,
                'participants': participants,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            logger.info(f"Created conference call {conference_name} with {len(participants)} participants")
            
            return conference_details
            
        except Exception as e:
            logger.error(f"Error creating conference call for session {call_session_id}: {str(e)}")
            raise
    
    def end_conference_call(self, conference_name: str) -> bool:
        """
        End a conference call.
        
        Args:
            conference_name: Conference identifier
        
        Returns:
            Success status
        """
        try:
            # End the conference
            conferences = self.twilio.client.conferences.list(friendly_name=conference_name)
            
            for conference in conferences:
                if conference.status == 'in-progress':
                    # End all participants
                    participants = conference.participants.list()
                    for participant in participants:
                        participant.delete()  # Remove participant from conference
                    
                    logger.info(f"Ended conference {conference_name}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ending conference {conference_name}: {str(e)}")
            return False
    
    def _handle_call_ringing(self, call_session_id: str, webhook_data: Dict[str, Any]) -> str:
        """Handle call ringing status."""
        logger.info(f"Call {call_session_id} is ringing")
        # Return empty response - Twilio will continue with the call
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    def _handle_call_answered(self, call_session_id: str, webhook_data: Dict[str, Any]) -> str:
        """Handle call answered status."""
        logger.info(f"Call {call_session_id} was answered")
        
        # Get call session and generate initial response
        call_session = self.phone_service.get_call_session(call_session_id)
        if call_session and call_session.get('voice_agent'):
            voice_agent = call_session['voice_agent']
            greeting = call_session.get('custom_greeting')
            
            if not greeting:
                greeting = f"Hello! This is {voice_agent.name}. Thank you for taking our call. How can I assist you today?"
            
            # Create gather response for initial interaction
            action_url = f"{self.phone_service.webhook_base_url}/twilio/gather/{call_session_id}"
            return self.twilio.create_gather_response(
                message=greeting,
                action_url=action_url,
                timeout=10
            )
        
        return self.twilio.create_voice_response("Hello! Thank you for taking our call.")
    
    def _handle_call_completed(self, call_session_id: str, webhook_data: Dict[str, Any]) -> str:
        """Handle call completion."""
        duration = webhook_data.get('CallDuration', '0')
        logger.info(f"Call {call_session_id} completed after {duration} seconds")
        
        # End the call session
        self.phone_service.end_call_session(call_session_id)
        
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    def _handle_call_failed(self, call_session_id: str, webhook_data: Dict[str, Any]) -> str:
        """Handle call failure."""
        call_status = webhook_data.get('CallStatus')
        logger.warning(f"Call {call_session_id} failed with status: {call_status}")
        
        # End the call session and potentially schedule retry
        self.phone_service.end_call_session(call_session_id)
        
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    
    def _handle_agent_interaction(self, call_session_id: str, webhook_data: Dict[str, Any]) -> str:
        """Handle ongoing agent interaction."""
        call_session = self.phone_service.get_call_session(call_session_id)
        if not call_session:
            return self.twilio.create_voice_response("Session not found. Please call again.")
        
        voice_agent = call_session.get('voice_agent')
        if not voice_agent:
            return self.twilio.create_voice_response("Agent not available. Please try again later.")
        
        # Generate initial agent interaction
        greeting = f"Hello! This is {voice_agent.name}. How can I help you today?"
        action_url = f"{self.phone_service.webhook_base_url}/twilio/gather/{call_session_id}"
        
        return self.twilio.create_gather_response(
            message=greeting,
            action_url=action_url,
            timeout=10
        )
    
    def _handle_no_input(self, call_session_id: str) -> str:
        """Handle case where no user input was received."""
        return self.twilio.create_voice_response(
            "I didn't hear anything. Please try calling again if you need assistance. Goodbye!"
        )