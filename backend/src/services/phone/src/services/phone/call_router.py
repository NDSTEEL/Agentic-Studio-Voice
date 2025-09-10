"""Call routing and webhook handling for Twilio integration."""

from typing import Dict, Any, Optional, Callable
import logging
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioException
from enum import Enum
from .twilio_client import TwilioPhoneClient

logger = logging.getLogger(__name__)


class CallAction(Enum):
    """Available call routing actions."""
    FORWARD = "forward"
    VOICEMAIL = "voicemail"
    HANGUP = "hangup"
    CONFERENCE = "conference"
    VOICE_AGENT = "voice_agent"


class CallRouter:
    """Handles incoming call routing and webhook processing."""
    
    def __init__(self, twilio_client: Optional[TwilioPhoneClient] = None):
        """Initialize call router.
        
        Args:
            twilio_client: Optional Twilio client instance (creates default if None)
        """
        self.routing_rules: Dict[str, Callable] = {}
        self.default_action = CallAction.VOICE_AGENT
        self.twilio_client = twilio_client or TwilioPhoneClient()
        
    def register_routing_rule(
        self,
        tenant_id: str,
        rule_handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """Register a custom routing rule for a tenant.
        
        Args:
            tenant_id: Tenant ID
            rule_handler: Function that takes call data and returns routing decision
        """
        self.routing_rules[tenant_id] = rule_handler
        logger.info(f"Registered routing rule for tenant {tenant_id}")
        
    async def handle_incoming_call(
        self,
        call_data: Dict[str, Any],
        tenant_id: str
    ) -> str:
        """Handle incoming call webhook from Twilio.
        
        Args:
            call_data: Call information from Twilio webhook
            tenant_id: Tenant ID extracted from webhook URL
            
        Returns:
            TwiML response string
        """
        try:
            logger.info(f"Handling incoming call for tenant {tenant_id}: {call_data}")
            
            # Get routing decision
            routing_decision = await self._determine_routing(call_data, tenant_id)
            
            # Generate TwiML response based on decision
            twiml_response = self._generate_twiml_response(routing_decision, call_data)
            
            return twiml_response
            
        except Exception as e:
            logger.error(f"Failed to handle incoming call for tenant {tenant_id}: {e}")
            # Return fallback TwiML
            return self._generate_fallback_response()
            
    async def handle_incoming_sms(
        self,
        sms_data: Dict[str, Any],
        tenant_id: str
    ) -> str:
        """Handle incoming SMS webhook from Twilio.
        
        Args:
            sms_data: SMS information from Twilio webhook
            tenant_id: Tenant ID extracted from webhook URL
            
        Returns:
            TwiML response string
        """
        try:
            logger.info(f"Handling incoming SMS for tenant {tenant_id}: {sms_data}")
            
            # For now, acknowledge receipt and optionally respond
            response = MessagingResponse()
            
            # Extract message content
            from_number = sms_data.get("From")
            message_body = sms_data.get("Body", "")
            
            # Simple auto-response logic (can be enhanced)
            if message_body.lower().strip() in ["stop", "unsubscribe"]:
                response.message("You have been unsubscribed from messages.")
            elif message_body.lower().strip() in ["start", "subscribe"]:
                response.message("You are now subscribed to receive messages.")
            else:
                # Forward to voice agent system for processing
                response.message("Thank you for your message. We'll get back to you soon!")
                
                # Log for processing by voice agent
                await self._log_sms_for_processing(sms_data, tenant_id)
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Failed to handle incoming SMS for tenant {tenant_id}: {e}")
            # Return simple acknowledgment
            response = MessagingResponse()
            response.message("Message received.")
            return str(response)
            
    async def _determine_routing(
        self,
        call_data: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """Determine how to route the incoming call.
        
        Args:
            call_data: Call information
            tenant_id: Tenant ID
            
        Returns:
            Routing decision with action and parameters
        """
        # Check if tenant has custom routing rule
        if tenant_id in self.routing_rules:
            try:
                return self.routing_rules[tenant_id](call_data)
            except Exception as e:
                logger.error(f"Custom routing rule failed for tenant {tenant_id}: {e}")
                
        # Default routing logic
        caller_number = call_data.get("From")
        called_number = call_data.get("To")
        call_status = call_data.get("CallStatus")
        
        # Business hours check (simplified)
        import datetime
        current_hour = datetime.datetime.now().hour
        is_business_hours = 9 <= current_hour <= 17
        
        if is_business_hours:
            return {
                "action": CallAction.VOICE_AGENT,
                "voice_agent_config": {
                    "tenant_id": tenant_id,
                    "caller_number": caller_number,
                    "called_number": called_number
                }
            }
        else:
            return {
                "action": CallAction.VOICEMAIL,
                "voicemail_config": {
                    "greeting_message": f"Thank you for calling. We're currently closed. Please leave a message.",
                    "max_length": 180  # 3 minutes
                }
            }
            
    def _generate_twiml_response(
        self,
        routing_decision: Dict[str, Any],
        call_data: Dict[str, Any]
    ) -> str:
        """Generate TwiML response based on routing decision.
        
        Args:
            routing_decision: Routing decision from _determine_routing
            call_data: Original call data
            
        Returns:
            TwiML response string
        """
        response = VoiceResponse()
        action = routing_decision["action"]
        
        if action == CallAction.VOICE_AGENT:
            # Connect to voice agent system
            config = routing_decision.get("voice_agent_config", {})
            tenant_id = config.get("tenant_id")
            
            # Say greeting and connect to voice agent
            response.say(
                "Hello! Please hold while I connect you to our voice assistant.",
                voice="alice"
            )
            
            # Use Twilio's programmable voice to connect to our voice agent endpoint
            response.dial().conference(
                f"voice-agent-{tenant_id}",
                start_conference_on_enter=True,
                end_conference_on_exit=True
            )
            
        elif action == CallAction.VOICEMAIL:
            config = routing_decision.get("voicemail_config", {})
            greeting = config.get("greeting_message", "Please leave a message after the beep.")
            max_length = config.get("max_length", 180)
            
            response.say(greeting, voice="alice")
            response.record(
                max_length=max_length,
                finish_on_key="#",
                action="/webhook/voicemail/recording"
            )
            
        elif action == CallAction.FORWARD:
            config = routing_decision.get("forward_config", {})
            forward_number = config.get("number")
            
            if forward_number:
                response.say("Please hold while I transfer your call.", voice="alice")
                response.dial(forward_number)
            else:
                response.say("I'm sorry, forwarding is not available right now.", voice="alice")
                
        elif action == CallAction.HANGUP:
            config = routing_decision.get("hangup_config", {})
            message = config.get("message", "Thank you for calling. Goodbye.")
            response.say(message, voice="alice")
            response.hangup()
            
        else:
            # Default fallback
            response.say("Thank you for calling. Please try again later.", voice="alice")
            
        return str(response)
        
    def _generate_fallback_response(self) -> str:
        """Generate fallback TwiML response for errors.
        
        Returns:
            Basic TwiML response string
        """
        response = VoiceResponse()
        response.say(
            "I'm sorry, we're experiencing technical difficulties. Please try again later.",
            voice="alice"
        )
        response.hangup()
        return str(response)
        
    async def _log_sms_for_processing(
        self,
        sms_data: Dict[str, Any],
        tenant_id: str
    ):
        """Log SMS message for processing by voice agent system.
        
        Args:
            sms_data: SMS message data
            tenant_id: Tenant ID
        """
        try:
            # This would integrate with the voice agent service
            # For now, just log the message
            logger.info(f"SMS for processing - Tenant: {tenant_id}, From: {sms_data.get('From')}, Message: {sms_data.get('Body')}")
            
            # TODO: Integrate with voice_agent_service for SMS processing
            # This would involve:
            # 1. Creating a conversation context for the SMS sender
            # 2. Processing the message through the voice agent
            # 3. Optionally sending a response back via SMS
            
        except Exception as e:
            logger.error(f"Failed to log SMS for processing: {e}")
            
    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get status of a specific call.
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            Call status information
        """
        try:
            # Use real Twilio API to fetch call details
            call = self.twilio_client.client.calls(call_sid).fetch()
            
            return {
                "call_sid": call.sid,
                "status": call.status,
                "duration": str(call.duration) if call.duration else "0",
                "caller": call.from_formatted or call.from_,
                "called": call.to_formatted or call.to,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
                "price": call.price,
                "direction": call.direction
            }
            
        except TwilioException as e:
            logger.error(f"Failed to get call status for {call_sid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting call status for {call_sid}: {e}")
            raise
        
    async def end_call(self, call_sid: str) -> bool:
        """End a specific call.
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            True if call was successfully ended
        """
        try:
            # Use real Twilio API to end the call
            self.twilio_client.client.calls(call_sid).update(status="completed")
            logger.info(f"Successfully ended call {call_sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error ending call {call_sid}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error ending call {call_sid}: {e}")
            return False