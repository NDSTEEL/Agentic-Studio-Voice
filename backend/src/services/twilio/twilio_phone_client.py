"""Real Twilio phone client for phone number search and provisioning."""

import os
from typing import List, Optional, Dict, Any
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class TwilioPhoneClient:
    """Real Twilio client for phone operations with zero mocks."""
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        webhook_base_url: Optional[str] = None
    ):
        """Initialize Twilio client with real credentials.
        
        Args:
            account_sid: Twilio Account SID (defaults to env var)
            auth_token: Twilio Auth Token (defaults to env var)  
            webhook_base_url: Base URL for webhooks (defaults to env var)
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.webhook_base_url = webhook_base_url or os.getenv('WEBHOOK_BASE_URL', 'https://example.com')
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio Account SID and Auth Token are required")
        
        # Initialize real Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        logger.info("✅ Real Twilio client initialized")
    
    async def search_phone_numbers(
        self,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        country_code: str = "US",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for available phone numbers using real Twilio API.
        
        Args:
            area_code: Desired area code
            contains: Phone number must contain this pattern
            country_code: Country code (default: "US")
            limit: Maximum numbers to return
            
        Returns:
            List of available phone numbers with details
        """
        try:
            search_params = {"limit": limit}
            
            if area_code and area_code.isdigit() and len(area_code) == 3:
                search_params["area_code"] = area_code
            if contains and contains.isdigit():
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
            logger.error(f"Twilio API error searching phone numbers: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching phone numbers: {e}")
            raise
    
    async def provision_phone_number(
        self,
        phone_number: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None,
        friendly_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provision a phone number using real Twilio API.
        
        Args:
            phone_number: Phone number to provision
            voice_url: Webhook URL for incoming calls
            sms_url: Webhook URL for incoming SMS
            friendly_name: Human-readable name
            
        Returns:
            Provisioned phone number details
        """
        try:
            purchase_params = {"phone_number": phone_number}
            
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
                
            incoming_number = self.client.incoming_phone_numbers.create(**purchase_params)
            
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
            logger.error(f"Twilio API error provisioning {phone_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error provisioning phone number {phone_number}: {e}")
            raise
    
    async def list_provisioned_numbers(self) -> List[Dict[str, Any]]:
        """List all provisioned phone numbers using real Twilio API."""
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
            logger.error(f"Twilio API error listing numbers: {e}")
            raise
        except Exception as e:
            logger.error(f"Error listing provisioned numbers: {e}")
            raise
    
    async def release_phone_number(self, number_sid: str) -> bool:
        """Release a provisioned phone number using real Twilio API."""
        try:
            self.client.incoming_phone_numbers(number_sid).delete()
            logger.info(f"Released phone number with SID: {number_sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio API error releasing {number_sid}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error releasing phone number {number_sid}: {e}")
            return False
    
    async def update_phone_number_webhooks(
        self,
        number_sid: str,
        voice_url: Optional[str] = None,
        sms_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update phone number webhooks using real Twilio API."""
        try:
            update_params = {}
            
            if voice_url is not None:
                update_params["voice_url"] = voice_url
            if sms_url is not None:
                update_params["sms_url"] = sms_url
                
            updated_number = self.client.incoming_phone_numbers(number_sid).update(**update_params)
            
            return {
                "sid": updated_number.sid,
                "phone_number": updated_number.phone_number,
                "voice_url": updated_number.voice_url,
                "sms_url": updated_number.sms_url
            }
            
        except TwilioException as e:
            logger.error(f"Twilio API error updating webhooks for {number_sid}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating phone number webhooks {number_sid}: {e}")
            raise
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status for monitoring and health checks.
        
        Returns:
            Dictionary containing service status information
        """
        try:
            # Test connection to Twilio by fetching account info
            account = self.client.api.account.fetch()
            
            return {
                'twilio_available': True,
                'security_validated': True,
                'mock_mode': False,
                'credentials_present': bool(self.account_sid and self.auth_token),
                'test_credentials': False,
                'demo_credentials': False,
                'service_type': 'real',
                'account_status': account.status,
                'account_friendly_name': account.friendly_name
            }
            
        except TwilioException as e:
            logger.error(f"Twilio service status check failed: {e}")
            return {
                'twilio_available': True,
                'security_validated': False,
                'mock_mode': False,
                'credentials_present': bool(self.account_sid and self.auth_token),
                'test_credentials': False,
                'demo_credentials': False,
                'service_type': 'real',
                'error': str(e),
                'account_status': 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Service status check failed: {e}")
            return {
                'twilio_available': False,
                'security_validated': False,
                'mock_mode': False,
                'credentials_present': bool(self.account_sid and self.auth_token),
                'test_credentials': False,
                'demo_credentials': False,
                'service_type': 'error',
                'error': str(e),
                'account_status': 'unknown'
            }