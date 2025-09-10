"""Call routing service for handling incoming phone calls."""

from datetime import datetime
from enum import Enum
from typing import Dict, Any


class CallAction(Enum):
    """Available call routing actions."""
    VOICEMAIL = "voicemail"
    CONFERENCE = "conference"
    QUEUE = "queue"
    FORWARD = "forward"
    HANGUP = "hangup"


class CallRouter:
    """Routes incoming calls based on business logic and tenant configuration."""
    
    def __init__(self):
        """Initialize the call router."""
        self.business_start_hour = 9  # 9 AM
        self.business_end_hour = 17   # 5 PM
    
    async def handle_incoming_call(self, call_data: Dict[str, Any], tenant_id: str) -> str:
        """
        Handle incoming call and return appropriate TwiML response.
        
        Args:
            call_data: Dictionary containing call information (from, to, etc.)
            tenant_id: Tenant identifier for routing configuration
            
        Returns:
            str: TwiML XML response for Twilio
        """
        current_hour = datetime.now().hour
        
        # Check if within business hours
        if self._is_business_hours(current_hour):
            return self._route_to_conference(call_data, tenant_id)
        else:
            return self._route_to_voicemail(call_data, tenant_id)
    
    def _is_business_hours(self, hour: int) -> bool:
        """Check if current time is within business hours."""
        return self.business_start_hour <= hour < self.business_end_hour
    
    def _route_to_conference(self, call_data: Dict[str, Any], tenant_id: str) -> str:
        """Route call to conference room."""
        conference_name = f"voice-agent-{tenant_id}"
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Welcome to the conference. Please wait while we connect you.</Say>
    <Dial>
        <Conference>{conference_name}</Conference>
    </Dial>
</Response>'''
        return twiml
    
    def _route_to_voicemail(self, call_data: Dict[str, Any], tenant_id: str) -> str:
        """Route call to voicemail."""
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Thank you for calling. We are currently closed. Please leave a message after the beep.</Say>
    <Record timeout="60" transcribe="true" action="/voice/voicemail/complete"/>
</Response>'''
        return twiml
    
    def _route_to_queue(self, call_data: Dict[str, Any], tenant_id: str) -> str:
        """Route call to queue."""
        queue_name = f"tenant-{tenant_id}-queue"
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Please hold while we connect you to the next available agent.</Say>
    <Enqueue>{queue_name}</Enqueue>
</Response>'''
        return twiml
    
    def get_routing_action(self, call_data: Dict[str, Any], tenant_id: str) -> CallAction:
        """
        Determine routing action based on call data and tenant configuration.
        
        Args:
            call_data: Dictionary containing call information
            tenant_id: Tenant identifier
            
        Returns:
            CallAction: The determined routing action
        """
        current_hour = datetime.now().hour
        
        if self._is_business_hours(current_hour):
            return CallAction.CONFERENCE
        else:
            return CallAction.VOICEMAIL