"""
Twilio API client for phone calls, SMS, and voice services.
"""
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from typing import Dict, Optional, Any, List
import logging
from datetime import datetime


logger = logging.getLogger(__name__)


class TwilioClient:
    """Client for interacting with Twilio API."""
    
    def __init__(
        self, 
        account_sid: str, 
        auth_token: str,
        phone_number: Optional[str] = None
    ):
        """
        Initialize Twilio client.
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            phone_number: Default Twilio phone number for outbound calls
        """
        if not account_sid or not auth_token:
            raise ValueError("Account SID and Auth Token are required")
        
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        self.client = Client(account_sid, auth_token)
    
    def make_call(
        self, 
        to_number: str, 
        twiml_url: str,
        from_number: Optional[str] = None,
        timeout: int = 30,
        record: bool = False
    ) -> Dict[str, Any]:
        """
        Make an outbound phone call.
        
        Args:
            to_number: Phone number to call
            twiml_url: URL that returns TwiML instructions
            from_number: Twilio number to call from (defaults to configured number)
            timeout: Call timeout in seconds
            record: Whether to record the call
        
        Returns:
            Call details dictionary
        """
        if not from_number:
            if not self.phone_number:
                raise ValueError("No phone number configured for outbound calls")
            from_number = self.phone_number
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=twiml_url,
                timeout=timeout,
                record=record
            )
            
            return {
                'call_sid': call.sid,
                'to': to_number,
                'from': from_number,
                'status': call.status,
                'date_created': call.date_created.isoformat() if call.date_created else None,
                'duration': call.duration
            }
            
        except Exception as e:
            logger.error(f"Failed to make call to {to_number}: {str(e)}")
            raise
    
    def send_sms(
        self, 
        to_number: str, 
        message: str,
        from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS message.
        
        Args:
            to_number: Phone number to send SMS to
            message: Message content
            from_number: Twilio number to send from
        
        Returns:
            Message details dictionary
        """
        if not from_number:
            if not self.phone_number:
                raise ValueError("No phone number configured for SMS")
            from_number = self.phone_number
        
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            return {
                'message_sid': message_obj.sid,
                'to': to_number,
                'from': from_number,
                'status': message_obj.status,
                'date_created': message_obj.date_created.isoformat() if message_obj.date_created else None,
                'body': message
            }
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            raise
    
    def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Get details of a specific call.
        
        Args:
            call_sid: Twilio Call SID
        
        Returns:
            Call details dictionary
        """
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                'call_sid': call.sid,
                'to': call.to,
                'from': call.from_,
                'status': call.status,
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None,
                'duration': call.duration,
                'direction': call.direction,
                'answered_by': call.answered_by,
                'price': call.price,
                'price_unit': call.price_unit
            }
            
        except Exception as e:
            logger.error(f"Failed to get call details for {call_sid}: {str(e)}")
            raise
    
    def get_call_recordings(self, call_sid: str) -> List[Dict[str, Any]]:
        """
        Get recordings for a specific call.
        
        Args:
            call_sid: Twilio Call SID
        
        Returns:
            List of recording details
        """
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            
            return [
                {
                    'recording_sid': recording.sid,
                    'call_sid': recording.call_sid,
                    'duration': recording.duration,
                    'date_created': recording.date_created.isoformat() if recording.date_created else None,
                    'status': recording.status,
                    'channels': recording.channels,
                    'source': recording.source,
                    'uri': recording.uri
                }
                for recording in recordings
            ]
            
        except Exception as e:
            logger.error(f"Failed to get recordings for call {call_sid}: {str(e)}")
            raise
    
    def update_call(self, call_sid: str, status: str) -> Dict[str, Any]:
        """
        Update a call's status (e.g., to hang up).
        
        Args:
            call_sid: Twilio Call SID
            status: New status ('canceled', 'completed')
        
        Returns:
            Updated call details
        """
        try:
            call = self.client.calls(call_sid).update(status=status)
            
            return {
                'call_sid': call.sid,
                'status': call.status,
                'date_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update call {call_sid}: {str(e)}")
            raise
    
    def create_voice_response(self, message: str = None, voice: str = "alice") -> str:
        """
        Create TwiML voice response.
        
        Args:
            message: Text to speak
            voice: Twilio voice to use
        
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        
        if message:
            response.say(message, voice=voice)
        
        return str(response)
    
    def create_gather_response(
        self, 
        message: str, 
        action_url: str,
        num_digits: int = 1,
        timeout: int = 5,
        voice: str = "alice"
    ) -> str:
        """
        Create TwiML response that gathers user input.
        
        Args:
            message: Prompt message
            action_url: URL to send gathered digits
            num_digits: Number of digits to gather
            timeout: Timeout for input
            voice: Twilio voice to use
        
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        
        gather = response.gather(
            action=action_url,
            method='POST',
            num_digits=num_digits,
            timeout=timeout
        )
        gather.say(message, voice=voice)
        
        # Fallback if no input received
        response.say("We didn't receive any input. Goodbye!", voice=voice)
        response.hangup()
        
        return str(response)
    
    def create_record_response(
        self, 
        message: str,
        action_url: str,
        max_length: int = 30,
        voice: str = "alice"
    ) -> str:
        """
        Create TwiML response that records user audio.
        
        Args:
            message: Prompt message before recording
            action_url: URL to send recording data
            max_length: Maximum recording length in seconds
            voice: Twilio voice to use
        
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        
        response.say(message, voice=voice)
        response.record(
            action=action_url,
            method='POST',
            max_length=max_length,
            finish_on_key='#',
            transcribe=True,
            transcribe_callback=action_url
        )
        
        return str(response)
    
    def validate_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Validate a phone number using Twilio Lookup API.
        
        Args:
            phone_number: Phone number to validate
        
        Returns:
            Validation results
        """
        try:
            # Use Twilio Lookup API to validate phone number
            phone_info = self.client.lookups.v1.phone_numbers(phone_number).fetch()
            
            return {
                'phone_number': phone_info.phone_number,
                'country_code': phone_info.country_code,
                'national_format': phone_info.national_format,
                'carrier': getattr(phone_info, 'carrier', None),
                'caller_name': getattr(phone_info, 'caller_name', None),
                'valid': True
            }
            
        except Exception as e:
            logger.warning(f"Phone number validation failed for {phone_number}: {str(e)}")
            return {
                'phone_number': phone_number,
                'valid': False,
                'error': str(e)
            }
    
    def get_account_usage(self) -> Dict[str, Any]:
        """
        Get account usage statistics.
        
        Returns:
            Usage statistics
        """
        try:
            # Get current month's usage
            usage_records = self.client.usage.records.list(
                category='calls',
                start_date=datetime.now().replace(day=1).date(),
                end_date=datetime.now().date()
            )
            
            total_usage = {
                'calls': 0,
                'call_duration': 0,
                'sms_sent': 0,
                'total_cost': 0.0
            }
            
            for record in usage_records:
                if record.category == 'calls':
                    total_usage['calls'] += int(record.count or 0)
                    total_usage['call_duration'] += int(record.usage or 0)
                    total_usage['total_cost'] += float(record.price or 0.0)
                elif record.category == 'sms-outbound':
                    total_usage['sms_sent'] += int(record.count or 0)
                    total_usage['total_cost'] += float(record.price or 0.0)
            
            return total_usage
            
        except Exception as e:
            logger.error(f"Failed to get account usage: {str(e)}")
            raise