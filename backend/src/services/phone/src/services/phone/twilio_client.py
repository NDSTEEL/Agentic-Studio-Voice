"""Twilio API client for phone number management and call routing."""

import os
from typing import List, Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import logging

logger = logging.getLogger(__name__)


class TwilioPhoneClient:
    """Twilio client for managing phone numbers and calls."""
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        webhook_base_url: Optional[str] = None
    ):
        """Initialize Twilio client.
        
        Args:
            account_sid: Twilio Account SID (defaults to env var)
            auth_token: Twilio Auth Token (defaults to env var)  
            webhook_base_url: Base URL for webhooks (defaults to env var)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.webhook_base_url = webhook_base_url or os.getenv('WEBHOOK_BASE_URL')
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio Account SID and Auth Token are required")
        
        self.client = Client(self.account_sid, self.auth_token)
        
    async def search_phone_numbers(
        self,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        country_code: str = "US",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for available phone numbers.
        
        Args:
            area_code: Desired area code (e.g., "415")
            contains: Phone number must contain this pattern
            country_code: Country code (default: "US")
            limit: Maximum numbers to return
            
        Returns:
            List of available phone numbers with details
        """
        try:
            search_params = {
                "limit": limit
            }
            
            if area_code:
                search_params["area_code"] = area_code
            if contains:
                search_params["contains"] = contains
                
            available_numbers = self.client.available_phone_numbers(country_code).local.list(
                **search_params
            )
            
            return [
                {
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "locality": number.locality,
                    "region": number.region,
                    "postal_code": number.postal_code,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("sms", False),
                        "mms": number.capabilities.get("mms", False)
                    }
                }
                for number in available_numbers
            ]
            
        except TwilioException as e:
            logger.error(f"Failed to search phone numbers: {e}")
            raise
            
    async def provision_phone_number(
        self,
        phone_number: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None,
        friendly_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provision a phone number for use.
        
        Args:
            phone_number: Phone number to provision (e.g., "+14155551234")
            voice_url: Webhook URL for incoming calls
            sms_url: Webhook URL for incoming SMS
            friendly_name: Human-readable name for the number
            
        Returns:
            Provisioned phone number details
        """
        try:
            purchase_params = {
                "phone_number": phone_number
            }
            
            # Set webhook URLs
            if voice_url:
                purchase_params["voice_url"] = voice_url
            elif self.webhook_base_url:
                purchase_params["voice_url"] = f"{self.webhook_base_url}/webhook/voice"
                
            if sms_url:
                purchase_params["sms_url"] = sms_url
            elif self.webhook_base_url:
                purchase_params["sms_url"] = f"{self.webhook_base_url}/webhook/sms"
                
            if friendly_name:
                purchase_params["friendly_name"] = friendly_name
                
            incoming_number = self.client.incoming_phone_numbers.create(
                **purchase_params
            )
            
            return {
                "sid": incoming_number.sid,
                "phone_number": incoming_number.phone_number,
                "friendly_name": incoming_number.friendly_name,
                "voice_url": incoming_number.voice_url,
                "sms_url": incoming_number.sms_url,
                "capabilities": {
                    "voice": incoming_number.capabilities.get("voice", False),
                    "sms": incoming_number.capabilities.get("sms", False),
                    "mms": incoming_number.capabilities.get("mms", False)
                },
                "status": incoming_number.status
            }
            
        except TwilioException as e:
            logger.error(f"Failed to provision phone number {phone_number}: {e}")
            raise
            
    async def list_provisioned_numbers(self) -> List[Dict[str, Any]]:
        """List all provisioned phone numbers.
        
        Returns:
            List of provisioned phone numbers
        """
        try:
            incoming_numbers = self.client.incoming_phone_numbers.list()
            
            return [
                {
                    "sid": number.sid,
                    "phone_number": number.phone_number,
                    "friendly_name": number.friendly_name,
                    "voice_url": number.voice_url,
                    "sms_url": number.sms_url,
                    "capabilities": {
                        "voice": number.capabilities.get("voice", False),
                        "sms": number.capabilities.get("sms", False),
                        "mms": number.capabilities.get("mms", False)
                    },
                    "status": number.status
                }
                for number in incoming_numbers
            ]
            
        except TwilioException as e:
            logger.error(f"Failed to list provisioned numbers: {e}")
            raise
            
    async def release_phone_number(self, number_sid: str) -> bool:
        """Release a provisioned phone number.
        
        Args:
            number_sid: SID of the phone number to release
            
        Returns:
            True if successfully released
        """
        try:
            self.client.incoming_phone_numbers(number_sid).delete()
            logger.info(f"Released phone number with SID: {number_sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Failed to release phone number {number_sid}: {e}")
            raise
            
    async def update_phone_number_webhooks(
        self,
        number_sid: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update webhook URLs for a phone number.
        
        Args:
            number_sid: SID of the phone number to update
            voice_url: New webhook URL for incoming calls
            sms_url: New webhook URL for incoming SMS
            
        Returns:
            Updated phone number details
        """
        try:
            update_params = {}
            if voice_url:
                update_params["voice_url"] = voice_url
            if sms_url:
                update_params["sms_url"] = sms_url
                
            if not update_params:
                raise ValueError("At least one webhook URL must be provided")
                
            incoming_number = self.client.incoming_phone_numbers(number_sid).update(
                **update_params
            )
            
            return {
                "sid": incoming_number.sid,
                "phone_number": incoming_number.phone_number,
                "voice_url": incoming_number.voice_url,
                "sms_url": incoming_number.sms_url
            }
            
        except TwilioException as e:
            logger.error(f"Failed to update webhooks for {number_sid}: {e}")
            raise